from app import create_app
from app.database.db import db
from app.models.admin_models import Payroll

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Módulo Remuneraciones actualizado.")