# app/models/auth_models.py
from app.database.db import db
from flask_login import UserMixin # <--- Importante
from werkzeug.security import generate_password_hash, check_password_hash

# 1. El Rol (Ej: Super Admin, Administrador, Conserje, Residente)
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    
    # Relación con usuarios y permisos
    users = db.relationship('User', backref='role', lazy=True)
    permissions = db.relationship('Permission', backref='role', lazy=True)

# 2. El Módulo General (Ej: Comunidad, Administración, Portería)
class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # Ej: "Comunidad"
    icon = db.Column(db.String(50)) # Para el icono del menú
    
    functions = db.relationship('ModuleFunction', backref='module', lazy=True)

# 3. La Función Específica (Ej: Dentro de Comunidad -> "Noticias", "Votaciones")
class ModuleFunction(db.Model):
    __tablename__ = 'module_functions'
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False) # Nombre legible Ej: "Libro de Visitas"
    code_name = db.Column(db.String(50), unique=True, nullable=False) # Código interno Ej: "visit_book"

# 4. La Tabla de Permisos (La Matriz)
# Conecta un ROL con una FUNCIÓN ESPECÍFICA y le asigna un NIVEL
class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    function_id = db.Column(db.Integer, db.ForeignKey('module_functions.id'), nullable=False)
    
    # Nivel de acceso: 0=Sin Acceso, 1=Lectura, 2=Escritura/Edición
    access_level = db.Column(db.Integer, default=0, nullable=False)

# 5. Usuario Actualizado
class User(UserMixin, db.Model): # <--- Hereda de UserMixin
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) # Cambiamos password por password_hash
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Método auxiliar para verificar permiso rápidamente
    def has_permission(self, function_code, required_level):
        # Si es Super Admin (ID 1 o nombre), acceso total (opcional, pero recomendado)
        if self.role.name == 'Super Admin':
            return True

        # Buscar la función por su código (ej: 'gastos_comunes')
        function = ModuleFunction.query.filter_by(code_name=function_code).first()
        if not function:
            return False
            
        # Buscar el permiso en la tabla intermedia
        perm = Permission.query.filter_by(role_id=self.role_id, function_id=function.id).first()
        
        if not perm:
            return False # Si no existe registro, es nivel 0
            
        return perm.access_level >= required_level