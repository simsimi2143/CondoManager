# app/models/admin_models.py
from datetime import datetime
from app.database.db import db

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    expenses = db.relationship('Expense', backref='unit', lazy=True, cascade="all, delete-orphan")

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    period = db.Column(db.String(7), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- AQUÍ EMPIEZA LO NUEVO (Fíjate en la sangría/espacio a la izquierda) ---
    
    @property
    def amount_paid(self):
        # Suma solo los pagos que tengan status 'approved'
        if not self.payments:
            return 0
        return sum(p.amount for p in self.payments if p.status == 'approved')

    @property
    def balance_due(self):
        # Calcula cuánto falta
        return self.amount - self.amount_paid

    # -------------------------------------------------------------------------

class Payment(db.Model):
    # ... (El resto de tu código de Payment sigue aquí igual que antes) ...
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    payment_date = db.Column(db.Date, default=datetime.utcnow)
    method = db.Column(db.String(50))
    reference_code = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    unit = db.relationship('Unit', backref='payments_list') # Relación con la Unidad
    
    # Esta relación es la que usa 'self.payments' arriba
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    expense = db.relationship('Expense', backref='payments')

class Fine(db.Model):
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    unit = db.relationship('Unit', backref='fines')
    
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False) # Motivo
    date_created = db.Column(db.Date, default=datetime.utcnow)
    
    # Estado: pending (Impaga), paid (Pagada)
    status = db.Column(db.String(20), default='pending')    

# apartado de presupuesto

class BudgetCategory(db.Model):
    __tablename__ = 'budget_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # Ej: "Sueldos", "Agua"
    
    entries = db.relationship('BudgetEntry', backref='category', lazy=True)

class BudgetEntry(db.Model):
    __tablename__ = 'budget_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('budget_categories.id'), nullable=False)
    
    period = db.Column(db.String(7), nullable=False) # YYYY-MM
    planned_amount = db.Column(db.Integer, default=0) # Presupuesto
    executed_amount = db.Column(db.Integer, default=0) # Gasto Real
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)