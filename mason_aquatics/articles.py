"""
Mason Aquatics — Documentation Articles Routes
Place this file at: routes/articles.py

GET  /articles/                 → list all articles
GET  /articles/new              → blank editor (optional ?species_id= or ?tank_idc=)
POST /articles/new              → save new → redirect to detail
GET  /articles/<id>             → read-only rendered view
GET  /articles/<id>/edit        → editor pre-filled
POST /articles/<id>/edit        → save edits → redirect to detail
POST /articles/<id>/delete      → delete → redirect to list
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from models import db, Article, Species
from datetime import datetime

articles_bp = Blueprint('articles', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _int_or_none(val):
    try:
        return int(val) if val and str(val).strip() else None
    except (ValueError, TypeError):
        return None


# ── Article list ──────────────────────────────────────────────────────────────

@articles_bp.route('/')
def list_articles():
    """Index of all documentation articles, newest first."""
    articles = Article.query.order_by(Article.updated_at.desc()).all()
    return render_template('articles/list.html', articles=articles)


# ── New article ───────────────────────────────────────────────────────────────

@articles_bp.route('/new', methods=['GET', 'POST'])
def new_article():
    """Create a new article. Supports ?species_id= and ?tank_idc= pre-fills."""
    all_species = Species.query.order_by(Species.common_name).all()

    # Pre-fill hints from query string
    pre_species_id = request.args.get('species_id', type=int)
    pre_tank_idc   = request.args.get('tank_idc', '').strip()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('A title is required.', 'danger')
            return render_template(
                'articles/form.html',
                article=None,
                all_species=all_species,
                pre_species_id=pre_species_id,
                pre_tank_idc=pre_tank_idc,
            )

        species_id   = _int_or_none(request.form.get('species_id'))
        tank_idc     = request.form.get('tank_idc', '').strip() or None
        content_html = request.form.get('content_html', '').strip()

        article = Article(
            title        = title,
            content_html = content_html,
            species_id   = species_id,
            tank_idc     = tank_idc,
        )
        db.session.add(article)
        db.session.commit()
        flash('Article created.', 'success')
        return redirect(url_for('articles.article_detail', article_id=article.id))

    return render_template(
        'articles/form.html',
        article=None,
        all_species=all_species,
        pre_species_id=pre_species_id,
        pre_tank_idc=pre_tank_idc,
    )


# ── Article detail (read-only) ────────────────────────────────────────────────

@articles_bp.route('/<int:article_id>')
def article_detail(article_id):
    """Read-only rendered article view."""
    article = Article.query.get_or_404(article_id)
    species = Species.query.get(article.species_id) if article.species_id else None
    return render_template('articles/detail.html', article=article, species=species)


# ── Edit article ──────────────────────────────────────────────────────────────

@articles_bp.route('/<int:article_id>/edit', methods=['GET', 'POST'])
def edit_article(article_id):
    """Edit an existing article."""
    article     = Article.query.get_or_404(article_id)
    all_species = Species.query.order_by(Species.common_name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('A title is required.', 'danger')
            return render_template(
                'articles/form.html',
                article=article,
                all_species=all_species,
                pre_species_id=article.species_id,
                pre_tank_idc=article.tank_idc or '',
            )

        article.title        = title
        article.content_html = request.form.get('content_html', '').strip()
        article.species_id   = _int_or_none(request.form.get('species_id'))
        article.tank_idc     = request.form.get('tank_idc', '').strip() or None

        db.session.commit()
        flash('Article updated.', 'success')
        return redirect(url_for('articles.article_detail', article_id=article.id))

    return render_template(
        'articles/form.html',
        article=article,
        all_species=all_species,
        pre_species_id=article.species_id,
        pre_tank_idc=article.tank_idc or '',
    )


# ── Delete article ────────────────────────────────────────────────────────────

@articles_bp.route('/<int:article_id>/delete', methods=['POST'])
def delete_article(article_id):
    """Delete an article and redirect to the list."""
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'success')
    return redirect(url_for('articles.list_articles'))
