from app import create_app
from app.database.db import db
from app.models.auth_models import User, Role

app = create_app()

with app.app_context():
    rol = Role.query.filter_by(name='Conserje').first()
    if rol:
        user = User(username='conserje', role_id=rol.id)
        user.set_password('conserje123')
        db.session.add(user)
        db.session.commit()
        print("Usuario 'conserje' creado.")