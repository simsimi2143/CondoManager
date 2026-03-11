from app import create_app
from app.database.db import db
from app.models.auth_models import User, Role

app = create_app()

with app.app_context():
    rol = Role.query.filter_by(name='Administrador').first()
    if rol:
        user = User(username='administrador', role_id=rol.id)
        user.set_password('administrador123')
        db.session.add(user)
        db.session.commit()
        print("Usuario 'administrador' creado.")