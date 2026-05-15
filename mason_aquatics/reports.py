"""
Mason Aquatics — Reports & Available List PDF
Place this file at: routes/reports.py

GET  /reports/available-list         → HTML preview + filter form
POST /reports/available-list/pdf     → stream PDF download
"""

import os
import io
from datetime import date, datetime

from flask import (
    Blueprint, render_template, request, send_file, current_app
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics

from models import Species

reports_bp = Blueprint('reports', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_prices(wharf_prices):
    """Format wharf price tiers as a readable string."""
    if not wharf_prices:
        return '—'
    parts = []
    for wp in sorted(wharf_prices, key=lambda p: p.quantity):
        parts.append(f'{wp.quantity} for £{wp.price_gbp:.2f}')
    return ' | '.join(parts)


def _get_filtered_species(stock_filter, threshold, selected_ids):
    """Return species list matching the chosen filter."""
    query = Species.query.order_by(Species.common_name)
    all_species = query.all()

    if stock_filter == 'in_stock':
        return [s for s in all_species if s.current_stock > 0]
    elif stock_filter == 'threshold':
        try:
            t = int(threshold or 1)
        except (ValueError, TypeError):
            t = 1
        return [s for s in all_species if s.current_stock >= t]
    elif stock_filter == 'selected' and selected_ids:
        id_set = set(int(i) for i in selected_ids if i)
        return [s for s in all_species if s.id in id_set]
    else:  # 'all'
        return all_species


# ── Routes ────────────────────────────────────────────────────────────────────

@reports_bp.route('/available-list', methods=['GET'])
def available_list():
    """Render HTML preview of available list with filter form."""
    stock_filter  = request.args.get('stock_filter', 'in_stock')
    threshold     = request.args.get('threshold', '1')
    selected_ids  = request.args.getlist('species_ids')

    all_species   = Species.query.order_by(Species.common_name).all()
    preview_list  = _get_filtered_species(stock_filter, threshold, selected_ids)

    return render_template(
        'reports/available_list.html',
        all_species=all_species,
        preview_list=preview_list,
        stock_filter=stock_filter,
        threshold=threshold,
        selected_ids=selected_ids,
        today=date.today().strftime('%d/%m/%Y'),
    )


@reports_bp.route('/available-list/pdf', methods=['POST'])
def available_list_pdf():
    """Generate and stream the Available List PDF."""
    stock_filter = request.form.get('stock_filter', 'in_stock')
    threshold    = request.form.get('threshold', '1')
    selected_ids = request.form.getlist('species_ids')

    species_list = _get_filtered_species(stock_filter, threshold, selected_ids)

    buf = io.BytesIO()
    _build_pdf(buf, species_list)
    buf.seek(0)

    filename = f'mason_aquatics_available_{date.today().isoformat()}.pdf'
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf',
    )


# ── PDF Builder ───────────────────────────────────────────────────────────────

def _build_pdf(buf, species_list):
    """Build the Available List PDF into a BytesIO buffer."""
    PAGE_W, PAGE_H = A4
    MARGIN = 18 * mm

    # ── Styles ────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    accent      = colors.HexColor('#2196F3')
    dark        = colors.HexColor('#0d1117')
    muted       = colors.HexColor('#57606a')
    light_bg    = colors.HexColor('#f4f6f8')
    header_bg   = colors.HexColor('#2196F3')
    row_alt     = colors.HexColor('#f0f5fb')

    title_style = ParagraphStyle(
        'MATItle',
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=accent,
        spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        'MASub',
        fontSize=9,
        fontName='Helvetica',
        textColor=muted,
        spaceAfter=0,
    )
    date_style = ParagraphStyle(
        'MADate',
        fontSize=8,
        fontName='Helvetica',
        textColor=muted,
        alignment=TA_RIGHT,
    )
    cell_normal = ParagraphStyle(
        'Cell',
        fontSize=9,
        fontName='Helvetica',
        textColor=dark,
        leading=12,
    )
    cell_italic = ParagraphStyle(
        'CellItalic',
        fontSize=9,
        fontName='Helvetica-Oblique',
        textColor=muted,
        leading=12,
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=dark,
        leading=12,
    )
    cell_right = ParagraphStyle(
        'CellRight',
        fontSize=9,
        fontName='Helvetica',
        textColor=dark,
        alignment=TA_RIGHT,
        leading=12,
    )

    # ── Document ──────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 8 * mm,   # room for footer
        title='Mason Aquatics — Available Stock List',
    )

    today_str = date.today().strftime('%d %B %Y')
    story = []

    # ── Header block ──────────────────────────────────────────────────────────
    from reportlab.platypus import Table as RLTable

    header_data = [[
        Paragraph('Mason Aquatics', title_style),
        Paragraph(f'Generated: {today_str}', date_style),
    ]]
    header_table = RLTable(
        header_data,
        colWidths=[PAGE_W - 2 * MARGIN - 50 * mm, 50 * mm],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Paragraph('Available Stock List', sub_style))
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(
        width='100%',
        thickness=2,
        color=accent,
        spaceAfter=4 * mm,
    ))

    # ── Summary line ──────────────────────────────────────────────────────────
    total_species = len(species_list)
    total_fish    = sum(s.current_stock for s in species_list)
    summary_style = ParagraphStyle(
        'Summary',
        fontSize=8,
        fontName='Helvetica',
        textColor=muted,
        spaceAfter=4 * mm,
    )
    story.append(Paragraph(
        f'{total_species} species listed &nbsp;·&nbsp; '
        f'{total_fish} fish available',
        summary_style,
    ))

    # ── Table ─────────────────────────────────────────────────────────────────
    usable_w = PAGE_W - 2 * MARGIN

    # Column widths: Name | Scientific | Stock | Prices
    col_widths = [
        usable_w * 0.26,
        usable_w * 0.30,
        usable_w * 0.10,
        usable_w * 0.34,
    ]

    # Header row
    table_data = [[
        Paragraph('Common Name', ParagraphStyle(
            'TH', fontSize=8, fontName='Helvetica-Bold',
            textColor=colors.white)),
        Paragraph('Scientific Name', ParagraphStyle(
            'TH2', fontSize=8, fontName='Helvetica-Bold',
            textColor=colors.white)),
        Paragraph('Stock', ParagraphStyle(
            'TH3', fontSize=8, fontName='Helvetica-Bold',
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph('Wharf Sale Price(s)', ParagraphStyle(
            'TH4', fontSize=8, fontName='Helvetica-Bold',
            textColor=colors.white)),
    ]]

    if not species_list:
        table_data.append([
            Paragraph('No species match the selected filters.', cell_normal),
            '', '', '',
        ])
    else:
        for i, sp in enumerate(species_list):
            stock    = sp.current_stock
            prices   = _format_prices(sp.wharf_prices)
            sci_name = sp.scientific_name or '—'

            # Stock colour
            if stock <= 0:
                stock_color = colors.HexColor('#cf222e')
            elif stock < 3:
                stock_color = colors.HexColor('#9a6700')
            else:
                stock_color = colors.HexColor('#1a7f37')

            stock_style = ParagraphStyle(
                f'Stock{i}',
                fontSize=9,
                fontName='Helvetica-Bold',
                textColor=stock_color,
                alignment=TA_CENTER,
                leading=12,
            )

            table_data.append([
                Paragraph(sp.common_name, cell_bold),
                Paragraph(sci_name, cell_italic),
                Paragraph(str(stock), stock_style),
                Paragraph(prices, cell_normal),
            ])

    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    row_count = len(table_data)

    ts = TableStyle([
        # Header
        ('BACKGROUND',   (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR',    (0, 0), (-1, 0), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, row_count - 1), [colors.white, row_alt]),
        # Padding
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
        # Grid
        ('LINEBELOW',  (0, 0), (-1, 0), 0, header_bg),
        ('LINEBELOW',  (0, 1), (-1, -1), 0.3, colors.HexColor('#d0d7de')),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        # Span empty row if no data
    ])

    t.setStyle(ts)
    story.append(t)

    # ── Footer function ───────────────────────────────────────────────────────
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(muted)
        y = MARGIN - 5 * mm

        # Left: branding
        canvas.drawString(MARGIN, y, 'Mason Aquatics — Fish Room Management System')

        # Centre: page number
        page_num = f'Page {doc.page}'
        canvas.drawCentredString(PAGE_W / 2, y, page_num)

        # Right: date
        canvas.drawRightString(PAGE_W - MARGIN, y, f'Generated {today_str}')

        # Thin rule above footer
        canvas.setStrokeColor(colors.HexColor('#d0d7de'))
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y + 4 * mm, PAGE_W - MARGIN, y + 4 * mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
