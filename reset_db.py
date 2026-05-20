# reset_db.py
import os
import sqlite3

# Deletar banco antigo
db_path = 'belenenses.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Banco {db_path} deletado")

# Recriar banco
from app import app, db
from models import User, Atleta, ComissaoTecnica, Compra, GastoMensal, ContaFixa, Inventario, Reuniao, Evento

with app.app_context():
    db.create_all()
    print("✅ Todas as tabelas criadas")
    
    # Criar admin
    from werkzeug.security import generate_password_hash
    admin = User(
        username='admin',
        email='admin@belenenses.com',
        password=generate_password_hash('belenenses123'),
        is_admin=True,
        is_active=True
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Usuário admin criado")
    
print("🎉 Banco de dados recriado com sucesso!")