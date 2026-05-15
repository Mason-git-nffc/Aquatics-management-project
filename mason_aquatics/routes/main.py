"""
Mason Aquatics — Main Routes (Dashboard + Settings)
Place this file at: routes/main.py

GET  /           → dashboard
POST /settings/theme  → quick theme toggle (called from topbar button, keep unchanged)
GET  /settings   → settings page
POST /settings   → save accent_colour, font_size, theme → redirect back
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, jsonify
)
from models import db, AppSettings, Species, Tank, BreedingRecord
from datetime import date
from collections import defaultdict

main_bp = Blueprint('main', __name__)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@main_bp.route('/')
def dashboard():
    from models import Sales, FeedLog, PowerCost

    total_species  = Species.query.count()
    total_stock    = sum(s.current_stock for s in Species.query.all())
    tanks_in_use   = Species.query.filter(Species.tank_idc != None).distinct(Species.tank_idc).count()
    total_tanks    = Tank.query.count()

    # Recent sales (last 5)
    try:
        recent_sales = Sales.query.order_by(Sales.sale_date.desc()).limit(5).all()
    except Exception:
        recent_sales = []

    # Recent breeding (last 5)
    recent_breeding = (
        BreedingRecord.query
        .order_by(BreedingRecord.record_date.desc())
        .limit(5)
        .all()
    )

    # Low stock species (≤2 and >0)
    low_stock = [s for s in Species.query.all() if 0 < s.current_stock <= 2]

    # This month's feed cost
    month = date.today().strftime('%Y-%m')
    try:
        month_feed = FeedLog.query.filter(FeedLog.feed_date.startswith(month)).all()
        feed_this_month = round(sum(f.cost_this_entry or 0 for f in month_feed), 2)
    except Exception:
        feed_this_month = 0

    return render_template(
        'dashboard.html',
        total_species=total_species,
        total_stock=total_stock,
        tanks_in_use=tanks_in_use,
        total_tanks=total_tanks,
        recent_sales=recent_sales,
        recent_breeding=recent_breeding,
        low_stock=low_stock,
        feed_this_month=feed_this_month,
        today=date.today().strftime('%d/%m/%Y'),
    )


# ── Quick theme toggle (called from topbar, keep unchanged) ───────────────────

@main_bp.route('/settings/theme', methods=['POST'])
def toggle_theme():
    data  = request.get_json(silent=True) or {}
    theme = data.get('theme', 'dark')
    if theme not in ('light', 'dark'):
        theme = 'dark'
    settings = AppSettings.query.get(1)
    if settings:
        settings.theme = theme
        db.session.commit()
    return jsonify({'ok': True, 'theme': theme})


# ── Settings page ─────────────────────────────────────────────────────────────

@main_bp.route('/settings', methods=['GET'])
def settings():
    """Render the settings page."""
    s = AppSettings.query.get(1)
    return render_template('settings.html', settings=s)


@main_bp.route('/settings', methods=['POST'])
def save_settings():
    """
    Save accent_colour, font_size, theme from the settings form.
    Redirects back to /settings with a success flash.
    """
    s = AppSettings.query.get(1)
    if not s:
        s = AppSettings(id=1)
        db.session.add(s)

    # Theme
    theme = request.form.get('theme', 'dark')
    if theme not in ('light', 'dark'):
        theme = 'dark'
    s.theme = theme

    # Accent colour — basic validation: must start with #
    accent = request.form.get('accent_colour', '#2196F3').strip()
    if not accent.startswith('#'):
        accent = '#2196F3'
    s.accent_colour = accent

    # Font size
    font_size = request.form.get('font_size', 'md')
    if font_size not in ('sm', 'md', 'lg', 'xl'):
        font_size = 'md'
    s.font_size = font_size

    db.session.commit()
    flash('Settings saved successfully.', 'success')
    return redirect(url_for('main.settings'))
