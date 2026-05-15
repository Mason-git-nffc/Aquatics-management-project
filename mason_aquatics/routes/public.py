"""
Mason Aquatics — Public Species Page (no login required)
Place this file at: routes/public.py

These pages are linked from QR codes on printed tank labels.
No authentication, no sidebar — clean read-only display.
"""

from flask import Blueprint, render_template
from models import Species

public_bp = Blueprint('public', __name__)


@public_bp.route('/species/<int:species_id>')
def species_page(species_id):
    """
    Public-facing species info page.
    Accessible at /public/species/<id> — no login required.
    Linked from QR codes printed on tank labels.
    """
    species = Species.query.get_or_404(species_id)
    return render_template('public/species.html', species=species)
