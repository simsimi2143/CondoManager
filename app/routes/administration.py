from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database.db import db
from app.models.admin_models import Unit, Expense, Payment, Fine, BudgetCategory, BudgetEntry, Payroll, BankTransaction, SystemAdjustment 
from app.utils.decorators import permission_required
from datetime import datetime

admin_bp = Blueprint('administracion', __name__)

# ==========================================
# 1. GESTIÓN DE UNIDADES (Copropietarios)
# ==========================================

@admin_bp.route('/unidades')
@login_required
@permission_required('copropietarios', 1)
def list_units():
    units = Unit.query.order_by(Unit.number).all()
    can_edit = current_user.has_permission('copropietarios', 2)
    return render_template('admin/units_list.html', units=units, can_edit=can_edit)

@admin_bp.route('/unidades/nueva', methods=['POST'])
@login_required
@permission_required('copropietarios', 2)
def create_unit():
    number = request.form.get('number')
    owner = request.form.get('owner')
    email = request.form.get('email')
    
    # Validación simple
    if Unit.query.filter_by(number=number).first():
        flash(f'La unidad {number} ya existe.', 'error')
        return redirect(url_for('administracion.list_units'))

    new_unit = Unit(number=number, owner_name=owner, email=email)
    db.session.add(new_unit)
    db.session.commit()
    flash('Unidad creada correctamente.', 'success')
    return redirect(url_for('administracion.list_units'))

# ==========================================
# 2. GASTOS COMUNES
# ==========================================

# En app/routes/administration.py

@admin_bp.route('/gastos')
@login_required
@permission_required('gastos_comunes', 1)
def list_expenses():
    expenses = Expense.query.order_by(Expense.period.desc(), Expense.status).all()
    units = Unit.query.all()
    
    can_edit = current_user.has_permission('gastos_comunes', 2)
    
    # Calculamos deuda total
    total_debt = sum(e.balance_due for e in expenses if e.status in ['pending', 'partial'])
    
    return render_template('admin/expenses_list.html', 
                           expenses=expenses, 
                           units=units, 
                           total_debt=total_debt,
                           can_edit=can_edit,
                           datetime=datetime) # <--- AGREGA ESTO AL FINAL

@admin_bp.route('/gastos/nuevo', methods=['POST'])
@login_required
@permission_required('gastos_comunes', 2)
def create_expense():
    unit_id = request.form.get('unit_id')
    period = request.form.get('period') # viene como YYYY-MM
    amount = request.form.get('amount')
    desc = request.form.get('description')
    
    expense = Expense(unit_id=unit_id, period=period, amount=amount, description=desc)
    db.session.add(expense)
    db.session.commit()
    
    flash('Gasto común asignado exitosamente.', 'success')
    return redirect(url_for('administracion.list_expenses'))

@admin_bp.route('/gastos/pagar/<int:expense_id>')
@login_required
@permission_required('gastos_comunes', 2)
def mark_paid(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    expense.status = 'paid'
    db.session.commit()
    flash('Pago registrado.', 'success')
    return redirect(url_for('administracion.list_expenses'))

# ==========================================
# 3. INFORMES DE PAGO
# ==========================================

@admin_bp.route('/pagos')
@login_required
@permission_required('informe_pagos', 1)
def list_payments():
    # Admin ve todos, Residente ve solo los de su unidad (si tuviera usuario asociado a unidad)
    # Por ahora simplificamos: Mostramos todos ordenados por fecha
    payments = Payment.query.order_by(Payment.status.desc(), Payment.payment_date.desc()).all()
    
    # Para el formulario de informar pago, necesitamos las deudas pendientes
    my_pending_expenses = Expense.query.filter_by(status='pending').all()
    
    can_edit = current_user.has_permission('informe_pagos', 2)
    
    return render_template('admin/payments_report.html', 
                           payments=payments, 
                           pending_expenses=my_pending_expenses,
                           can_edit=can_edit)

@admin_bp.route('/pagos/informar', methods=['POST'])
@login_required
@permission_required('informe_pagos', 2) # Nivel 2 porque es "escribir" un informe
def report_payment():
    expense_id = request.form.get('expense_id')
    amount = request.form.get('amount')
    method = request.form.get('method')
    reference = request.form.get('reference')
    date_str = request.form.get('payment_date')
    
    # Buscar el gasto asociado
    expense = Expense.query.get(expense_id)
    
    payment = Payment(
        amount=amount,
        method=method,
        reference_code=reference,
        payment_date=datetime.strptime(date_str, '%Y-%m-%d'),
        unit_id=expense.unit_id, # Asociamos la unidad del gasto
        expense_id=expense.id,
        status='pending' # Nace pendiente de aprobación
    )
    
    db.session.add(payment)
    db.session.commit()
    flash('Pago informado. Esperando aprobación de administración.', 'success')
    return redirect(url_for('administracion.list_payments'))

@admin_bp.route('/pagos/aprobar/<int:payment_id>')
@login_required
@permission_required('informe_pagos', 2)
def approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # 1. Aprobamos el pago actual
    payment.status = 'approved'
    db.session.commit() # Guardamos para que el cálculo incluya este pago
    
    # 2. Verificamos el saldo restante del gasto asociado
    if payment.expense:
        # Usamos las propiedades que creamos en el Paso 1
        paid_so_far = payment.expense.amount_paid
        total_debt = payment.expense.amount
        
        if paid_so_far >= total_debt:
            payment.expense.status = 'paid' # Deuda saldada
        elif paid_so_far > 0:
            payment.expense.status = 'partial' # Abono parcial
        else:
            payment.expense.status = 'pending'
            
        db.session.commit()
    
    flash(f'Pago de ${payment.amount} aprobado correctamente.', 'success')
    return redirect(url_for('administracion.list_payments'))

@admin_bp.route('/pagos/rechazar/<int:payment_id>')
@login_required
@permission_required('informe_pagos', 2)
def reject_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'rejected'
    db.session.commit()
    flash('Informe de pago rechazado.', 'error')
    return redirect(url_for('administracion.list_payments'))

# ==========================================
# 4. MULTAS E INFRACCIONES
# ==========================================

@admin_bp.route('/multas')
@login_required
@permission_required('multas', 1)
def list_fines():
    # Listamos las multas ordenadas por fecha
    fines = Fine.query.order_by(Fine.date_created.desc()).all()
    units = Unit.query.all() # Para el formulario de crear
    
    can_edit = current_user.has_permission('multas', 2)
    
    return render_template('admin/fines_list.html', 
                           fines=fines, 
                           units=units, 
                           can_edit=can_edit)

@admin_bp.route('/multas/crear', methods=['POST'])
@login_required
@permission_required('multas', 2)
def create_fine():
    unit_id = request.form.get('unit_id')
    amount = request.form.get('amount')
    reason = request.form.get('reason')
    date_str = request.form.get('date_created')
    date_fine = datetime.strptime(date_str, '%Y-%m-%d').date()

    # 1. Primero creamos el registro de la multa (para historial)
    new_fine = Fine(
        unit_id=unit_id,
        amount=amount,
        reason=reason,
        date_created=date_fine
    )
    db.session.add(new_fine)
    db.session.flush() # Obtenemos el ID sin hacer commit aun

    # 2. ✅ MAGIA: Creamos automaticamente el Gasto Comun asociado
    auto_expense = Expense(
        unit_id=unit_id,
        period = date_fine.strftime('%Y-%m'),
        description = f"✅ MULTA: {reason}",
        amount = amount,
        status = 'pending'
    )

    db.session.add(auto_expense)
    db.session.commit()

    flash(f'Multa cursada. Se ha generado automaticamente la deuda #{auto_expense.id} para el departamento.', 'success')
    return redirect(url_for('administracion.list_fines'))

@admin_bp.route('/multas/pagar/<int:fine_id>')
@login_required
@permission_required('multas', 2)
def pay_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    fine.status = 'paid'
    db.session.commit()
    flash('Multa marcada como pagada.', 'success')
    return redirect(url_for('administracion.list_fines'))


# ==========================================
# 5. INFORME DE MOROSOS (DEUDORES)
# ==========================================

@admin_bp.route('/morosos')
@login_required
@permission_required('morosos', 1)
def list_debtors():
    units = Unit.query.all()
    debtors = []
    total_community_debt = 0
    
    for u in units:
        # Filtramos gastos no pagados (pending o partial)
        unpaid_expenses = [e for e in u.expenses if e.status in ['pending', 'partial']]
        
        if unpaid_expenses:
            # Calcular deuda total de esta unidad
            total_unit_debt = sum(e.balance_due for e in unpaid_expenses)
            total_community_debt += total_unit_debt
            
            # Calcular antigüedad (Meses de mora)
            # Ordenamos por periodo para encontrar el más antiguo
            unpaid_expenses.sort(key=lambda x: x.period)
            oldest_period = unpaid_expenses[0].period # Ej: "2023-01"
            
            # Guardamos los datos procesados
            debtors.append({
                'unit': u,
                'total_debt': total_unit_debt,
                'count': len(unpaid_expenses), # Cantidad de recibos impagos
                'oldest_period': oldest_period
            })
    
    # Ordenar: Los que deben más dinero primero
    debtors.sort(key=lambda x: x['total_debt'], reverse=True)
    
    can_notify = current_user.has_permission('morosos', 2)
    
    return render_template('admin/debtors_report.html', 
                           debtors=debtors, 
                           total_debt=total_community_debt,
                           can_notify=can_notify)

@admin_bp.route('/morosos/notificar/<int:unit_id>')
@login_required
@permission_required('morosos', 2)
def notify_debtor(unit_id):
    # Simulación de envío de correo de cobranza
    unit = Unit.query.get_or_404(unit_id)
    email = unit.email or "No tiene email"
    
    flash(f'📧 Carta de cobranza enviada a {unit.owner_name} ({email}) exitosamente.', 'success')
    return redirect(url_for('administracion.list_debtors'))

@admin_bp.route('/presupuesto', methods=['GET', 'POST'])
@login_required
@permission_required('presupuesto', 1)
def view_budget():
    # 1. Determinar el periodo (Mes actual o el seleccionado)
    selected_period = request.args.get('period', datetime.now().strftime('%Y-%m'))
    
    # 2. Si es POST, estamos guardando/actualizando montos (Nivel 2)
    if request.method == 'POST':
        if not current_user.has_permission('presupuesto', 2):
            flash('No tienes permiso para editar el presupuesto.', 'error')
            return redirect(url_for('administracion.view_budget', period=selected_period))
            
        category_id = request.form.get('category_id')
        planned = request.form.get('planned') or 0
        executed = request.form.get('executed') or 0
        
        # Buscar si ya existe la entrada para ese mes y categoría
        entry = BudgetEntry.query.filter_by(period=selected_period, category_id=category_id).first()
        
        if not entry:
            entry = BudgetEntry(period=selected_period, category_id=category_id)
            db.session.add(entry)
            
        entry.planned_amount = int(planned)
        entry.executed_amount = int(executed)
        db.session.commit()
        flash('Montos actualizados correctamente.', 'success')
        return redirect(url_for('administracion.view_budget', period=selected_period))

    # 3. Preparar datos para la vista
    categories = BudgetCategory.query.all()
    budget_data = []
    
    total_planned = 0
    total_executed = 0
    
    for cat in categories:
        entry = BudgetEntry.query.filter_by(category_id=cat.id, period=selected_period).first()
        planned = entry.planned_amount if entry else 0
        executed = entry.executed_amount if entry else 0
        
        total_planned += planned
        total_executed += executed
        
        # Calcular porcentaje de uso
        percent = (executed / planned * 100) if planned > 0 else 0
        
        budget_data.append({
            'category': cat,
            'planned': planned,
            'executed': executed,
            'difference': planned - executed,
            'percent': min(percent, 100), # Tope visual 100%
            'is_over': executed > planned
        })
        
    can_edit = current_user.has_permission('presupuesto', 2)
    
    return render_template('admin/budget_view.html', 
                           budget_data=budget_data,
                           period=selected_period,
                           categories=categories,
                           totals={'planned': total_planned, 'executed': total_executed},
                           can_edit=can_edit)

@admin_bp.route('/presupuesto/categoria/nueva', methods=['POST'])
@login_required
@permission_required('presupuesto', 2)
def create_budget_category():
    name = request.form.get('name')
    if name:
        if not BudgetCategory.query.filter_by(name=name).first():
            db.session.add(BudgetCategory(name=name))
            db.session.commit()
            flash('Categoría creada.', 'success')
    return redirect(request.referrer)

# ==========================================
# 7. REMUNERACIONES Y SUELDOS
# ==========================================

@admin_bp.route('/remuneraciones')
@login_required
@permission_required('remuneraciones', 1)
def list_payrolls():
    period = request.args.get('period', datetime.now().strftime('%Y-%m'))
    
    payrolls = Payroll.query.filter_by(period=period).all()
    
    total_liquid = sum(p.liquid_salary for p in payrolls)
    
    can_edit = current_user.has_permission('remuneraciones', 2)
    
    return render_template('admin/payroll_list.html', 
                           payrolls=payrolls, 
                           period=period,
                           total_liquid=total_liquid,
                           can_edit=can_edit)

@admin_bp.route('/remuneraciones/nuevo', methods=['POST'])
@login_required
@permission_required('remuneraciones', 2)
def create_payroll():
    name = request.form.get('name')
    rut = request.form.get('rut')
    position = request.form.get('position')
    base = int(request.form.get('base'))
    bonus = int(request.form.get('bonus') or 0)
    deduction = int(request.form.get('deduction') or 0)
    bank = request.form.get('bank')
    account = request.form.get('account')
    period = request.form.get('period')
    
    # Crear registro
    payroll = Payroll(
        employee_name=name, rut=rut, position=position,
        period=period, base_salary=base, bonuses=bonus, deductions=deduction,
        bank_name=bank, bank_account=account
    )
    db.session.add(payroll)
    db.session.commit()
    
    flash('Liquidación registrada exitosamente.', 'success')
    return redirect(url_for('administracion.list_payrolls', period=period))

@admin_bp.route('/remuneraciones/pagar/<int:payroll_id>')
@login_required
@permission_required('remuneraciones', 2)
def mark_paid_payroll(payroll_id):
    payroll = Payroll.query.get_or_404(payroll_id)
    payroll.payment_status = 'paid'
    db.session.commit()
    flash(f'Sueldo de {payroll.employee_name} marcado como PAGADO.', 'success')
    return redirect(request.referrer)

# ==========================================
# 8. CONCILIACIÓN BANCARIA
# ==========================================

@admin_bp.route('/conciliacion')
@login_required
@permission_required('conciliacion', 1)
def bank_reconciliation():
    # 1. Movimientos del SISTEMA
    # A) Ingresos por Pagos GC
    incomes = Payment.query.filter_by(status='approved').all()
    # B) Egresos por Sueldos
    outflows = Payroll.query.filter_by(payment_status='paid').all()
    # C) Ajustes / Saldos Iniciales (NUEVO)
    adjustments = SystemAdjustment.query.all()
    
    system_movements = []
    
    # ... (El bucle de incomes y outflows que ya tenías sigue igual) ...
    for inc in incomes:
        system_movements.append({'date': inc.payment_date, 'desc': f"Pago GC Depto {inc.unit.number}", 'amount': inc.amount, 'type': 'income'})
    for out in outflows:
        date_obj = datetime.strptime(out.period + '-28', '%Y-%m-%d').date()
        system_movements.append({'date': date_obj, 'desc': f"Sueldo {out.employee_name}", 'amount': -out.liquid_salary, 'type': 'outflow'})

    # --- AGREGAMOS LOS AJUSTES A LA LISTA ---
    for adj in adjustments:
        system_movements.append({
            'date': adj.date,
            'desc': f"⚙️ {adj.description}",
            'amount': adj.amount,
            'type': 'adjustment'
        })
    # ----------------------------------------
        
    system_movements.sort(key=lambda x: x['date'], reverse=True)
    
    # 2. Movimientos del BANCO (Igual que antes)
    bank_movements = BankTransaction.query.order_by(BankTransaction.date.desc()).all()
    
    # 3. Calcular Saldos (Ahora incluye ajustes)
    saldo_sistema = sum(m['amount'] for m in system_movements)
    saldo_banco = sum(b.amount for b in bank_movements)
    
    can_edit = current_user.has_permission('conciliacion', 2)
    
    return render_template('admin/reconciliation.html', 
                           system_movements=system_movements,
                           bank_movements=bank_movements,
                           saldo_sistema=saldo_sistema,
                           saldo_banco=saldo_banco,
                           can_edit=can_edit)

@admin_bp.route('/conciliacion/agregar', methods=['POST'])
@login_required
@permission_required('conciliacion', 2)
def add_bank_transaction():
    date_str = request.form.get('date')
    desc = request.form.get('description')
    amount = int(request.form.get('amount'))
    type_trans = request.form.get('type') # 'deposit' o 'withdrawal'
    
    final_amount = amount if type_trans == 'deposit' else -amount
    
    trans = BankTransaction(
        date=datetime.strptime(date_str, '%Y-%m-%d'),
        description=desc,
        amount=final_amount
    )
    db.session.add(trans)
    db.session.commit()
    flash('Movimiento bancario registrado.', 'success')
    return redirect(url_for('administracion.bank_reconciliation'))

@admin_bp.route('/conciliacion/toggle/<int:trans_id>')
@login_required
@permission_required('conciliacion', 2)
def toggle_reconcile(trans_id):
    trans = BankTransaction.query.get_or_404(trans_id)
    trans.is_reconciled = not trans.is_reconciled
    db.session.commit()
    return redirect(url_for('administracion.bank_reconciliation'))

# --- ESTA ES LA RUTA QUE TE FALTA ---
@admin_bp.route('/conciliacion/ajuste', methods=['POST'])
@login_required
@permission_required('conciliacion', 2)
def add_system_adjustment():
    amount = int(request.form.get('amount'))
    desc = request.form.get('description')
    date_str = request.form.get('date')
    
    adj = SystemAdjustment(
        amount=amount,
        description=desc,
        date=datetime.strptime(date_str, '%Y-%m-%d')
    )
    db.session.add(adj)
    db.session.commit()
    flash('Ajuste de sistema registrado.', 'success')
    return redirect(url_for('administracion.bank_reconciliation'))