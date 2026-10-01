"""
Mason Aquatics — Central Gallery Routes
Place this file at: routes/gallery.py

Template contract (templates/gallery/index.html):
    groups           list of (Species, [Photo, ...])   — grouped view
    photos_flat      list of {'photo': Photo, 'species': Species} — flat view
    all_species      species that have at least one photo (filter dropdown)
    selected_species species id as a string ('' when unfiltered)
    view_mode        'grouped' | 'all'
    total_photos     int
"""

from flask import Blueprint, render_template, request
from models import Photo, Species

gallery_bp = Blueprint('gallery', __name__)


@gallery_bp.route('/')
def index():
    """Central photo gallery, browseable and filterable by species."""
    selected_species = request.args.get('species_id', '').strip()
    view_mode        = request.args.get('view', 'grouped')
    if view_mode not in ('grouped', 'all'):
        view_mode = 'grouped'

    query = Photo.query.join(Species, Photo.species_id == Species.id)

    if selected_species:
        try:
            query = query.filter(Photo.species_id == int(selected_species))
        except ValueError:
            selected_species = ''

    # Primary photos first, then newest first
    photos = (
        query.order_by(Species.common_name,
                       Photo.is_primary.desc(),
                       Photo.upload_date.desc(),
                       Photo.id.desc())
        .all()
    )

    # Grouped view — photos per species, ordered by common name
    groups, index_by_species = [], {}
    for p in photos:
        if p.species_id not in index_by_species:
            index_by_species[p.species_id] = len(groups)
            groups.append((p.species, []))
        groups[index_by_species[p.species_id]][1].append(p)

    # Flat view — newest first across all species
    photos_flat = [
        {'photo': p, 'species': p.species}
        for p in sorted(photos, key=lambda p: (p.upload_date or '', p.id), reverse=True)
    ]

    # Dropdown: species with at least one photo
    all_species = (
        Species.query
        .join(Photo, Photo.species_id == Species.id)
        .distinct()
        .order_by(Species.common_name)
        .all()
    )

    return render_template(
        'gallery/index.html',
        groups           = groups,
        photos_flat      = photos_flat,
        all_species      = all_species,
        selected_species = selected_species,
        view_mode        = view_mode,
        total_photos     = Photo.query.count(),
    )
