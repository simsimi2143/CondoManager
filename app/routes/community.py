from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database.db import db
from app.models.community_models import News, Incidence
from app.utils.decorators import permission_required

community_bp = Blueprint('comunidad', __name__)

# --- LISTAR NOTICIAS (Requiere Nivel 1 - Lectura) ---
@community_bp.route('/noticias')
@login_required
@permission_required('noticias', 1) 
def list_news():
    # Obtenemos todas las noticias ordenadas por fecha
    news_list = News.query.order_by(News.date_posted.desc()).all()
    
    # Pasamos una variable extra para saber si el usuario puede editar en la vista
    can_edit = current_user.has_permission('noticias', 2)
    
    return render_template('community/news_list.html', news=news_list, can_edit=can_edit)

# --- CREAR NOTICIA (Requiere Nivel 2 - Escritura) ---
@community_bp.route('/noticias/crear', methods=['GET', 'POST'])
@login_required
@permission_required('noticias', 2)
def create_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_important = True if request.form.get('is_important') else False
        
        new_post = News(title=title, content=content, is_important=is_important, author=current_user)
        db.session.add(new_post)
        db.session.commit()
        
        flash('Noticia publicada exitosamente', 'success')
        return redirect(url_for('comunidad.list_news'))
        
    return render_template('community/news_form.html', legend="Nueva Noticia")

# --- EDITAR NOTICIA (Requiere Nivel 2 - Escritura) ---
@community_bp.route('/noticias/editar/<int:news_id>', methods=['GET', 'POST'])
@login_required
@permission_required('noticias', 2)
def edit_news(news_id):
    post = News.query.get_or_404(news_id)
    
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.is_important = True if request.form.get('is_important') else False
        db.session.commit()
        flash('Noticia actualizada', 'success')
        return redirect(url_for('comunidad.list_news'))
    
    return render_template('community/news_form.html', legend="Editar Noticia", post=post)

# --- ELIMINAR NOTICIA (Requiere Nivel 2 - Escritura) ---
@community_bp.route('/noticias/eliminar/<int:news_id>')
@login_required
@permission_required('noticias', 2)
def delete_news(news_id):
    post = News.query.get_or_404(news_id)
    db.session.delete(post)
    db.session.commit()
    flash('Noticia eliminada', 'success')
    return redirect(url_for('comunidad.list_news'))

@community_bp.route('/incidencias')
@login_required
@permission_required('incidencias', 1)
def list_incidences():
    # LÓGICA DE FILTRADO:
    # Si es Admin o Conserje (Staff), ve TODO.
    # Si es Residente, solo ve LO SUYO.
    
    is_staff = current_user.role.name in ['Super Admin', 'Administrador', 'Conserje']
    
    if is_staff:
        # Staff ve todo, ordenado por las pendientes primero
        incidences = Incidence.query.order_by(Incidence.status.desc(), Incidence.created_at.desc()).all()
    else:
        # Residente ve solo sus reportes
        incidences = Incidence.query.filter_by(author_id=current_user.id).order_by(Incidence.created_at.desc()).all()
        
    can_edit = current_user.has_permission('incidencias', 2)
    
    return render_template('community/incidences_list.html', 
                           incidences=incidences, 
                           can_edit=can_edit, 
                           is_staff=is_staff)

@community_bp.route('/incidencias/nueva', methods=['POST'])
@login_required
@permission_required('incidencias', 2)
def create_incidence():
    title = request.form.get('title')
    description = request.form.get('description')
    priority = request.form.get('priority')
    
    new_inc = Incidence(
        title=title, 
        description=description, 
        priority=priority, 
        author=current_user
    )
    db.session.add(new_inc)
    db.session.commit()
    flash('Incidencia reportada correctamente.', 'success')
    return redirect(url_for('comunidad.list_incidences'))

@community_bp.route('/incidencias/gestionar/<int:inc_id>', methods=['POST'])
@login_required
@permission_required('incidencias', 2)
def manage_incidence(inc_id):
    # Solo para cambiar estado (Admin/Conserje)
    incidence = Incidence.query.get_or_404(inc_id)
    
    incidence.status = request.form.get('status')
    incidence.admin_response = request.form.get('admin_response')
    
    db.session.commit()
    flash('Estado de incidencia actualizado.', 'success')
    return redirect(url_for('comunidad.list_incidences'))