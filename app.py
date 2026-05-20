from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import send_file
import os
from supabase import create_client, Client

SUPABASE_URL = "https://qkkjwiyxsiununimsipp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFra2p3aXl4c2l1bnVuaW1zaXBwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxOTA2OTYsImV4cCI6MjA5NDc2NjY5Nn0.flpfkgAal_Zbmei2tNDfJrbhvgLUJT9GHYj2Iw03mkU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'belenenses2024'
import os
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///belenenses-db-novo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/atletas'
app.config['UPLOAD_FOLDER_COMISSAO'] = 'static/uploads/comissao'
app.config['UPLOAD_FOLDER_DOCS'] = 'static/uploads/documentos'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_COMISSAO'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_DOCS'], exist_ok=True)

from models import db, User, Atleta, ComissaoTecnica, Compra, GastoMensal, ContaFixa, Inventario, Reuniao, Evento, FichaMedica, Scouting, Patrocinio, Documento

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== ROTAS PRINCIPAIS ====================
@app.route('/')
@login_required
def index():
    total_gastos_mes = GastoMensal.query.filter_by(mes=datetime.now().strftime('%Y-%m')).first()
    total_gastos = total_gastos_mes.valor if total_gastos_mes else 0
    num_atletas = Atleta.query.count()
    num_reunioes = Reuniao.query.filter(Reuniao.data >= datetime.now().date()).count()
    atletas_recentes = Atleta.query.order_by(Atleta.id.desc()).limit(5).all()
    
    # Atletas lesionados (fichas com status 'em_tratamento')
    atletas_lesionados = FichaMedica.query.filter_by(status='em_tratamento').count()
    
    return render_template('index.html', 
                         total_gastos=total_gastos,
                         num_atletas=num_atletas,
                         num_reunioes=num_reunioes,
                         atletas=atletas_recentes,
                         atletas_lesionados=atletas_lesionados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Usuário ou senha inválidos', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ==================== ROTAS PARA USUÁRIOS ====================
@app.route('/usuarios')
@login_required
def usuarios():
    if not current_user.is_admin:
        flash('Acesso restrito a administradores!', 'error')
        return redirect(url_for('index'))
    
    todos_usuarios = User.query.all()
    return render_template('usuarios.html', usuarios=todos_usuarios)

@app.route('/criar-usuario', methods=['POST'])
@login_required
def criar_usuario():
    if not current_user.is_admin:
        flash('Acesso negado!', 'error')
        return redirect(url_for('usuarios'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == '1'
    
    if User.query.filter_by(username=username).first():
        flash(f'Usuário {username} já existe!', 'warning')
        return redirect(url_for('usuarios'))
    
    if User.query.filter_by(email=email).first():
        flash(f'Email {email} já cadastrado!', 'warning')
        return redirect(url_for('usuarios'))
    
    try:
        novo = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            is_admin=is_admin
        )
        db.session.add(novo)
        db.session.commit()
        flash(f'Usuário {username} criado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
    return redirect(url_for('usuarios'))

@app.route('/deletar-usuario/<int:id>')
@login_required
def deletar_usuario(id):
    if not current_user.is_admin:
        flash('Acesso negado!', 'error')
        return redirect(url_for('usuarios'))
    
    if id == current_user.id:
        flash('Você não pode deletar seu próprio usuário!', 'warning')
        return redirect(url_for('usuarios'))
    
    usuario = User.query.get_or_404(id)
    nome = usuario.username
    db.session.delete(usuario)
    db.session.commit()
    
    flash(f'Usuário {nome} removido com sucesso!', 'success')
    return redirect(url_for('usuarios'))

# ==================== ROTAS PARA ATLETAS ====================
@app.route('/atletas', methods=['GET', 'POST'])
@login_required
def atletas():
    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('Nome do atleta é obrigatório!', 'error')
                return redirect(url_for('atletas'))
            
            foto_path = None
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename and allowed_file(foto.filename):
                    filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
                    # Upload para Supabase Storage
                    supabase.storage.from_("atletas").upload(
                        filename,
                        foto.read(),
                        {"content-type": foto.content_type}
                    )
                    foto_path = filename
            
            atleta = Atleta(
                nome=nome,
                data_nascimento=datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else datetime.now().date(),
                posicao=request.form.get('posicao') or None,
                numero=request.form.get('numero') or None,
                altura=float(request.form['altura']) if request.form.get('altura') else None,
                peso=float(request.form['peso']) if request.form.get('peso') else None,
                telefone=request.form.get('telefone') or None,
                email=request.form.get('email') or None,
                endereco=request.form.get('endereco') or None,
                categoria=request.form.get('categoria') or None,
                foto=foto_path
            )
            db.session.add(atleta)
            db.session.commit()
            flash(f'Atleta {nome} cadastrado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar atleta: {str(e)}', 'error')
        return redirect(url_for('atletas'))
    
    atletas_list = Atleta.query.all()
    return render_template('atletas.html', atletas=atletas_list)

@app.route('/atletas/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_atleta(id):
    atleta = Atleta.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            atleta.nome = request.form.get('nome', '').strip()
            atleta.posicao = request.form.get('posicao') or None
            atleta.numero = request.form.get('numero') or None
            atleta.telefone = request.form.get('telefone') or None
            atleta.email = request.form.get('email') or None
            atleta.categoria = request.form.get('categoria') or None
            atleta.endereco = request.form.get('endereco') or None
            atleta.salario = float(request.form.get('salario') or 0)
            atleta.premios = float(request.form.get('premios') or 0)
            atleta.contrato_inicio = datetime.strptime(request.form.get('contrato_inicio'), '%Y-%m-%d').date() if request.form.get('contrato_inicio') else None
            atleta.contrato_fim = datetime.strptime(request.form.get('contrato_fim'), '%Y-%m-%d').date() if request.form.get('contrato_fim') else None

            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename and allowed_file(foto.filename):
                    filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
                    # Upload para Supabase Storage
                    supabase.storage.from_("atletas").upload(
                        filename,
                        foto.read(),
                        {"content-type": foto.content_type}
                    )
                    atleta.foto = filename
            
            db.session.commit()
            flash(f'Atleta {atleta.nome} atualizado!', 'success')
            return redirect(url_for('atletas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
    
    return render_template('editar_atleta.html', atleta=atleta)

@app.route('/atletas/deletar/<int:id>')
@login_required
def deletar_atleta(id):
    atleta = Atleta.query.get_or_404(id)
    nome = atleta.nome
    
    # Remove fichas médicas vinculadas
    FichaMedica.query.filter_by(atleta_id=id).delete()
    
    if atleta.foto:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], atleta.foto))
        except:
            pass
    
    db.session.delete(atleta)
    db.session.commit()
    flash(f'Atleta {nome} removido!', 'success')
    return redirect(url_for('atletas'))

# ==================== ROTAS PARA COMISSÃO TÉCNICA ====================
@app.route('/comissao', methods=['GET', 'POST'])
@login_required
def comissao():
    if request.method == 'POST':
        try:
            foto_path = None
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename and allowed_file(foto.filename):
                    filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
                    foto.save(os.path.join(app.config['UPLOAD_FOLDER_COMISSAO'], filename))
                    foto_path = filename
            
            membro = ComissaoTecnica(
                nome=request.form['nome'],
                cargo=request.form['cargo'],
                especialidade=request.form.get('especialidade', ''),
                telefone=request.form.get('telefone', ''),
                email=request.form.get('email', ''),
                data_contratacao=datetime.strptime(request.form['data_contratacao'], '%Y-%m-%d').date() if request.form.get('data_contratacao') else datetime.now().date(),
                foto=foto_path
            )
            db.session.add(membro)
            db.session.commit()
            flash(f'Membro {membro.nome} cadastrado!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('comissao'))
    
    comissao_list = ComissaoTecnica.query.all()
    return render_template('comissao.html', comissao=comissao_list)

@app.route('/comissao/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_comissao(id):
    membro = ComissaoTecnica.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            membro.nome = request.form['nome']
            membro.cargo = request.form['cargo']
            membro.especialidade = request.form.get('especialidade', '')
            membro.telefone = request.form.get('telefone', '')
            membro.email = request.form.get('email', '')
            membro.data_contratacao = datetime.strptime(request.form['data_contratacao'], '%Y-%m-%d').date() if request.form.get('data_contratacao') else membro.data_contratacao
            
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename and allowed_file(foto.filename):
                    if membro.foto:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER_COMISSAO'], membro.foto))
                        except:
                            pass
                    filename = secure_filename(f"{datetime.now().timestamp()}_{foto.filename}")
                    foto.save(os.path.join(app.config['UPLOAD_FOLDER_COMISSAO'], filename))
                    membro.foto = filename
            
            db.session.commit()
            flash(f'{membro.nome} atualizado!', 'success')
            return redirect(url_for('comissao'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
    
    return render_template('editar_comissao.html', membro=membro)

@app.route('/comissao/deletar/<int:id>')
@login_required
def deletar_comissao(id):
    membro = ComissaoTecnica.query.get_or_404(id)
    nome = membro.nome
    db.session.delete(membro)
    db.session.commit()
    flash(f'Membro {nome} removido!', 'success')
    return redirect(url_for('comissao'))

# ==================== ROTAS PARA COMPRAS ====================
@app.route('/compras', methods=['GET', 'POST'])
@login_required
def compras():
    if request.method == 'POST':
        try:
            compra = Compra(
                item=request.form['item'],
                quantidade=int(request.form['quantidade']),
                valor_unitario=float(request.form['valor_unitario']),
                total=float(request.form['quantidade']) * float(request.form['valor_unitario']),
                data_compra=datetime.strptime(request.form['data_compra'], '%Y-%m-%d').date() if request.form.get('data_compra') else datetime.now().date(),
                fornecedor=request.form.get('fornecedor'),
                categoria=request.form.get('categoria', 'Geral')
            )
            db.session.add(compra)
            db.session.commit()
            flash('Compra registrada!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('compras'))
    
    compras_list = Compra.query.all()
    total_gastos = sum(c.total for c in compras_list if c.total)
    return render_template('compras.html', compras=compras_list, total_gastos=total_gastos)

@app.route('/compras/deletar/<int:id>')
@login_required
def deletar_compra(id):
    compra = Compra.query.get_or_404(id)
    db.session.delete(compra)
    db.session.commit()
    flash('Compra removida!', 'success')
    return redirect(url_for('compras'))

# ==================== ROTAS PARA GASTOS ====================
@app.route('/gastos', methods=['GET', 'POST'])
@login_required
def gastos():
    if request.method == 'POST':
        try:
            gasto = GastoMensal(
                mes=request.form['mes'],
                categoria=request.form['categoria'],
                valor=float(request.form['valor']),
                descricao=request.form.get('descricao', ''),
                data_pagamento=datetime.strptime(request.form['data_pagamento'], '%Y-%m-%d').date() if request.form.get('data_pagamento') else datetime.now().date()
            )
            db.session.add(gasto)
            db.session.commit()
            flash('Gasto registrado!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('gastos'))
    
    gastos_list = GastoMensal.query.all()
    return render_template('gastos.html', gastos=gastos_list)

@app.route('/gastos/deletar/<int:id>')
@login_required
def deletar_gasto(id):
    gasto = GastoMensal.query.get_or_404(id)
    db.session.delete(gasto)
    db.session.commit()
    flash('Gasto removido com sucesso!', 'success')
    return redirect(url_for('gastos'))

# ==================== ROTAS PARA CONTAS FIXAS ====================
@app.route('/contas_fixas', methods=['GET', 'POST'])
@login_required
def contas_fixas():
    if request.method == 'POST':
        try:
            conta = ContaFixa(
                descricao=request.form['descricao'],
                valor=float(request.form['valor']),
                data_vencimento=int(request.form['dia_vencimento']),
                categoria=request.form.get('categoria', 'Outros'),
                status='ativa'
            )
            db.session.add(conta)
            db.session.commit()
            flash('Conta fixa cadastrada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar conta: {str(e)}', 'error')
        return redirect(url_for('contas_fixas'))
    
    contas_list = ContaFixa.query.all()
    total_mensal = sum(conta.valor for conta in contas_list if conta.status == 'ativa')
    
    return render_template('contas_fixas.html', contas=contas_list, total_mensal=total_mensal)

@app.route('/contas_fixas/toggle/<int:id>')
@login_required
def toggle_conta_fixa(id):
    conta = ContaFixa.query.get_or_404(id)
    conta.status = 'inativa' if conta.status == 'ativa' else 'ativa'
    db.session.commit()
    flash(f'Status da conta alterado para {conta.status}!', 'success')
    return redirect(url_for('contas_fixas'))

@app.route('/contas_fixas/deletar/<int:id>')
@login_required
def deletar_conta_fixa(id):
    conta = ContaFixa.query.get_or_404(id)
    db.session.delete(conta)
    db.session.commit()
    flash('Conta removida com sucesso!', 'success')
    return redirect(url_for('contas_fixas'))




# ==================== ROTAS PARA INVENTÁRIO ====================
@app.route('/inventario', methods=['GET', 'POST'])
@login_required
def inventario():
    if request.method == 'POST':
        try:
            item = Inventario(
                nome=request.form['nome'],
                categoria=request.form.get('categoria', 'Geral'),
                quantidade=int(request.form.get('quantidade', 1)),
                localizacao=request.form.get('localizacao', ''),
                data_aquisicao=datetime.strptime(request.form['data_aquisicao'], '%Y-%m-%d').date() if request.form.get('data_aquisicao') else datetime.now().date(),
                valor_aquisicao=float(request.form.get('valor_aquisicao', 0)),
                status=request.form.get('status', 'bom')
            )
            db.session.add(item)
            db.session.commit()
            flash('Item adicionado ao inventário!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('inventario'))
    
    inventario_list = Inventario.query.all()
    return render_template('inventario.html', inventario=inventario_list)

@app.route('/inventario/deletar/<int:id>')
@login_required
def deletar_item(id):
    item = Inventario.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item removido!', 'success')
    return redirect(url_for('inventario'))

# ==================== ROTAS PARA REUNIÕES ====================
@app.route('/reunioes', methods=['GET', 'POST'])
@login_required
def reunioes():
    if request.method == 'POST':
        try:
            reuniao = Reuniao(
                titulo=request.form['titulo'],
                data=datetime.strptime(request.form['data'], '%Y-%m-%d').date(),
                hora=request.form['hora'],
                local=request.form.get('local', ''),
                pauta=request.form['pauta'],
                participantes=request.form.get('participantes', ''),
                status='agendada'
            )
            db.session.add(reuniao)
            db.session.commit()
            
            # Criar também no calendário
            evento = Evento(
                titulo=request.form['titulo'],
                data=datetime.strptime(request.form['data'], '%Y-%m-%d').date(),
                tipo='Reunião',
                descricao=request.form.get('pauta', '')
            )
            db.session.add(evento)
            db.session.commit()
            
            flash('Reunião agendada e adicionada ao calendário!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {str(e)}', 'error')
        return redirect(url_for('reunioes'))
    
    reunioes_list = Reuniao.query.all()
    return render_template('reunioes.html', reunioes=reunioes_list)

@app.route('/reunioes/concluir/<int:id>')
@login_required
def concluir_reuniao(id):
    reuniao = Reuniao.query.get_or_404(id)
    reuniao.status = 'concluída'
    
    # Atualizar o evento no calendário
    evento = Evento.query.filter_by(
        titulo=reuniao.titulo,
        data=reuniao.data,
        tipo='Reunião'
    ).first()
    if evento:
        evento.descricao = '✅ CONCLUÍDA - ' + (evento.descricao or '')
    
    db.session.commit()
    flash('Reunião concluída!', 'success')
    return redirect(url_for('reunioes'))

@app.route('/reunioes/deletar/<int:id>')
@login_required
def deletar_reuniao(id):
    reuniao = Reuniao.query.get_or_404(id)
    
    # Remover também do calendário
    evento = Evento.query.filter_by(
        titulo=reuniao.titulo,
        data=reuniao.data,
        tipo='Reunião'
    ).first()
    if evento:
        db.session.delete(evento)
    
    db.session.delete(reuniao)
    db.session.commit()
    flash('Reunião removida do calendário!', 'success')
    return redirect(url_for('reunioes'))

@app.route('/reunioes/editar/<int:id>', methods=['POST'])
@login_required
def editar_reuniao(id):
    reuniao = Reuniao.query.get_or_404(id)
    try:
        reuniao.titulo = request.form['titulo']
        reuniao.data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        reuniao.hora = request.form['hora']
        reuniao.local = request.form.get('local', '')
        reuniao.pauta = request.form['pauta']
        reuniao.participantes = request.form.get('participantes', '')
        db.session.commit()
        flash('Reunião atualizada!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('reunioes'))

# ==================== ROTAS PARA CALENDÁRIO ====================
@app.route('/calendario')
@login_required
def calendario():
    eventos = Evento.query.all()
    return render_template('calendario.html', eventos=eventos)

@app.route('/calendario/adicionar', methods=['POST'])
@login_required
def adicionar_evento():
    try:
        evento = Evento(
            titulo=request.form['titulo'],
            data=datetime.strptime(request.form['data'], '%Y-%m-%d').date(),
            tipo=request.form['tipo'],
            descricao=request.form.get('descricao', '')
        )
        db.session.add(evento)
        db.session.commit()
        flash('Evento adicionado!', 'success')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('calendario'))

# ==================== ROTAS PARA DEPARTAMENTO MÉDICO ====================
@app.route('/departamento_medico')
@login_required
def departamento_medico():
    fichas = FichaMedica.query.all()
    atletas = Atleta.query.filter_by(status='ativo').all()
    return render_template('departamento_medico.html', fichas=fichas, atletas=atletas)

@app.route('/departamento_medico/adicionar', methods=['POST'])
@login_required
def adicionar_ficha_medica():
    try:
        ficha = FichaMedica(
            atleta_id=int(request.form['atleta_id']),
            tipo_lesao=request.form.get('tipo_lesao'),
            data_lesao=datetime.strptime(request.form['data_lesao'], '%Y-%m-%d').date() if request.form.get('data_lesao') else None,
            data_retorno_previsto=datetime.strptime(request.form['data_retorno_previsto'], '%Y-%m-%d').date() if request.form.get('data_retorno_previsto') else None,
            gravidade=request.form.get('gravidade'),
            medico_responsavel=request.form.get('medico_responsavel'),
            diagnostico=request.form.get('diagnostico'),
            tratamento=request.form.get('tratamento'),
            observacoes=request.form.get('observacoes')
        )
        db.session.add(ficha)
        db.session.commit()
        flash('Ficha médica criada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('departamento_medico'))

@app.route('/departamento_medico/atualizar/<int:id>', methods=['POST'])
@login_required
def atualizar_ficha_medica(id):
    ficha = FichaMedica.query.get_or_404(id)
    try:
        ficha.status = request.form['status']
        if request.form['status'] == 'recuperado':
            ficha.data_retorno_efetivo = datetime.now().date()
        ficha.observacoes = request.form.get('observacoes', ficha.observacoes)
        db.session.commit()
        flash('Ficha médica atualizada!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('departamento_medico'))

# ==================== ROTAS PARA SCOUTING ====================
@app.route('/scouting')
@login_required
def scouting():
    jogadores = Scouting.query.all()
    return render_template('scouting.html', jogadores=jogadores)

@app.route('/scouting/adicionar', methods=['POST'])
@login_required
def adicionar_scouting():
    try:
        jogador = Scouting(
            nome_jogador=request.form['nome_jogador'],
            clube_atual=request.form.get('clube_atual'),
            posicao=request.form.get('posicao'),
            data_nascimento=datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else None,
            nacionalidade=request.form.get('nacionalidade'),
            altura=float(request.form['altura']) if request.form.get('altura') else None,
            peso=float(request.form['peso']) if request.form.get('peso') else None,
            pe_dominante=request.form.get('pe_dominante'),
            valor_estimado=float(request.form['valor_estimado']) if request.form.get('valor_estimado') else None,
            contrato_ate=datetime.strptime(request.form['contrato_ate'], '%Y-%m-%d').date() if request.form.get('contrato_ate') else None,
            nota_tecnica=int(request.form['nota_tecnica']) if request.form.get('nota_tecnica') else None,
            nota_fisica=int(request.form['nota_fisica']) if request.form.get('nota_fisica') else None,
            nota_tatica=int(request.form['nota_tatica']) if request.form.get('nota_tatica') else None,
            nota_mental=int(request.form['nota_mental']) if request.form.get('nota_mental') else None,
            partida_observada=request.form.get('partida_observada'),
            data_observacao=datetime.strptime(request.form['data_observacao'], '%Y-%m-%d').date() if request.form.get('data_observacao') else None,
            campeonato=request.form.get('campeonato'),
            observador=request.form.get('observador'),
            pontos_fortes=request.form.get('pontos_fortes'),
            pontos_fracos=request.form.get('pontos_fracos'),
            resumo=request.form.get('resumo'),
            indicacao=request.form.get('indicacao'),
            video_url=request.form.get('video_url')
        )
        db.session.add(jogador)
        db.session.commit()
        flash('Jogador adicionado ao scouting!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('scouting'))

@app.route('/scouting/atualizar/<int:id>', methods=['POST'])
@login_required
def atualizar_scouting(id):
    jogador = Scouting.query.get_or_404(id)
    try:
        jogador.status = request.form['status']
        jogador.indicacao = request.form.get('indicacao', jogador.indicacao)
        db.session.commit()
        flash('Status atualizado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('scouting'))

# ==================== CRIAR ADMIN ====================
def create_admin():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@belenenses.com',
                password=generate_password_hash('belenenses123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado!")

# ==================== INICIAR APP ====================

@app.route('/adicionar_reuniao', methods=['POST'])
@login_required
def adicionar_reuniao():
    try:
        reuniao = Reuniao(
            titulo=request.form['titulo'],
            data=datetime.strptime(request.form['data'], '%Y-%m-%d').date(),
            hora=request.form['hora'],
            local=request.form.get('local', ''),
            pauta=request.form['pauta'],
            participantes=request.form.get('participantes', ''),
            status='agendada'
        )
        db.session.add(reuniao)
        db.session.commit()
        flash('Reunião agendada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao agendar reunião: {str(e)}', 'error')
    return redirect(url_for('reunioes'))

# ==================== ROTAS PARA PATROCÍNIOS ====================
@app.route('/patrocinios')
@login_required
def patrocinios():
    patrocinios_list = Patrocinio.query.all()
    total_aportes = sum(p.valor_aporte for p in patrocinios_list if p.status == 'ativo')
    return render_template('patrocinios.html', patrocinios=patrocinios_list, total_aportes=total_aportes)

@app.route('/patrocinios/adicionar', methods=['POST'])
@login_required
def adicionar_patrocinio():
    try:
        patrocinio = Patrocinio(
            nome_patrocinador=request.form['nome_patrocinador'],
            valor_aporte=float(request.form['valor_aporte']),
            data_inicio=datetime.strptime(request.form['data_inicio'], '%Y-%m-%d').date() if request.form.get('data_inicio') else None,
            data_fim=datetime.strptime(request.form['data_fim'], '%Y-%m-%d').date() if request.form.get('data_fim') else None,
            tipo=request.form.get('tipo'),
            descricao=request.form.get('descricao'),
            contato=request.form.get('contato'),
            status=request.form.get('status', 'ativo')
        )
        db.session.add(patrocinio)
        db.session.commit()
        flash(f'Patrocínio de {patrocinio.nome_patrocinador} cadastrado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('patrocinios'))

@app.route('/patrocinios/atualizar/<int:id>', methods=['POST'])
@login_required
def atualizar_patrocinio(id):
    patrocinio = Patrocinio.query.get_or_404(id)
    try:
        patrocinio.status = request.form['status']
        db.session.commit()
        flash('Status atualizado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('patrocinios'))

@app.route('/patrocinios/deletar/<int:id>')
@login_required
def deletar_patrocinio(id):
    patrocinio = Patrocinio.query.get_or_404(id)
    nome = patrocinio.nome_patrocinador
    db.session.delete(patrocinio)
    db.session.commit()
    flash(f'Patrocínio de {nome} removido!', 'success')
    return redirect(url_for('patrocinios'))

# ==================== ROTAS PARA DOCUMENTOS ====================
@app.route('/documentos')
@login_required
def documentos():
    categoria_filtro = request.args.get('categoria', 'todos')
    if categoria_filtro == 'todos':
        docs = Documento.query.order_by(Documento.data_upload.desc()).all()
    else:
        docs = Documento.query.filter_by(categoria=categoria_filtro).order_by(Documento.data_upload.desc()).all()
    
    categorias = ['Contratos', 'Fichas de Inscrição', 'Comprovativos de Pagamento', 'Sumários', 'Facturas']
    return render_template('documentos.html', documentos=docs, categorias=categorias, categoria_ativa=categoria_filtro)

@app.route('/documentos/upload', methods=['POST'])
@login_required
def upload_documento():
    try:
        if 'arquivo' not in request.files:
            flash('Nenhum arquivo enviado!', 'error')
            return redirect(url_for('documentos'))
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            flash('Nenhum arquivo selecionado!', 'error')
            return redirect(url_for('documentos'))
        
        if arquivo:
            filename = secure_filename(f"{datetime.now().timestamp()}_{arquivo.filename}")
            arquivo.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename))
            
            doc = Documento(
                nome=request.form['nome'],
                categoria=request.form['categoria'],
                arquivo=filename,
                descricao=request.form.get('descricao', ''),
                uploaded_by=current_user.username
            )
            db.session.add(doc)
            db.session.commit()
            flash('Documento carregado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')
    return redirect(url_for('documentos'))

@app.route('/documentos/download/<int:id>')
@login_required
def download_documento(id):
    doc = Documento.query.get_or_404(id)
    caminho = os.path.join(app.config['UPLOAD_FOLDER_DOCS'], doc.arquivo)
    return send_file(caminho, as_attachment=True, download_name=doc.arquivo)

@app.route('/documentos/deletar/<int:id>')
@login_required
def deletar_documento(id):
    doc = Documento.query.get_or_404(id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], doc.arquivo))
    except:
        pass
    db.session.delete(doc)
    db.session.commit()
    flash('Documento removido!', 'success')
    return redirect(url_for('documentos'))

# Criar tabelas ao iniciar
with app.app_context():
    db.create_all()
    create_admin()

@app.route('/migrar')
def migrar():
    from sqlalchemy import text
    colunas = [
        ('salario', 'FLOAT'),
        ('premios', 'FLOAT'),
        ('contrato_inicio', 'DATE'),
        ('contrato_fim', 'DATE'),
        ('iban', 'VARCHAR(34)'),
        ('status', 'VARCHAR(20) DEFAULT \'ativo\'')
    ]
    resultado = []
    for nome, tipo in colunas:
        try:
            db.session.execute(text(f'ALTER TABLE atleta ADD COLUMN {nome} {tipo}'))
            db.session.commit()
            resultado.append(f'✅ {nome}')
        except Exception as e:
            resultado.append(f'⏭️ {nome}: {e}')
    return '<br>'.join(resultado)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(debug=False, host='0.0.0.0', port=port)