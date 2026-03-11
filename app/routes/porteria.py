# app/routes/porteria.py
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database.db import db
from app.models.porteria_models import Package
from app.utils.decorators import permission_required

porteria_bp = Blueprint('porteria', __name__)

# --- LISTAR PAQUETES (Nivel 1) ---
@porteria_bp.route('/paqueteria')
@login_required
@permission_required('paqueteria', 1)
def list_packages():
    # Filtro opcional: ?filter=pending o ?filter=history
    filter_status = request.args.get('filter', 'pending')
    
    if filter_status == 'pending':
        packages = Package.query.filter_by(status='pending').order_by(Package.arrival_date.desc()).all()
    else:
        packages = Package.query.filter_by(status='delivered').order_by(Package.delivered_date.desc()).all()
        
    can_edit = current_user.has_permission('paqueteria', 2)
    
    return render_template('porteria/packages_list.html', packages=packages, filter=filter_status, can_edit=can_edit)

# --- REGISTRAR NUEVO PAQUETE (Nivel 2) ---
@porteria_bp.route('/paqueteria/nuevo', methods=['GET', 'POST'])
@login_required
@permission_required('paqueteria', 2)
def new_package():
    if request.method == 'POST':
        unit = request.form.get('unit')
        recipient = request.form.get('recipient')
        company = request.form.get('company')
        
        pkg = Package(
            unit_number=unit,
            recipient_name=recipient,
            company=company,
            registered_by=current_user
        )
        db.session.add(pkg)
        db.session.commit()
        flash('Paquete registrado correctamente', 'success')
        return redirect(url_for('porteria.list_packages'))
    
    return render_template('porteria/package_form.html')

# --- MARCAR COMO ENTREGADO (Nivel 2) ---
@porteria_bp.route('/paqueteria/entregar/<int:pkg_id>', methods=['POST'])
@login_required
@permission_required('paqueteria', 2)
def deliver_package(pkg_id):
    pkg = Package.query.get_or_404(pkg_id)
    picked_up_by = request.form.get('picked_up_by')
    
    pkg.status = 'delivered'
    pkg.delivered_date = datetime.utcnow()
    pkg.picked_up_by = picked_up_by
    
    db.session.commit()
    flash('Paquete marcado como entregado.', 'success')
    return redirect(url_for('porteria.list_packages'))