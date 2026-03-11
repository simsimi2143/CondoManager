# app/utils/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user

def permission_required(function_code, level):
    """
    function_code: El código único de la función (ej: 'gastos_comunes')
    level: 1 (Lectura) o 2 (Escritura)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(401) # No autorizado (Login requerido)
                
            # Usamos el método que creamos en el modelo User
            if not current_user.has_permission(function_code, level):
                # Si no tiene permiso, lanzamos Error 403 (Prohibido)
                return abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator