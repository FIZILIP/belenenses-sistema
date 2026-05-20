import os
import sys

# Deletar banco antigo se existir
db_path = 'belenenses.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Banco antigo deletado: {db_path}")

# Importar e recriar
from app import app, db
from models import User, Atleta, ComissaoTecnica, Compra, GastoMensal, ContaFixa, Inventario, Reuniao, Evento
from werkzeug.security import generate_password_hash

print("🔄 Recriando banco de dados...")

with app.app_context():
    # Criar todas as tabelas
    db.create_all()
    print("✅ Tabelas criadas")
    
    # Verificar se admin já existe
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
        print("✅ Usuário admin criado")
    else:
        print("✅ Usuário admin já existe")

print("\n" + "=" * 50)
print("🎉 BANCO DE DADOS RECRIADO COM SUCESSO!")
print("=" * 50)
print("📝 Usuário: admin")
print("🔑 Senha: belenenses123")
print("=" * 50)
