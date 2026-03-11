# app/models/porteria_models.py
from datetime import datetime
from app.database.db import db

class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(20), nullable=False) # Ej: "A-502"
    recipient_name = db.Column(db.String(100), nullable=False) # Nombre destinatario
    company = db.Column(db.String(50)) # Ej: Amazon, MercadoLibre, Starken
    arrival_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Estado: 'pending' (En conserjería) o 'delivered' (Entregado)
    status = db.Column(db.String(20), default='pending') 
    
    # Fecha de entrega y quién lo retiró
    delivered_date = db.Column(db.DateTime, nullable=True)
    picked_up_by = db.Column(db.String(100), nullable=True)

    # Relación con quién registró el paquete (El conserje)
    registered_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    registered_by = db.relationship('User', backref='registered_packages')