# migrate_db.py
from app import app, db
from models import User
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Verificar quais colunas existem
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        # Adicionar colunas faltando
        if 'is_active' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1'))
            print("✅ Coluna is_active adicionada")
        
        if 'can_manage_comissao' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN can_manage_comissao BOOLEAN DEFAULT 0'))
            print("✅ Coluna can_manage_comissao adicionada")
        
        if 'can_manage_financeiro' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN can_manage_financeiro BOOLEAN DEFAULT 0'))
            print("✅ Coluna can_manage_financeiro adicionada")
        
        if 'can_manage_inventario' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN can_manage_inventario BOOLEAN DEFAULT 0'))
            print("✅ Coluna can_manage_inventario adicionada")
        
        if 'can_manage_reunioes' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN can_manage_reunioes BOOLEAN DEFAULT 1'))
            print("✅ Coluna can_manage_reunioes adicionada")
        
        if 'can_view_relatorios' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN can_view_relatorios BOOLEAN DEFAULT 1'))
            print("✅ Coluna can_view_relatorios adicionada")
        
        if 'last_login' not in columns:
            db.session.execute(text('ALTER TABLE user ADD COLUMN last_login DATETIME'))
            print("✅ Coluna last_login adicionada")
        
        db.session.commit()
        print("\n🎉 Migração concluída com sucesso!")

if __name__ == '__main__':
    migrate()
    