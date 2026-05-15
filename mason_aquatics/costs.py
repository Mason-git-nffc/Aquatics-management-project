"""
Mason Aquatics — Cost Controls Routes
Place this file at: routes/costs.py

Covers:
  Feed log  — /costs/feed
  Power     — /costs/power
  Dashboard — /costs/
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash
)
from models import db, FeedLog, PowerCost, Tank, TankEquipment, Species
from datetime import datetime, date, timedelta
from collections import defaultdict

costs_bp = Blueprint('costs', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _float_or_none(val):
    try:
        return float(val) if val and str(val).strip() else None
    except (ValueError, TypeError):
        return None


def _parse_date(raw):
    if not raw or not raw.strip():
        return date.today().isoformat()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return raw.strip()


def _month_label(iso_month):
    """'2026-05' → 'May 2026'"""
    try:
        return datetime.strptime(iso_month, '%Y-%m').strftime('%B %Y')
    except ValueError:
        return iso_month


def _current_month():
    return date.today().strftime('%Y-%m')


def _all_equipment():
    """Return all TankEquipment rows with their daily kWh."""
    return TankEquipment.query.all()


def _total_monthly_kwh():
    """Sum kWh across all registered equipment for a 30-day month."""
    return round(sum(e.daily_kwh for e in _all_equipment()) * 30, 2)


# ── Cost Dashboard ────────────────────────────────────────────────────────────

@costs_bp.route('/')
def dashboard():
    month = _current_month()

    # ── Feed stats ────────────────────────────────────────────────────────────
    all_feed         = FeedLog.query.order_by(FeedLog.feed_date.desc()).all()
    month_feed       = [f for f in all_feed if f.feed_date.startswith(month)]
    feed_this_month  = round(sum(f.cost_this_entry or 0 for f in month_feed), 2)
    feed_all_time    = round(sum(f.cost_this_entry or 0 for f in all_feed), 2)
    recent_feed      = all_feed[:6]

    # Feed by month (last 6 months for mini chart)
    feed_by_month = defaultdict(float)
    for f in all_feed:
        m = f.feed_date[:7] if f.feed_date and len(f.feed_date) >= 7 else 'unknown'
        feed_by_month[m] += f.cost_this_entry or 0
    feed_months = sorted(feed_by_month.keys())[-6:]
    feed_chart_labels = [_month_label(m) for m in feed_months]
    feed_chart_data   = [round(feed_by_month[m], 2) for m in feed_months]

    # ── Power stats ───────────────────────────────────────────────────────────
    all_power       = PowerCost.query.order_by(PowerCost.month_year.desc()).all()
    power_this_row  = next((p for p in all_power if p.month_year == month), None)
    power_this_month = power_this_row.total_cost_gbp if power_this_row else None

    # Equipment-based estimate for current tariff
    est_kwh      = _total_monthly_kwh()
    latest_tariff = all_power[0].tariff_per_kwh_gbp if all_power else None
    est_power_cost = round(est_kwh * latest_tariff, 2) if latest_tariff else None

    power_chart_labels = [_month_label(p.month_year) for p in reversed(all_power[-6:])]
    power_chart_data   = [p.total_cost_gbp or 0 for p in reversed(all_power[-6:])]

    # ── Combined / per-fish ───────────────────────────────────────────────────
    total_fish = sum(s.current_stock for s in Species.query.all())
    monthly_total = round(feed_this_month + (power_this_month or 0), 2)
    cost_per_fish = round(monthly_total / total_fish, 2) if total_fish > 0 else None

    # ── Equipment summary by tank ─────────────────────────────────────────────
    equip_by_tank = defaultdict(list)
    for e in _all_equipment():
        equip_by_tank[e.tank_idc].append(e)

    tank_power = []
    for tank_idc, items in sorted(equip_by_tank.items()):
        daily  = sum(e.daily_kwh for e in items)
        monthly = round(daily * 30, 2)
        cost   = round(monthly * latest_tariff, 2) if latest_tariff else None
        tank_power.append({
            'tank_idc': tank_idc,
            'items':    len(items),
            'daily_kwh': round(daily, 4),
            'monthly_kwh': monthly,
            'monthly_cost': cost,
        })

    return render_template(
        'costs/dashboard.html',
        month_label=_month_label(month),
        feed_this_month=feed_this_month,
        feed_all_time=feed_all_time,
        power_this_month=power_this_month,
        est_power_cost=est_power_cost,
        est_kwh=est_kwh,
        latest_tariff=latest_tariff,
        monthly_total=monthly_total,
        total_fish=total_fish,
        cost_per_fish=cost_per_fish,
        recent_feed=recent_feed,
        feed_chart_labels=feed_chart_labels,
        feed_chart_data=feed_chart_data,
        power_chart_labels=power_chart_labels,
        power_chart_data=power_chart_data,
        tank_power=tank_power,
    )


# ── Feed Log ──────────────────────────────────────────────────────────────────

@costs_bp.route('/feed')
def feed_list():
    f_month = request.args.get('month', '')
    f_tank  = request.args.get('tank_idc', '')

    query = FeedLog.query
    if f_month:
        query = query.filter(FeedLog.feed_date.startswith(f_month))
    if f_tank:
        if f_tank == '__global__':
            query = query.filter(FeedLog.tank_idc == None)
        else:
            query = query.filter(FeedLog.tank_idc == f_tank)

    entries = query.order_by(FeedLog.feed_date.desc()).all()

    total_cost   = round(sum(e.cost_this_entry or 0 for e in entries), 2)
    total_grams  = round(sum(e.amount_grams or 0 for e in entries), 1)

    # Months available for filter
    all_entries  = FeedLog.query.all()
    months_set   = sorted(set(
        e.feed_date[:7] for e in all_entries if e.feed_date and len(e.feed_date) >= 7
    ), reverse=True)
    month_choices = [(_month_label(m), m) for m in months_set]

    return render_template(
        'costs/feed_log.html',
        entries=entries,
        total_cost=total_cost,
        total_grams=total_grams,
        f_month=f_month,
        f_tank=f_tank,
        month_choices=month_choices,
    )


@costs_bp.route('/feed/add', methods=['POST'])
def add_feed():
    amount_g  = _float_or_none(request.form.get('amount_grams'))
    cost_kg   = _float_or_none(request.form.get('cost_per_kg_gbp'))
    entry_cost = None
    if amount_g is not None and cost_kg is not None:
        entry_cost = round((amount_g / 1000) * cost_kg, 4)

    tank_raw = request.form.get('tank_idc', '').strip()
    tank_idc = tank_raw if tank_raw else None

    entry = FeedLog(
        feed_date        = _parse_date(request.form.get('feed_date')),
        brand            = request.form.get('brand', '').strip(),
        feed_type        = request.form.get('feed_type', '').strip(),
        amount_grams     = amount_g,
        cost_per_kg_gbp  = cost_kg,
        cost_this_entry  = entry_cost,
        tank_idc         = tank_idc,
        notes            = request.form.get('notes', '').strip(),
    )
    db.session.add(entry)
    db.session.commit()
    flash('Feed entry recorded.', 'success')
    return redirect(url_for('costs.feed_list'))


@costs_bp.route('/feed/<int:entry_id>/delete', methods=['POST'])
def delete_feed(entry_id):
    entry = FeedLog.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash('Feed entry deleted.', 'success')
    return redirect(url_for('costs.feed_list'))


# ── Power Costs ───────────────────────────────────────────────────────────────

@costs_bp.route('/power')
def power_list():
    records = PowerCost.query.order_by(PowerCost.month_year.desc()).all()

    # Equipment totals for the "calculate from equipment" helper
    est_kwh = _total_monthly_kwh()

    # Per-tank breakdown
    equip_all = _all_equipment()
    tank_breakdown = defaultdict(lambda: {'items': 0, 'daily_kwh': 0.0})
    for e in equip_all:
        tank_breakdown[e.tank_idc]['items']     += 1
        tank_breakdown[e.tank_idc]['daily_kwh'] += e.daily_kwh

    tank_rows = []
    for t_idc, info in sorted(tank_breakdown.items()):
        monthly = round(info['daily_kwh'] * 30, 2)
        tank_rows.append({
            'tank_idc':   t_idc,
            'items':      info['items'],
            'daily_kwh':  round(info['daily_kwh'], 4),
            'monthly_kwh': monthly,
        })

    return render_template(
        'costs/power.html',
        records=records,
        est_kwh=est_kwh,
        tank_rows=tank_rows,
        current_month=_current_month(),
        current_month_label=_month_label(_current_month()),
    )


@costs_bp.route('/power/add', methods=['POST'])
def add_power():
    month_year = request.form.get('month_year', '').strip()
    if not month_year:
        month_year = _current_month()

    tariff     = _float_or_none(request.form.get('tariff_per_kwh_gbp'))
    total_kwh  = _float_or_none(request.form.get('total_kwh'))
    total_cost = None
    if tariff is not None and total_kwh is not None:
        total_cost = round(tariff * total_kwh, 2)

    # Check for existing record for same month — update rather than duplicate
    existing = PowerCost.query.filter_by(month_year=month_year).first()
    if existing:
        existing.tariff_per_kwh_gbp = tariff
        existing.total_kwh          = total_kwh
        existing.total_cost_gbp     = total_cost
        existing.notes              = request.form.get('notes', '').strip()
    else:
        record = PowerCost(
            month_year          = month_year,
            tariff_per_kwh_gbp  = tariff,
            total_kwh           = total_kwh,
            total_cost_gbp      = total_cost,
            notes               = request.form.get('notes', '').strip(),
        )
        db.session.add(record)

    db.session.commit()
    flash(f'Power cost for {_month_label(month_year)} saved.', 'success')
    return redirect(url_for('costs.power_list'))


@costs_bp.route('/power/<int:record_id>/delete', methods=['POST'])
def delete_power(record_id):
    record = PowerCost.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash('Power cost record deleted.', 'success')
    return redirect(url_for('costs.power_list'))
