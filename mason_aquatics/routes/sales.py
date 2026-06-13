"""
Mason Aquatics — Sales & Customer Routes
Place this file at: routes/sales.py
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash
)
from models import db, Sales, Customer, Species
from datetime import datetime, date

sales_bp = Blueprint('sales', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _float_or_none(val):
    try:
        return float(val) if val and str(val).strip() else None
    except (ValueError, TypeError):
        return None


def _int_or_none(val):
    try:
        return int(val) if val and str(val).strip() else None
    except (ValueError, TypeError):
        return None


def _parse_date(raw):
    if not raw or not raw.strip():
        return date.today().isoformat()
    raw = raw.strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


# ── Sales list ────────────────────────────────────────────────────────────────

@sales_bp.route('/')
def list_sales():
    f_species  = request.args.get('species_id',  '')
    f_customer = request.args.get('customer_id', '')
    f_payment  = request.args.get('payment_type', '')
    f_from     = request.args.get('date_from',   '')
    f_to       = request.args.get('date_to',     '')

    query = Sales.query

    if f_species:
        query = query.filter(Sales.species_id == int(f_species))
    if f_customer:
        query = query.filter(Sales.customer_id == int(f_customer))
    if f_payment:
        query = query.filter(Sales.payment_type == f_payment)
    if f_from:
        query = query.filter(Sales.sale_date >= _parse_date(f_from))
    if f_to:
        query = query.filter(Sales.sale_date <= _parse_date(f_to))

    sales         = query.order_by(Sales.sale_date.desc()).all()
    total_revenue = round(sum(s.total_gbp or 0 for s in sales), 2)
    total_fish    = sum(s.quantity_sold or 0 for s in sales)
    all_species   = Species.query.order_by(Species.common_name).all()
    all_customers = Customer.query.order_by(Customer.name).all()

    return render_template(
        'sales/list.html',
        sales         = sales,
        total_revenue = total_revenue,
        total_fish    = total_fish,
        all_species   = all_species,
        all_customers = all_customers,
        f_species     = f_species,
        f_customer    = f_customer,
        f_payment     = f_payment,
        f_from        = f_from,
        f_to          = f_to,
    )


# ── Add sale ──────────────────────────────────────────────────────────────────

@sales_bp.route('/add', methods=['GET', 'POST'])
@sales_bp.route('/add/<int:species_id>', methods=['GET', 'POST'])
def add_sale(species_id=None):
    all_species   = Species.query.order_by(Species.common_name).all()
    all_customers = Customer.query.order_by(Customer.name).all()
    pre_species   = Species.query.get(species_id) if species_id else None

    if request.method == 'POST':
        sid = _int_or_none(request.form.get('species_id'))
        if not sid:
            flash('Please select a species.', 'danger')
            return render_template('sales/form.html', sale=None,
                                   all_species=all_species,
                                   all_customers=all_customers,
                                   pre_species=pre_species)

        sp    = Species.query.get(sid)
        qty   = _int_or_none(request.form.get('quantity_sold')) or 0
        price = _float_or_none(request.form.get('price_per_fish_gbp')) or 0.0

        # Stock validation
        if sp and qty > sp.current_stock:
            flash(f'Insufficient stock — only {sp.current_stock} available.', 'danger')
            return render_template('sales/form.html', sale=None,
                                   all_species=all_species,
                                   all_customers=all_customers,
                                   pre_species=pre_species)

        payment     = request.form.get('payment_type', 'Cash')
        customer_id = _int_or_none(request.form.get('customer_id'))
        total       = round(qty * price, 2)

        # Store credit deduction
        if payment == 'Store Credit' and customer_id:
            customer = Customer.query.get(customer_id)
            if customer:
                if (customer.store_credit_gbp or 0) < total:
                    flash(
                        f'Insufficient store credit — customer has '
                        f'£{customer.store_credit_gbp:.2f}, sale is £{total:.2f}.',
                        'danger'
                    )
                    return render_template('sales/form.html', sale=None,
                                           all_species=all_species,
                                           all_customers=all_customers,
                                           pre_species=pre_species)
                customer.store_credit_gbp = round(
                    (customer.store_credit_gbp or 0) - total, 2)

        sale = Sales(
            species_id         = sid,
            customer_id        = customer_id,
            sale_date          = _parse_date(request.form.get('sale_date')),
            quantity_sold      = qty,
            price_per_fish_gbp = price,
            payment_type       = payment,
            notes              = request.form.get('notes', '').strip(),
        )
        db.session.add(sale)
        db.session.commit()
        flash('Sale recorded.', 'success')
        return redirect(url_for('sales.list_sales'))

    return render_template(
        'sales/form.html',
        sale          = None,
        all_species   = all_species,
        all_customers = all_customers,
        pre_species   = pre_species,
    )


# ── Edit sale ─────────────────────────────────────────────────────────────────

@sales_bp.route('/<int:sale_id>/edit', methods=['GET', 'POST'])
def edit_sale(sale_id):
    sale          = Sales.query.get_or_404(sale_id)
    all_species   = Species.query.order_by(Species.common_name).all()
    all_customers = Customer.query.order_by(Customer.name).all()

    if request.method == 'POST':
        old_total   = sale.total_gbp or 0
        old_payment = sale.payment_type
        old_cid     = sale.customer_id

        sale.species_id         = _int_or_none(request.form.get('species_id')) or sale.species_id
        sale.customer_id        = _int_or_none(request.form.get('customer_id'))
        sale.sale_date          = _parse_date(request.form.get('sale_date'))
        sale.quantity_sold      = _int_or_none(request.form.get('quantity_sold')) or sale.quantity_sold
        sale.price_per_fish_gbp = _float_or_none(request.form.get('price_per_fish_gbp')) or sale.price_per_fish_gbp
        sale.payment_type       = request.form.get('payment_type', sale.payment_type)
        sale.notes              = request.form.get('notes', '').strip()

        # Refund old store credit
        if old_payment == 'Store Credit' and old_cid:
            old_customer = Customer.query.get(old_cid)
            if old_customer:
                old_customer.store_credit_gbp = round(
                    (old_customer.store_credit_gbp or 0) + old_total, 2)

        # Deduct new store credit
        new_total = sale.total_gbp or 0
        if sale.payment_type == 'Store Credit' and sale.customer_id:
            new_customer = Customer.query.get(sale.customer_id)
            if new_customer:
                new_customer.store_credit_gbp = round(
                    (new_customer.store_credit_gbp or 0) - new_total, 2)

        db.session.commit()
        flash('Sale updated.', 'success')
        return redirect(url_for('sales.list_sales'))

    return render_template(
        'sales/form.html',
        sale          = sale,
        all_species   = all_species,
        all_customers = all_customers,
        pre_species   = None,
    )


# ── Delete sale ───────────────────────────────────────────────────────────────

@sales_bp.route('/<int:sale_id>/delete', methods=['POST'])
def delete_sale(sale_id):
    sale = Sales.query.get_or_404(sale_id)

    # Refund store credit on delete
    if sale.payment_type == 'Store Credit' and sale.customer_id:
        customer = Customer.query.get(sale.customer_id)
        if customer:
            customer.store_credit_gbp = round(
                (customer.store_credit_gbp or 0) + (sale.total_gbp or 0), 2)

    db.session.delete(sale)
    db.session.commit()
    flash('Sale deleted.', 'success')
    return redirect(url_for('sales.list_sales'))


# ── Customer list ─────────────────────────────────────────────────────────────

@sales_bp.route('/customers')
def list_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('sales/customer_list.html', customers=customers)


# ── Customer detail ───────────────────────────────────────────────────────────

@sales_bp.route('/customers/<int:customer_id>')
def customer_detail(customer_id):
    customer    = Customer.query.get_or_404(customer_id)
    sales       = (Sales.query
                   .filter_by(customer_id=customer_id)
                   .order_by(Sales.sale_date.desc())
                   .all())
    total_spent = round(sum(s.total_gbp or 0 for s in sales), 2)
    return render_template(
        'sales/customer_detail.html',
        customer    = customer,
        sales       = sales,
        total_spent = total_spent,
    )


# ── Add customer ──────────────────────────────────────────────────────────────

@sales_bp.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Name is required.', 'danger')
            return render_template('sales/customer_form.html', customer=None)

        customer = Customer(
            name             = name,
            phone            = request.form.get('phone', '').strip() or None,
            email            = request.form.get('email', '').strip() or None,
            store_credit_gbp = _float_or_none(request.form.get('store_credit_gbp')) or 0.0,
            notes            = request.form.get('notes', '').strip() or None,
        )
        db.session.add(customer)
        db.session.commit()
        flash(f'{name} added.', 'success')
        return redirect(url_for('sales.customer_detail', customer_id=customer.id))

    return render_template('sales/customer_form.html', customer=None)


# ── Edit customer ─────────────────────────────────────────────────────────────

@sales_bp.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Name is required.', 'danger')
            return render_template('sales/customer_form.html', customer=customer)

        customer.name             = name
        customer.phone            = request.form.get('phone', '').strip() or None
        customer.email            = request.form.get('email', '').strip() or None
        customer.store_credit_gbp = (
            _float_or_none(request.form.get('store_credit_gbp'))
            if request.form.get('store_credit_gbp', '').strip()
            else customer.store_credit_gbp
        )
        customer.notes = request.form.get('notes', '').strip() or None
        db.session.commit()
        flash(f'{name} updated.', 'success')
        return redirect(url_for('sales.customer_detail', customer_id=customer.id))

    return render_template('sales/customer_form.html', customer=customer)


# ── Delete customer ───────────────────────────────────────────────────────────

@sales_bp.route('/customers/<int:customer_id>/delete', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    name     = customer.name

    # Null-out customer_id on existing sales rather than cascade-deleting them
    for sale in list(customer.sales):
        sale.customer_id = None

    db.session.delete(customer)
    db.session.commit()
    flash(f'{name} deleted. Their sales remain with no customer assigned.', 'success')
    return redirect(url_for('sales.list_customers'))


# ── Add store credit ──────────────────────────────────────────────────────────

@sales_bp.route('/customers/<int:customer_id>/add-credit', methods=['POST'])
def add_credit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    amount   = _float_or_none(request.form.get('amount'))

    if amount and amount > 0:
        customer.store_credit_gbp = round((customer.store_credit_gbp or 0) + amount, 2)
        db.session.commit()
        flash(
            f'£{amount:.2f} added. New balance: £{customer.store_credit_gbp:.2f}',
            'success'
        )
    else:
        flash('Enter a positive amount.', 'danger')

    return redirect(url_for('sales.customer_detail', customer_id=customer_id))
