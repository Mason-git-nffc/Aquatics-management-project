"""
Mason Aquatics — Breeding Records Routes
Place this file at: routes/breeding.py
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash
)
from models import db, BreedingRecord, Species
from datetime import datetime, date

breeding_bp = Blueprint('breeding', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _int_or_none(val):
    try:
        return int(val) if val and str(val).strip() else None
    except (ValueError, TypeError):
        return None


def _parse_date(raw):
    """Accept DD/MM/YYYY or ISO; return ISO string or today."""
    if not raw or not raw.strip():
        return date.today().isoformat()
    raw = raw.strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def _parse_iso_display(iso):
    """Convert ISO date string to DD/MM/YYYY for display."""
    if not iso:
        return ''
    try:
        return datetime.fromisoformat(iso).strftime('%d/%m/%Y')
    except ValueError:
        return iso


# ── Central breeding log ──────────────────────────────────────────────────────

@breeding_bp.route('/')
def list_breeding():
    """Central breeding log — all species, filterable."""
    f_species   = request.args.get('species_id', '', type=str)
    f_tank      = request.args.get('tank_idc', '')
    f_from      = request.args.get('date_from', '')
    f_to        = request.args.get('date_to', '')
    sort_by     = request.args.get('sort', 'date_desc')

    query = BreedingRecord.query

    if f_species:
        query = query.filter(BreedingRecord.species_id == int(f_species))
    if f_tank:
        query = query.filter(BreedingRecord.tank_idc == f_tank)
    if f_from:
        iso_from = _parse_date(f_from)
        query = query.filter(BreedingRecord.record_date >= iso_from)
    if f_to:
        iso_to = _parse_date(f_to)
        query = query.filter(BreedingRecord.record_date <= iso_to)

    if sort_by == 'date_asc':
        query = query.order_by(BreedingRecord.record_date.asc())
    elif sort_by == 'species':
        query = query.join(Species).order_by(Species.common_name.asc())
    elif sort_by == 'hatch':
        query = query.order_by(BreedingRecord.eggs_hatched.desc())
    else:
        query = query.order_by(BreedingRecord.record_date.desc())

    records = query.all()

    # Summary stats across filtered records
    total_events  = len(records)
    total_eggs    = sum(r.eggs_laid or 0 for r in records)
    total_hatched = sum(r.eggs_hatched or 0 for r in records)
    overall_rate  = round((total_hatched / total_eggs) * 100, 1) if total_eggs > 0 else None

    # Best hatch rate record
    best_record = None
    if records:
        rated = [r for r in records if r.hatch_rate is not None]
        if rated:
            best_record = max(rated, key=lambda r: r.hatch_rate)

    # All species for filter dropdown
    all_species = Species.query.order_by(Species.common_name).all()

    # Tank IDCs that have breeding records (for filter dropdown)
    used_tanks = sorted(set(
        r.tank_idc for r in BreedingRecord.query.all() if r.tank_idc
    ))

    return render_template(
        'breeding/list.html',
        records=records,
        all_species=all_species,
        used_tanks=used_tanks,
        f_species=f_species,
        f_tank=f_tank,
        f_from=f_from,
        f_to=f_to,
        sort_by=sort_by,
        total_events=total_events,
        total_eggs=total_eggs,
        total_hatched=total_hatched,
        overall_rate=overall_rate,
        best_record=best_record,
    )


# ── Add record (inline POST from species detail OR standalone form) ────────────

@breeding_bp.route('/add', methods=['GET', 'POST'])
@breeding_bp.route('/add/<int:species_id>', methods=['GET', 'POST'])
def add_record(species_id=None):
    """Add a new breeding record. species_id optional pre-fill."""
    all_species = Species.query.order_by(Species.common_name).all()

    if request.method == 'POST':
        sid = _int_or_none(request.form.get('species_id'))
        if not sid:
            flash('Please select a species.', 'danger')
            pre = Species.query.get(species_id) if species_id else None
            return render_template('breeding/form.html',
                                   record=None, species=pre,
                                   all_species=all_species)

        record = BreedingRecord(
            species_id  = sid,
            record_date = _parse_date(request.form.get('record_date')),
            eggs_laid   = _int_or_none(request.form.get('eggs_laid')),
            eggs_hatched= _int_or_none(request.form.get('eggs_hatched')),
            tank_idc    = request.form.get('tank_idc') or None,
            notes       = request.form.get('notes', '').strip(),
        )
        db.session.add(record)
        db.session.commit()

        # Return to inline origin if 'return_to' set
        return_to = request.form.get('return_to', '')
        if return_to == 'species':
            flash('Breeding record added.', 'success')
            return redirect(url_for('species.detail', species_id=sid))
        flash('Breeding record added.', 'success')
        return redirect(url_for('breeding.list_breeding'))

    pre_species = Species.query.get(species_id) if species_id else None
    return render_template(
        'breeding/form.html',
        record=None,
        species=pre_species,
        all_species=all_species,
    )


# ── Edit record ───────────────────────────────────────────────────────────────

@breeding_bp.route('/<int:record_id>/edit', methods=['GET', 'POST'])
def edit_record(record_id):
    record      = BreedingRecord.query.get_or_404(record_id)
    all_species = Species.query.order_by(Species.common_name).all()

    if request.method == 'POST':
        record.species_id   = _int_or_none(request.form.get('species_id')) or record.species_id
        record.record_date  = _parse_date(request.form.get('record_date'))
        record.eggs_laid    = _int_or_none(request.form.get('eggs_laid'))
        record.eggs_hatched = _int_or_none(request.form.get('eggs_hatched'))
        record.tank_idc     = request.form.get('tank_idc') or None
        record.notes        = request.form.get('notes', '').strip()
        db.session.commit()

        return_to = request.form.get('return_to', '')
        flash('Breeding record updated.', 'success')
        if return_to == 'species':
            return redirect(url_for('species.detail', species_id=record.species_id))
        return redirect(url_for('breeding.list_breeding'))

    return render_template(
        'breeding/form.html',
        record=record,
        species=record.species,
        all_species=all_species,
    )


# ── Delete record ─────────────────────────────────────────────────────────────

@breeding_bp.route('/<int:record_id>/delete', methods=['POST'])
def delete_record(record_id):
    record   = BreedingRecord.query.get_or_404(record_id)
    sid      = record.species_id
    return_to = request.form.get('return_to', '')
    db.session.delete(record)
    db.session.commit()
    flash('Breeding record deleted.', 'success')
    if return_to == 'species':
        return redirect(url_for('species.detail', species_id=sid))
    return redirect(url_for('breeding.list_breeding'))
