# app/__init__.py
from flask import Flask
from flask_login import LoginManager, current_user
from config import Config
from app.database.db import db 

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Inicia sesión para continuar."

    # Modelos
    from app.models.auth_models import User, Module, Permission, ModuleFunction
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Blueprints
    from app.routes.superadmin import superadmin_bp
    from app.routes.auth import auth_bp
    # ... (debajo de auth_bp)
    from app.routes.community import community_bp # <--- Importar
        # ... debajo de community_bp
    from app.routes.porteria import porteria_bp
        # ... debajo de porteria_bp
    from app.routes.administration import admin_bp
        # ... debajo de admin_bp
    from app.routes.operations import ops_bp
    
    
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(community_bp, url_prefix='/comunidad') # <--- Registrar
    app.register_blueprint(porteria_bp, url_prefix='/porteria')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ops_bp, url_prefix='/operaciones')

    # --- NUEVO: CONTEXT PROCESSOR PARA EL MENÚ ---
    @app.context_processor
    def inject_menu():
        """
        Esta función hace que la variable 'user_menu' esté disponible
        en TODAS las plantillas HTML automáticamente.
        """
        if not current_user.is_authenticated:
            return dict(user_menu=[])
        
        # Si es Super Admin (ID 1), mostramos todo
        if current_user.role.name == 'Super Admin':
            menu_modules = Module.query.all()
            # Estructuramos datos para simular permisos totales
            menu_structure = []
            for mod in menu_modules:
                functions = ModuleFunction.query.filter_by(module_id=mod.id).all()
                menu_structure.append({
                    'name': mod.name,
                    'icon': mod.icon,
                    'functions': [{'name': f.name, 'code': f.code_name} for f in functions]
                })
            return dict(user_menu=menu_structure)

        # Para otros roles, filtramos según permisos > 0
        # 1. Obtenemos permisos del rol actual donde nivel > 0
        perms = Permission.query.filter(
            Permission.role_id == current_user.role_id,
            Permission.access_level > 0
        ).all()
        
        allowed_func_ids = [p.function_id for p in perms]

        # 2. Construimos el menú solo con módulos que tengan funciones permitidas
        menu_structure = []
        all_modules = Module.query.all()
        
        for mod in all_modules:
            # Buscamos funciones de este módulo que estén permitidas
            functions = ModuleFunction.query.filter(
                ModuleFunction.module_id == mod.id,
                ModuleFunction.id.in_(allowed_func_ids)
            ).all()
            
            if functions:
                menu_structure.append({
                    'name': mod.name,
                    'icon': mod.icon,
                    'functions': [{'name': f.name, 'code': f.code_name} for f in functions]
                })

        return dict(user_menu=menu_structure)
    # ---------------------------------------------

    return app