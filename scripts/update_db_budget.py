from app import create_app
from app.database.db import db
from app.models.admin_models import BudgetCategory, BudgetEntry

app = create_app()
with app.app_context():
    db.create_all()
    
    # Opcional: Crear categorías base si no existen
    cats = ['Agua Potable', 'Electricidad', 'Gas', 'Sueldos Personal', 'Mantención Ascensores', 'Jardinería', 'Insumos Aseo']
    for c in cats:
        if not BudgetCategory.query.filter_by(name=c).first():
            db.session.add(BudgetCategory(name=c))
    db.session.commit()
    
    print("✅ Módulo Presupuesto actualizado.")