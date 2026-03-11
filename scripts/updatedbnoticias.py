from app import create_app
from app.database.db import db
from app.models.community_models import News

app = create_app()
with app.app_context():
    db.create_all()
    print("Tabla de Noticias creada correctamente.")