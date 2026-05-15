"""
Mason Aquatics — Tank Management Routes
Place this file at: routes/tanks.py
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from models import db, Tank, TankTest, TankEquipment, Species
from datetime import datetime, date

tanks_bp = Blueprint('tanks', __name__)

EQUIPMENT_TYPE_CHOICES = ['Heater', 'Filter', 'Light', 'Pump', 'Other']


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


# ── Routes ────────────────────────────────────────────────────────────────────

@tanks_bp.route('/')
def list_tanks():
    """Show all 30 tanks in a grid with summary data."""
    tanks = Tank.query.order_by(Tank.tank_idc).all()

    # Build a quick lookup of species per tank
    all_species = Species.query.all()
    species_by_tank = {}
    for s in all_species:
        if s.tank_idc:
            species_by_tank.setdefault(s.tank_idc, []).append(s)

    return render_template(
        'tanks/list.html',
        tanks=tanks,
        species_by_tank=species_by_tank,
    )


@tanks_bp.route('/<tank_idc>')
def detail(tank_idc):
    """Tank detail page — species, tests, chart data, equipment, primer."""
    tank = Tank.query.filter_by(tank_idc=tank_idc).first_or_404()

    species_in_tank = Species.query.filter_by(tank_idc=tank_idc).all()

    # Last 30 temperature readings for the chart (oldest → newest)
    recent_tests = (
        TankTest.query
        .filter_by(tank_idc=tank_idc)
        .order_by(TankTest.test_date.desc())
        .limit(30)
        .all()
    )
    chart_tests = list(reversed(recent_tests))  # chronological order for chart

    chart_labels  = [t.test_date_display for t in chart_tests]
    chart_temps   = [t.temperature_c for t in chart_tests]
    chart_ph      = [t.ph for t in chart_tests]

    # All tests for the history table (most recent first)
    all_tests = (
        TankTest.query
        .filter_by(tank_idc=tank_idc)
        .order_by(TankTest.test_date.desc())
        .all()
    )

    equipment = (
        TankEquipment.query
        .filter_by(tank_idc=tank_idc)
        .order_by(TankEquipment.equipment_type)
        .all()
    )

    # Primer calculation for different change %
    primer_25 = tank.primer_amount_ml  # default 25 %
    primer_50 = None
    if tank.volume_litres:
        change_litres_50 = tank.volume_litres * 0.50
        primer_50 = round((change_litres_50 / 200) * 5, 1)

    # Daily kWh total
    total_daily_kwh = sum(e.daily_kwh for e in equipment)
    monthly_kwh = round(total_daily_kwh * 30, 2)

    return render_template(
        'tanks/detail.html',
        tank=tank,
        species_in_tank=species_in_tank,
        all_tests=all_tests,
        chart_labels=chart_labels,
        chart_temps=chart_temps,
        chart_ph=chart_ph,
        equipment=equipment,
        equipment_type_choices=EQUIPMENT_TYPE_CHOICES,
        primer_25=primer_25,
        primer_50=primer_50,
        total_daily_kwh=total_daily_kwh,
        monthly_kwh=monthly_kwh,
    )


@tanks_bp.route('/<tank_idc>/edit', methods=['GET', 'POST'])
def edit_tank(tank_idc):
    """Edit tank meta — volume, location, notes."""
    tank = Tank.query.filter_by(tank_idc=tank_idc).first_or_404()

    if request.method == 'POST':
        tank.volume_litres = _float_or_none(request.form.get('volume_litres'))
        tank.location      = request.form.get('location', '').strip()
        tank.notes         = request.form.get('notes', '').strip()
        db.session.commit()
        flash(f'{tank_idc} details updated.', 'success')
        return redirect(url_for('tanks.detail', tank_idc=tank_idc))

    return render_template('tanks/edit.html', tank=tank)


# ── Water Tests ───────────────────────────────────────────────────────────────

@tanks_bp.route('/<tank_idc>/test/add', methods=['POST'])
def add_test(tank_idc):
    """Submit a new water test record."""
    Tank.query.filter_by(tank_idc=tank_idc).first_or_404()

    raw_date = request.form.get('test_date', '').strip()
    if not raw_date:
        raw_date = date.today().isoformat()
    else:
        # Accept DD/MM/YYYY or ISO
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                raw_date = datetime.strptime(raw_date, fmt).date().isoformat()
                break
            except ValueError:
                continue

    test = TankTest(
        tank_idc=tank_idc,
        test_date=raw_date,
        temperature_c=_float_or_none(request.form.get('temperature_c')),
        ph=_float_or_none(request.form.get('ph')),
        ammonia_ppm=_float_or_none(request.form.get('ammonia_ppm')),
        nitrite_ppm=_float_or_none(request.form.get('nitrite_ppm')),
        nitrate_ppm=_float_or_none(request.form.get('nitrate_ppm')),
        gh=_float_or_none(request.form.get('gh')),
        kh=_float_or_none(request.form.get('kh')),
        notes=request.form.get('notes', '').strip(),
        recorded_by=request.form.get('recorded_by', '').strip(),
    )
    db.session.add(test)
    db.session.commit()
    flash('Water test recorded.', 'success')
    return redirect(url_for('tanks.detail', tank_idc=tank_idc))


@tanks_bp.route('/test/<int:test_id>/delete', methods=['POST'])
def delete_test(test_id):
    test = TankTest.query.get_or_404(test_id)
    tank_idc = test.tank_idc
    db.session.delete(test)
    db.session.commit()
    flash('Test record deleted.', 'success')
    return redirect(url_for('tanks.detail', tank_idc=tank_idc))


# ── Equipment ─────────────────────────────────────────────────────────────────

@tanks_bp.route('/<tank_idc>/equipment/add', methods=['POST'])
def add_equipment(tank_idc):
    Tank.query.filter_by(tank_idc=tank_idc).first_or_404()

    hours = _float_or_none(request.form.get('hours_per_day'))
    if hours is None:
        hours = 24.0

    equip = TankEquipment(
        tank_idc=tank_idc,
        equipment_type=request.form.get('equipment_type', 'Other'),
        brand=request.form.get('brand', '').strip(),
        model=request.form.get('model', '').strip(),
        wattage=_float_or_none(request.form.get('wattage')),
        hours_per_day=hours,
        notes=request.form.get('notes', '').strip(),
    )
    db.session.add(equip)
    db.session.commit()
    flash('Equipment added.', 'success')
    return redirect(url_for('tanks.detail', tank_idc=tank_idc))


@tanks_bp.route('/equipment/<int:equip_id>/delete', methods=['POST'])
def delete_equipment(equip_id):
    equip = TankEquipment.query.get_or_404(equip_id)
    tank_idc = equip.tank_idc
    db.session.delete(equip)
    db.session.commit()
    flash('Equipment removed.', 'success')
    return redirect(url_for('tanks.detail', tank_idc=tank_idc))


# ── Chart API (optional JSON endpoint) ───────────────────────────────────────

@tanks_bp.route('/<tank_idc>/chart-data')
def chart_data(tank_idc):
    """Return JSON of last 30 tests for live chart refresh."""
    tests = (
        TankTest.query
        .filter_by(tank_idc=tank_idc)
        .order_by(TankTest.test_date.asc())
        .limit(30)
        .all()
    )
    return jsonify({
        'labels':       [t.test_date_display for t in tests],
        'temperatures': [t.temperature_c for t in tests],
        'ph':           [t.ph for t in tests],
    })
