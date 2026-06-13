"""
Mason Aquatics — Reports Blueprint  (Phase 7)
Place this file at: routes/reports.py

Endpoints
---------
GET  /reports/available-list              HTML preview + filter form
POST /reports/available-list/pdf          Stream PDF download
"""

import io
from datetime import date, datetime

from flask import (
    Blueprint, render_template, request, make_response, flash, redirect, url_for
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from models import db, Species

reports_bp = Blueprint('reports', __name__)

# ── Brand colours ─────────────────────────────────────────────────────────────
ACCENT      = colors.HexColor('#2196F3')
ACCENT_DARK = colors.HexColor('#1565C0')
LIGHT_BG    = colors.HexColor('#E3F2FD')
HEADER_BG   = colors.HexColor('#0D47A1')
ROW_ALT     = colors.HexColor('#F5F9FF')
TEXT_DARK   = colors.HexColor('#1A1A2E')
TEXT_MUTED  = colors.HexColor('#546E7A')
SUCCESS     = colors.HexColor('#2E7D32')
WARNING     = colors.HexColor('#E65100')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_wharf_prices(species):
    """Return tier string like '1 for £3.00 | 6 for £15.00' or '—'."""
    tiers = sorted(species.wharf_prices, key=lambda w: w.quantity)
    if not tiers:
        return '—'
    return ' | '.join(f"{w.quantity} for £{w.price_gbp:.2f}" for w in tiers)


def _apply_filter(form):
    """
    Return (species_list, filter_mode, threshold, selected_ids).
    filter_mode: 'in_stock' | 'all' | 'threshold' | 'selected'
    """
    mode        = form.get('filter_mode', 'in_stock')
    threshold   = None
    selected_ids = []

    all_sp = Species.query.order_by(Species.common_name).all()

    if mode == 'in_stock':
        result = [s for s in all_sp if s.current_stock > 0]

    elif mode == 'all':
        result = all_sp

    elif mode == 'threshold':
        try:
            threshold = int(form.get('threshold', 1))
        except (ValueError, TypeError):
            threshold = 1
        result = [s for s in all_sp if s.current_stock > threshold]

    elif mode == 'selected':
        raw = form.getlist('species_ids')
        try:
            selected_ids = [int(x) for x in raw if x]
        except ValueError:
            selected_ids = []
        result = [s for s in all_sp if s.id in selected_ids]

    else:
        result = [s for s in all_sp if s.current_stock > 0]

    return result, mode, threshold, selected_ids


# ── HTML preview ──────────────────────────────────────────────────────────────

@reports_bp.route('/available-list', methods=['GET', 'POST'])
def available_list():
    all_species = Species.query.order_by(Species.common_name).all()

    # POST = regenerate preview; GET = default in-stock view
    form        = request.form if request.method == 'POST' else request.args
    mode        = form.get('filter_mode', 'in_stock')
    threshold   = form.get('threshold', '1')
    selected_ids_raw = form.getlist('species_ids')

    try:
        selected_ids = [int(x) for x in selected_ids_raw if x]
    except ValueError:
        selected_ids = []
    try:
        threshold_int = int(threshold) if threshold else 1
    except ValueError:
        threshold_int = 1

    # Build preview list
    if mode == 'in_stock':
        preview = [s for s in all_species if s.current_stock > 0]
    elif mode == 'all':
        preview = list(all_species)
    elif mode == 'threshold':
        preview = [s for s in all_species if s.current_stock > threshold_int]
    elif mode == 'selected':
        preview = [s for s in all_species if s.id in selected_ids]
    else:
        preview = [s for s in all_species if s.current_stock > 0]

    today_str = date.today().strftime('%d %B %Y')

    return render_template(
        'reports/available_list.html',
        all_species   = all_species,
        preview       = preview,
        filter_mode   = mode,
        threshold     = threshold,
        selected_ids  = selected_ids,
        today_str     = today_str,
        format_prices = _format_wharf_prices,
    )


# ── PDF download ──────────────────────────────────────────────────────────────

@reports_bp.route('/available-list/pdf', methods=['POST'])
def available_list_pdf():
    species_list, mode, threshold, selected_ids = _apply_filter(request.form)

    if not species_list:
        flash('No species matched your filter — PDF not generated.', 'warning')
        return redirect(url_for('reports.available_list'))

    buf = io.BytesIO()
    _build_pdf(buf, species_list)
    buf.seek(0)

    filename = f"mason_aquatics_available_{date.today().isoformat()}.pdf"
    response = make_response(buf.read())
    response.headers['Content-Type']        = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ── PDF builder ───────────────────────────────────────────────────────────────

def _build_pdf(buffer, species_list):
    PAGE_W, PAGE_H = A4
    MARGIN = 18 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize    = A4,
        leftMargin  = MARGIN,
        rightMargin = MARGIN,
        topMargin   = MARGIN,
        bottomMargin= MARGIN + 8 * mm,
        title       = 'Mason Aquatics — Available Stock List',
        author      = 'Mason Aquatics',
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'MATitle',
        fontSize    = 18,
        fontName    = 'Helvetica-Bold',
        textColor   = colors.white,
        alignment   = TA_LEFT,
        spaceAfter  = 0,
    )
    subtitle_style = ParagraphStyle(
        'MASubtitle',
        fontSize   = 9,
        fontName   = 'Helvetica',
        textColor  = colors.HexColor('#BBDEFB'),
        alignment  = TA_LEFT,
    )
    col_header_style = ParagraphStyle(
        'MAColHeader',
        fontSize   = 8,
        fontName   = 'Helvetica-Bold',
        textColor  = colors.white,
        alignment  = TA_CENTER,
    )
    cell_normal = ParagraphStyle(
        'MACellNormal',
        fontSize   = 8.5,
        fontName   = 'Helvetica',
        textColor  = TEXT_DARK,
        alignment  = TA_LEFT,
    )
    cell_italic = ParagraphStyle(
        'MACellItalic',
        fontSize   = 8,
        fontName   = 'Helvetica-Oblique',
        textColor  = TEXT_MUTED,
        alignment  = TA_LEFT,
    )
    cell_center = ParagraphStyle(
        'MACellCenter',
        fontSize   = 9,
        fontName   = 'Helvetica-Bold',
        textColor  = TEXT_DARK,
        alignment  = TA_CENTER,
    )
    cell_price = ParagraphStyle(
        'MACellPrice',
        fontSize   = 8,
        fontName   = 'Helvetica',
        textColor  = TEXT_DARK,
        alignment  = TA_LEFT,
    )

    # ── Column widths ──────────────────────────────────────────────────────
    usable = PAGE_W - 2 * MARGIN
    COL_W = [
        usable * 0.27,   # Common Name
        usable * 0.27,   # Scientific Name
        usable * 0.10,   # Stock
        usable * 0.36,   # Wharf Prices
    ]

    # ── Content list ───────────────────────────────────────────────────────
    story = []

    today_str = datetime.now().strftime('%d %B %Y')
    gen_time  = datetime.now().strftime('%H:%M')

    # ── Header banner (drawn as a coloured table) ──────────────────────────
    header_table = Table(
        [[
            Paragraph('Mason Aquatics', title_style),
            Paragraph(
                f'Available Stock List<br/>'
                f'<font size="8" color="#BBDEFB">Generated: {today_str} at {gen_time}</font>',
                subtitle_style
            ),
        ]],
        colWidths=[usable * 0.5, usable * 0.5],
    )
    header_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), HEADER_BG),
        ('TOPPADDING',   (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 10),
        ('LEFTPADDING',  (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # ── Summary strip ──────────────────────────────────────────────────────
    total_fish = sum(s.current_stock for s in species_list)
    summary_data = [[
        Paragraph(f'<b>{len(species_list)}</b> species listed', cell_normal),
        Paragraph(f'<b>{total_fish}</b> fish available', cell_normal),
        Paragraph(f'<b>{today_str}</b>', cell_normal),
    ]]
    summary_table = Table(summary_data, colWidths=[usable / 3] * 3)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_BG),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('BOX',           (0, 0), (-1, -1), 0.5, ACCENT),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, colors.HexColor('#BBDEFB')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 5 * mm))

    # ── Main table ─────────────────────────────────────────────────────────
    col_headers = [
        Paragraph('Common Name',       col_header_style),
        Paragraph('Scientific Name',   col_header_style),
        Paragraph('In Stock',          col_header_style),
        Paragraph('Wharf Sale Prices', col_header_style),
    ]

    table_data = [col_headers]

    for i, sp in enumerate(species_list):
        stock = sp.current_stock
        # Stock colour: green if healthy, amber if low (≤2), red if zero
        if stock <= 0:
            stock_colour = colors.HexColor('#C62828')
        elif stock <= 2:
            stock_colour = colors.HexColor('#E65100')
        else:
            stock_colour = SUCCESS

        stock_style = ParagraphStyle(
            f'stock_{i}',
            fontSize  = 9,
            fontName  = 'Helvetica-Bold',
            textColor = stock_colour,
            alignment = TA_CENTER,
        )

        price_str = _format_wharf_prices(sp)

        row = [
            Paragraph(sp.common_name or '—',             cell_normal),
            Paragraph(sp.scientific_name or '—',         cell_italic),
            Paragraph(str(stock),                         stock_style),
            Paragraph(price_str,                          cell_price),
        ]
        table_data.append(row)

    main_table = Table(table_data, colWidths=COL_W, repeatRows=1)

    row_count = len(table_data)
    ts = TableStyle([
        # Header row
        ('BACKGROUND',    (0, 0), (-1, 0),  ACCENT),
        ('TOPPADDING',    (0, 0), (-1, 0),  7),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  7),
        ('LEFTPADDING',   (0, 0), (-1, 0),  8),
        ('RIGHTPADDING',  (0, 0), (-1, 0),  8),
        # Data rows
        ('TOPPADDING',    (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING',   (0, 1), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 1), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        # Grid
        ('INNERGRID',     (0, 0), (-1, -1), 0.25, colors.HexColor('#CFD8DC')),
        ('BOX',           (0, 0), (-1, -1), 0.5,  ACCENT),
        # Alternate row shading
        *[
            ('BACKGROUND', (0, r), (-1, r), ROW_ALT)
            for r in range(2, row_count, 2)
        ],
    ])
    main_table.setStyle(ts)
    story.append(main_table)

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=ACCENT))
    story.append(Spacer(1, 2 * mm))

    footer_style = ParagraphStyle(
        'MAFooter',
        fontSize  = 7,
        fontName  = 'Helvetica',
        textColor = TEXT_MUTED,
        alignment = TA_CENTER,
    )
    story.append(Paragraph(
        'Mason Aquatics · Fish Room Management System · '
        'This list is for personal/trade use only.',
        footer_style
    ))

    # ── Page template with page numbers ───────────────────────────────────
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(TEXT_MUTED)
        canvas.drawRightString(
            PAGE_W - MARGIN,
            10 * mm,
            f'Page {doc.page}  ·  Mason Aquatics Available Stock List  ·  {today_str}'
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
