from app import create_app
from app.database.db import db
from app.models.porteria_models import Package

app = create_app()
with app.app_context():
    db.create_all()
    print("Tabla Paquetes creada.")