# ESTE seed.py FUNCIONA. El orden es lo unico que importa aqui.

# ✅ PRIMERO creamos la aplicacion
from app import create_app
app = create_app()

# ✅ SOLAMENTE DESPUES importamos db y los modelos
from app.database.db import db
from app.models.auth_models import Role, Module, ModuleFunction, User


def seed_data():
    with app.app_context():
        db.create_all()

        # 1. Crear Roles Básicos
        roles = ['Super Admin', 'Administrador', 'Conserje', 'Residente', 'Comité']
        for r_name in roles:
            if not Role.query.filter_by(name=r_name).first():
                db.session.add(Role(name=r_name))
        
        db.session.commit()

        # 2. Usuario Super Admin
        super_role = Role.query.filter_by(name='Super Admin').first()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role_id=super_role.id)
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Usuario 'admin' creado con clave 'admin123'")
            
        # 3. Estructura de Modulos igual que Edifito
        modules_data = {
            "Comunidad": [
                ("biblioteca", "Biblioteca"),
                ("incidencias", "Incidencias"),
                ("noticias", "Noticias"),
                ("cartas", "Cartas Condominio"),
                ("conferencias", "Conferencias"),
                ("muro", "Muro"),
                ("votaciones", "Votaciones")
            ],
            "Administración": [
                ("gastos_comunes", "Gastos Comunes"),
                ("informe_pagos", "Informes de Pago"),
                ("morosos", "Informe de Morosos"),
                ("multas", "Multas"),
                ("copropietarios", "Registro Copropietarios"),
                ("remuneraciones", "Remuneraciones"),
                ("conciliacion", "Conciliación Bancaria"),
                ("presupuesto", "Presupuesto")
            ],
            "Portería": [
                ("libro_condominio", "Libro Condominio"),
                ("camaras", "Conexión Cámaras"),
                ("visitas_qr", "Control Visitas QR"),
                ("tareas", "Tareas"),
                ("paqueteria", "Paquetería")
            ],
            "Operaciones": [
                ("catastro", "Catastro"),
                ("mantenciones", "Calendario Mantenciones")
            ]
        }

        # 4. Insertar Módulos y Funciones
        for mod_name, functions in modules_data.items():
            module = Module.query.filter_by(name=mod_name).first()
            if not module:
                module = Module(name=mod_name)
                db.session.add(module)
                db.session.commit()
            
            for code, name in functions:
                if not ModuleFunction.query.filter_by(code_name=code).first():
                    func = ModuleFunction(module_id=module.id, name=name, code_name=code)
                    db.session.add(func)

        db.session.commit()
        print("✅ Base de datos poblada correctamente")


if __name__ == '__main__':
    seed_data()