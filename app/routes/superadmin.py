from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.database.db import db
from app.models.auth_models import Role, Module, Permission, ModuleFunction

superadmin_bp = Blueprint('superadmin', __name__)

@superadmin_bp.route('/roles')
def list_roles():
    roles = Role.query.all()
    return render_template('superadmin/roles_list.html', roles=roles)

@superadmin_bp.route('/permissions/<int:role_id>', methods=['GET', 'POST'])
def manage_permissions(role_id):
    role = Role.query.get_or_404(role_id)
    modules = Module.query.all() # Traemos todos los módulos y sus funciones
    
    if request.method == 'POST':
        # Procesar el formulario de la matriz
        for key, value in request.form.items():
            if key.startswith('perm_'):
                # El name del input es perm_{function_id} y el value es el nivel (0,1,2)
                function_id = int(key.split('_')[1])
                level = int(value)
                
                # Buscar si ya existe el permiso
                perm = Permission.query.filter_by(role_id=role.id, function_id=function_id).first()
                
                if perm:
                    perm.access_level = level
                else:
                    new_perm = Permission(role_id=role.id, function_id=function_id, access_level=level)
                    db.session.add(new_perm)
        
        db.session.commit()
        flash('Permisos actualizados correctamente', 'success')
        return redirect(url_for('superadmin.manage_permissions', role_id=role.id))

    # Para GET: Necesitamos saber los permisos actuales para marcar los checkboxes/radios
    current_perms = {p.function_id: p.access_level for p in role.permissions}
    
    return render_template('superadmin/edit_perm.html', role=role, modules=modules, current_perms=current_perms)