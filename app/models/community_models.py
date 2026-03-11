# app/models/community_models.py
from datetime import datetime
from app.database.db import db

class News(db.Model):
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_important = db.Column(db.Boolean, default=False)
    
    # Relación con el autor (Usuario)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref='news_posts', lazy=True)

    def __repr__(self):
        return f"News('{self.title}', '{self.date_posted}')"

# ... (al final de app/models/community_models.py)

class Incidence(db.Model):
    __tablename__ = 'incidences'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Prioridad: Baja, Media, Alta
    priority = db.Column(db.String(20), default='Media')
    
    # Estado: Pendiente, En Revisión, Resuelta, Rechazada
    status = db.Column(db.String(20), default='Pendiente')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Quién reportó
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref='incidences', lazy=True)
    
    # Respuesta de la administración
    admin_response = db.Column(db.Text)