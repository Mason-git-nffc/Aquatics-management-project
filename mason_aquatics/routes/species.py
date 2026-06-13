"""
Mason Aquatics — Species CRUD Routes
Place this file at: routes/species.py
"""

import os
import uuid
from datetime import datetime, date
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app
)
from models import db, Species, Photo, WharfPrice, Tank

# ── Static choice lists ───────────────────────────────────────────────────────

REPRODUCTION_CHOICES = [
    'Egg Layer', 'Livebearer', 'Mouthbrooder',
    'Bubble Nest Builder', 'Cave Spawner', 'Other',
]

PURCHASED_FROM_CHOICES = [
    'Wharf Aquatics', 'Aquatic Warehouse', 'Local Breeder',
    'Online Seller', 'Aquatic Society', 'Other',
]


def _choice_lists():
    """Return dicts of dropdown choices for form templates."""
    tanks = [t.tank_idc for t in Tank.query.order_by(Tank.tank_idc).all()]
    repros = sorted({
        s.reproduction_type
        for s in Species.query.with_entities(Species.reproduction_type).all()
        if s.reproduction_type
    }) or REPRODUCTION_CHOICES
    return dict(
        tank_choices         = tanks,
        reproduction_choices = repros,
        purchased_from_choices = PURCHASED_FROM_CHOICES,
    )

species_bp = Blueprint('species', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        return None
    raw = raw.strip()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def _apply_form(species, form):
    """Write form fields onto a Species instance."""
    species.common_name          = form.get('common_name', '').strip()
    species.scientific_name      = form.get('scientific_name', '').strip() or None
    species.native_to            = form.get('native_to', '').strip() or None
    species.weather_link         = form.get('weather_link', '').strip() or None
    species.tank_idc             = form.get('tank_idc', '').strip() or None
    species.min_temp_c           = _float_or_none(form.get('min_temp_c'))
    species.max_temp_c           = _float_or_none(form.get('max_temp_c'))
    species.ideal_ph             = _float_or_none(form.get('ideal_ph'))
    species.reproduction_type    = form.get('reproduction_type', '').strip() or None
    species.purchased_from       = form.get('purchased_from', '').strip() or None
    species.purchased_from_notes = form.get('purchased_from_notes', '').strip() or None
    species.date_purchased       = _parse_date(form.get('date_purchased'))
    species.price_per_fish_gbp   = _float_or_none(form.get('price_per_fish_gbp'))
    species.quantity_bought      = _int_or_none(form.get('quantity_bought'))


def _save_wharf_prices(species, form):
    """Replace all wharf price rows from repeated wp_quantity / wp_price fields."""
    for wp in list(species.wharf_prices):
        db.session.delete(wp)

    quantities = form.getlist('wp_quantity')
    prices     = form.getlist('wp_price')
    notes_list = form.getlist('wp_notes')

    for i, (qty_raw, price_raw) in enumerate(zip(quantities, prices)):
        qty   = _int_or_none(qty_raw)
        price = _float_or_none(price_raw)
        if qty and price is not None:
            note = notes_list[i].strip() if i < len(notes_list) else ''
            db.session.add(WharfPrice(
                species_id = species.id,
                quantity   = qty,
                price_gbp  = price,
                notes      = note or None,
            ))


# ── List ──────────────────────────────────────────────────────────────────────

@species_bp.route('/')
def list_species():
    search  = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'name')
    f_tank  = request.args.get('tank_idc', '')
    f_repro = request.args.get('reproduction_type', '')

    query = Species.query

    if search:
        like = f'%{search}%'
        query = query.filter(
            Species.common_name.ilike(like) | Species.scientific_name.ilike(like)
        )
    if f_tank:
        query = query.filter(Species.tank_idc == f_tank)
    if f_repro:
        query = query.filter(Species.reproduction_type == f_repro)

    if sort_by == 'tank':
        query = query.order_by(Species.tank_idc.nullslast(), Species.common_name)
    else:
        query = query.order_by(Species.common_name)

    all_species   = query.all()
    total_species = len(all_species)
    total_stock   = sum(s.current_stock for s in all_species)

    return render_template(
        'species/list.html',
        species_list  = all_species,
        total_species = total_species,
        total_stock   = total_stock,
        search        = search,
        sort_by       = sort_by,
        f_tank        = f_tank,
        f_repro       = f_repro,
        **_choice_lists(),
    )


# ── Add ───────────────────────────────────────────────────────────────────────

@species_bp.route('/add', methods=['GET', 'POST'])
def add_species():
    if request.method == 'POST':
        if not request.form.get('common_name', '').strip():
            flash('Common name is required.', 'danger')
            return render_template('species/form.html', species=None,
                                   is_edit=False, **_choice_lists())

        species = Species()
        _apply_form(species, request.form)
        db.session.add(species)
        db.session.flush()          # get species.id before saving prices
        _save_wharf_prices(species, request.form)
        db.session.commit()
        flash(f'{species.common_name} added successfully.', 'success')
        return redirect(url_for('species.detail', species_id=species.id))

    return render_template('species/form.html', species=None,
                           is_edit=False, **_choice_lists())


# ── Detail ────────────────────────────────────────────────────────────────────

@species_bp.route('/<int:species_id>')
def detail(species_id):
    species = Species.query.get_or_404(species_id)
    return render_template('species/detail.html', species=species)


# ── Edit ──────────────────────────────────────────────────────────────────────

@species_bp.route('/<int:species_id>/edit', methods=['GET', 'POST'])
def edit_species(species_id):
    species = Species.query.get_or_404(species_id)

    if request.method == 'POST':
        if not request.form.get('common_name', '').strip():
            flash('Common name is required.', 'danger')
            return render_template('species/form.html', species=species,
                                   is_edit=True, **_choice_lists())

        _apply_form(species, request.form)
        _save_wharf_prices(species, request.form)
        db.session.commit()
        flash(f'{species.common_name} updated.', 'success')
        return redirect(url_for('species.detail', species_id=species.id))

    return render_template('species/form.html', species=species,
                           is_edit=True, **_choice_lists())


# ── Delete ────────────────────────────────────────────────────────────────────

@species_bp.route('/<int:species_id>/delete', methods=['POST'])
def delete_species(species_id):
    species = Species.query.get_or_404(species_id)
    name    = species.common_name

    upload_folder = current_app.config['UPLOAD_FOLDER']
    for photo in species.photos:
        path = os.path.join(upload_folder, photo.filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.session.delete(species)
    db.session.commit()
    flash(f'{name} deleted.', 'success')
    return redirect(url_for('species.list_species'))


# ── Photo upload ──────────────────────────────────────────────────────────────

@species_bp.route('/<int:species_id>/photos/upload', methods=['POST'])
def upload_photo(species_id):
    species = Species.query.get_or_404(species_id)
    file    = request.files.get('photo')

    if not file or not file.filename:
        flash('No file selected.', 'warning')
        return redirect(url_for('species.detail', species_id=species_id))

    if not _allowed_file(file.filename):
        flash('Unsupported file type. Use PNG, JPG, GIF or WebP.', 'danger')
        return redirect(url_for('species.detail', species_id=species_id))

    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{ext}'
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    make_primary = bool(request.form.get('make_primary'))
    caption      = request.form.get('caption', '').strip() or None

    if make_primary:
        for p in species.photos:
            p.is_primary = False
        species.display_photo = filename

    photo = Photo(
        species_id  = species_id,
        filename    = filename,
        caption     = caption,
        is_primary  = make_primary,
        upload_date = date.today().isoformat(),
    )
    db.session.add(photo)

    # Auto-primary if this is the first photo
    if not species.display_photo:
        species.display_photo = filename
        photo.is_primary = True

    db.session.commit()
    flash('Photo uploaded.', 'success')
    return redirect(url_for('species.detail', species_id=species_id))


# ── Photo delete ──────────────────────────────────────────────────────────────

@species_bp.route('/photos/<int:photo_id>/delete', methods=['POST'])
def delete_photo(photo_id):
    photo   = Photo.query.get_or_404(photo_id)
    species = Species.query.get(photo.species_id)
    sid     = photo.species_id

    path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

    was_primary = photo.is_primary
    db.session.delete(photo)

    if species and was_primary:
        remaining = Photo.query.filter_by(species_id=sid).first()
        if remaining:
            remaining.is_primary  = True
            species.display_photo = remaining.filename
        else:
            species.display_photo = None

    db.session.commit()
    flash('Photo removed.', 'success')
    return redirect(url_for('species.detail', species_id=sid))
