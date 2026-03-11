from app import create_app
from app.database.db import db
# IMPORTANTE: Importamos el modelo Payment para que SQLAlchemy sepa que existe
from app.models.admin_models import Payment 

app = create_app()

def update():
    with app.app_context():
        db.create_all()
        print("✅ ¡Tabla 'payments' creada exitosamente!")

if __name__ == '__main__':
    update()