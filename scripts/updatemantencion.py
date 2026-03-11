from app import create_app
from app.database.db import db
from app.models.ops_models import Asset, Maintenance

app = create_app()
with app.app_context():
    db.create_all()
    print("Tablas de Operaciones creadas.")