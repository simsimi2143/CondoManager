from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database.db import db
from app.models.ops_models import Asset, Maintenance
from app.utils.decorators import permission_required

ops_bp = Blueprint('operaciones', __name__)

# --- CATASTRO DE ACTIVOS (Equipos) ---
@ops_bp.route('/catastro', methods=['GET', 'POST'])
@login_required
@permission_required('catastro', 1)
def list_assets():
    # Si es POST y tiene permiso nivel 2, crea el activo
    if request.method == 'POST':
        if not current_user.has_permission('catastro', 2):
            flash('No tienes permiso para crear activos.', 'error')
            return redirect(url_for('operaciones.list_assets'))
            
        name = request.form.get('name')
        location = request.form.get('location')
        brand = request.form.get('brand')
        
        asset = Asset(name=name, location=location, brand=brand)
        db.session.add(asset)
        db.session.commit()
        flash('Equipo registrado exitosamente.', 'success')
        
    assets = Asset.query.all()
    can_edit = current_user.has_permission('catastro', 2)
    return render_template('operations/assets_list.html', assets=assets, can_edit=can_edit)

# --- CALENDARIO DE MANTENCIONES ---
@ops_bp.route('/mantenciones')
@login_required
@permission_required('mantenciones', 1)
def list_maintenance():
    # Separamos pendientes de completadas
    pending = Maintenance.query.filter_by(status='pending').order_by(Maintenance.scheduled_date).all()
    history = Maintenance.query.filter_by(status='completed').order_by(Maintenance.completed_date.desc()).all()
    
    assets = Asset.query.all() # Para el select del formulario
    can_edit = current_user.has_permission('mantenciones', 2)
    
    return render_template('operations/maintenance_list.html', 
                           pending=pending, 
                           history=history, 
                           assets=assets, 
                           can_edit=can_edit,
                           today=date.today())

@ops_bp.route('/mantenciones/nueva', methods=['POST'])
@login_required
@permission_required('mantenciones', 2)
def create_maintenance():
    asset_id = request.form.get('asset_id')
    title = request.form.get('title')
    date_str = request.form.get('scheduled_date') # Viene como YYYY-MM-DD
    provider = request.form.get('provider')
    
    # Convertir string a objeto date
    sched_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    task = Maintenance(asset_id=asset_id, title=title, scheduled_date=sched_date, provider=provider)
    db.session.add(task)
    db.session.commit()
    flash('Mantención programada.', 'success')
    return redirect(url_for('operaciones.list_maintenance'))

@ops_bp.route('/mantenciones/completar/<int:task_id>')
@login_required
@permission_required('mantenciones', 2)
def complete_task(task_id):
    task = Maintenance.query.get_or_404(task_id)
    task.status = 'completed'
    task.completed_date = datetime.now()
    db.session.commit()
    flash('Mantención marcada como realizada.', 'success')
    return redirect(url_for('operaciones.list_maintenance'))