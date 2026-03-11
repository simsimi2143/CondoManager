from datetime import datetime
from app.database.db import db

class Asset(db.Model):
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Ej: Ascensor Torre A
    location = db.Column(db.String(100)) # Ej: Piso -1
    brand = db.Column(db.String(50)) # Marca
    serial_number = db.Column(db.String(50))
    
    # Relación con sus mantenciones
    maintenances = db.relationship('Maintenance', backref='asset', lazy=True, cascade="all, delete-orphan")

class Maintenance(db.Model):
    __tablename__ = 'maintenances'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    
    title = db.Column(db.String(100), nullable=False) # Ej: Cambio de Aceite
    scheduled_date = db.Column(db.Date, nullable=False) # Cuándo toca
    provider = db.Column(db.String(100)) # Empresa externa (Otis, Schindler, etc)
    
    # Estado: pending (Pendiente), completed (Realizada)
    status = db.Column(db.String(20), default='pending') 
    
    completed_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text) # Observaciones del técnico