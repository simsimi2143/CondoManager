from app import create_app
from app.database.db import db
from app.models.admin_models import Unit

app = create_app()

def seed_units():
    with app.app_context():
        print("🏗️ Construyendo edificio virtual...")
        
        floors = range(1, 11) # Pisos 1 al 10
        apts_per_floor = ['01', '02', '03', '04'] # Deptos por piso
        
        count = 0
        for floor in floors:
            for apt in apts_per_floor:
                unit_num = f"{floor}{apt}" # Ej: 101, 202, 1004
                
                # Verificar si ya existe
                if not Unit.query.filter_by(number=unit_num).first():
                    # Crear unidad dummy
                    u = Unit(
                        number=unit_num, 
                        owner_name=f"Propietario Depto {unit_num}", 
                        email=f"contacto{unit_num}@edificio.com"
                    )
                    db.session.add(u)
                    count += 1
        
        db.session.commit()
        print(f"✅ Se han creado {count} departamentos nuevos exitosamente.")

if __name__ == '__main__':
    seed_units()