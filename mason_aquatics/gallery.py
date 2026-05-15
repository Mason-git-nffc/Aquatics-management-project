"""
Mason Aquatics — Central Gallery Routes
Place this file at: routes/gallery.py
"""

from flask import Blueprint, render_template, request
from models import Photo, Species
from collections import defaultdict

gallery_bp = Blueprint('gallery', __name__)


@gallery_bp.route('/')
def index():
    """Central photo gallery, browseable and filterable by species."""
    f_species = request.args.get('species_id', '')
    view_mode = request.args.get('view', 'grouped')   # 'grouped' | 'all'

    # Base query
    query = Photo.query.join(Species, Photo.species_id == Species.id)

    if f_species:
        query = query.filter(Photo.species_id == int(f_species))
        view_mode = 'all'   # when filtering to one species, show flat grid

    photos = query.order_by(Photo.upload_date.desc()).all()

    # All species that have at least one photo (for filter dropdown)
    species_with_photos_ids = set(p.species_id for p in Photo.query.all())
    all_species = (
        Species.query
        .filter(Species.id.in_(species_with_photos_ids))
        .order_by(Species.common_name)
        .all()
    ) if species_with_photos_ids else []

    # All species for "no filter" dropdown too
    all_species_full = Species.query.order_by(Species.common_name).all()

    # Grouped view — photos per species
    grouped = defaultdict(list)
    for p in photos:
        grouped[p.species_id].append(p)

    # Order groups by species common name
    grouped_list = []
    for s in (all_species if f_species == '' else []):
        if s.id in grouped:
            grouped_list.append((s, grouped[s.id]))

    # Stats
    total_photos   = Photo.query.count()
    total_species_with_photos = len(species_with_photos_ids)

    return render_template(
        'gallery/index.html',
        photos=photos,
        all_species=all_species_full,
        f_species=f_species,
        view_mode=view_mode,
        grouped_list=grouped_list,
        total_photos=total_photos,
        total_species_with_photos=total_species_with_photos,
    )
