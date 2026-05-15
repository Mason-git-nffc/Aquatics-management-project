"""
Mason Aquatics — QR Code & Tank Label Generator
Place this file at: routes/labels.py

Generates:
  - PNG QR codes linking to /public/species/<id>
  - A4 PDF labels (99×57mm) with photo, names, temp, QR
"""

import os
import io
import qrcode
from flask import (
    Blueprint, render_template, current_app,
    send_file, redirect, url_for, flash, request
)
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from models import Species

labels_bp = Blueprint('labels', __name__)

# ── Label dimensions — 99×57mm (Avery L7636 style) ───────────────────────────
LABEL_W = 99 * mm
LABEL_H = 57 * mm


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_public_url(species_id):
    """Build the absolute public URL for a species page."""
    # Use request.host_url for reliable local + deployed URLs
    host = request.host_url.rstrip('/')
    return f"{host}/public/species/{species_id}"


def _generate_qr_png(species_id, url, generated_folder):
    """Generate and save a QR code PNG; returns filepath."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    path = os.path.join(generated_folder, f'qr_{species_id}.png')
    img.save(path)
    return path


def _draw_wrapped_text(c, text, x, y, max_width, font, font_size, line_height):
    """Draw text, wrapping if wider than max_width. Returns final y."""
    c.setFont(font, font_size)
    words = text.split()
    line = ''
    for word in words:
        test = (line + ' ' + word).strip()
        if c.stringWidth(test, font, font_size) <= max_width:
            line = test
        else:
            if line:
                c.drawString(x, y, line)
                y -= line_height
            line = word
    if line:
        c.drawString(x, y, line)
        y -= line_height
    return y


# ── Routes ────────────────────────────────────────────────────────────────────

@labels_bp.route('/')
def list_labels():
    """Label manager — list all species with generate buttons."""
    species_list = Species.query.order_by(Species.common_name).all()
    return render_template('labels/index.html', species_list=species_list)


@labels_bp.route('/qr/<int:species_id>')
def download_qr(species_id):
    """Generate and download a QR code PNG for the given species."""
    species = Species.query.get_or_404(species_id)
    generated_folder = current_app.config['GENERATED_FOLDER']

    url = _get_public_url(species_id)
    qr_path = _generate_qr_png(species_id, url, generated_folder)

    safe_name = species.common_name.replace(' ', '_').replace('/', '-')
    return send_file(
        qr_path,
        as_attachment=True,
        download_name=f'qr_{safe_name}.png',
        mimetype='image/png',
    )


@labels_bp.route('/label/<int:species_id>')
def generate_label(species_id):
    """Generate and download a PDF tank label for the given species."""
    species     = Species.query.get_or_404(species_id)
    generated   = current_app.config['GENERATED_FOLDER']
    upload_dir  = current_app.config['UPLOAD_FOLDER']

    # ── QR code ───────────────────────────────────────────────────────────────
    public_url = _get_public_url(species_id)
    qr_path    = _generate_qr_png(species_id, public_url, generated)

    # ── PDF setup ─────────────────────────────────────────────────────────────
    pdf_path = os.path.join(generated, f'label_{species_id}.pdf')
    c = canvas.Canvas(pdf_path, pagesize=(LABEL_W, LABEL_H))

    margin   = 3.5 * mm
    pad      = 2.5 * mm

    # ── Background: very subtle white ─────────────────────────────────────────
    c.setFillColor(colors.white)
    c.rect(0, 0, LABEL_W, LABEL_H, fill=1, stroke=0)

    # ── Thin border ───────────────────────────────────────────────────────────
    c.setStrokeColor(colors.HexColor('#cccccc'))
    c.setLineWidth(0.5)
    c.rect(0.5 * mm, 0.5 * mm, LABEL_W - 1 * mm, LABEL_H - 1 * mm, fill=0, stroke=1)

    # ── Accent stripe across top ──────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#2196F3'))
    c.rect(0, LABEL_H - 5.5 * mm, LABEL_W, 5.5 * mm, fill=1, stroke=0)

    # Brand text in stripe
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 7)
    c.drawString(margin, LABEL_H - 4 * mm, 'MASON AQUATICS')

    # ── Photo (left column) ───────────────────────────────────────────────────
    photo_size = 36 * mm
    photo_x    = margin
    photo_y    = (LABEL_H - 5.5 * mm - photo_size) / 2   # vertically centred below stripe

    has_photo = False
    if species.display_photo:
        photo_path = os.path.join(upload_dir, species.display_photo)
        if os.path.exists(photo_path):
            try:
                c.drawImage(
                    photo_path,
                    photo_x, photo_y,
                    width=photo_size, height=photo_size,
                    preserveAspectRatio=True,
                    mask='auto',
                )
                has_photo = True
            except Exception:
                pass

    if not has_photo:
        # Placeholder box
        c.setStrokeColor(colors.HexColor('#dddddd'))
        c.setFillColor(colors.HexColor('#f5f5f5'))
        c.rect(photo_x, photo_y, photo_size, photo_size, fill=1, stroke=1)
        c.setFillColor(colors.HexColor('#aaaaaa'))
        c.setFont('Helvetica', 7)
        c.drawCentredString(photo_x + photo_size / 2, photo_y + photo_size / 2 - 3, 'No Photo')

    # ── QR code (right column) ────────────────────────────────────────────────
    qr_size = 28 * mm
    qr_x    = LABEL_W - margin - qr_size
    qr_y    = (LABEL_H - 5.5 * mm - qr_size) / 2

    try:
        c.drawImage(qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
    except Exception:
        pass

    # Tiny 'Scan me' label under QR
    c.setFillColor(colors.HexColor('#888888'))
    c.setFont('Helvetica', 5.5)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 3.5 * mm, 'Scan for info')

    # ── Text column (centre) ──────────────────────────────────────────────────
    text_x      = photo_x + photo_size + pad
    text_max_w  = qr_x - text_x - pad
    text_y      = LABEL_H - 5.5 * mm - pad - 2 * mm   # just below stripe

    # Common name
    c.setFillColor(colors.HexColor('#111111'))
    text_y = _draw_wrapped_text(
        c, species.common_name,
        text_x, text_y, text_max_w,
        'Helvetica-Bold', 10, 5.5 * mm,
    )
    text_y -= 0.5 * mm

    # Scientific name (italic)
    sci = species.scientific_name or ''
    if sci:
        c.setFillColor(colors.HexColor('#555555'))
        text_y = _draw_wrapped_text(
            c, sci,
            text_x, text_y, text_max_w,
            'Helvetica-Oblique', 8, 4.5 * mm,
        )
        text_y -= 1.5 * mm

    # Divider rule
    c.setStrokeColor(colors.HexColor('#dddddd'))
    c.setLineWidth(0.4)
    c.line(text_x, text_y + 1.5 * mm, text_x + text_max_w, text_y + 1.5 * mm)
    text_y -= 3 * mm

    # Temperature
    c.setFillColor(colors.HexColor('#222222'))
    c.setFont('Helvetica', 8)
    if species.min_temp_c is not None or species.max_temp_c is not None:
        mn = int(species.min_temp_c) if species.min_temp_c is not None else '?'
        mx = int(species.max_temp_c) if species.max_temp_c is not None else '?'
        c.drawString(text_x, text_y, f'\u26a1  {mn}°C – {mx}°C')
        text_y -= 5 * mm

    # pH
    if species.ideal_ph is not None:
        c.drawString(text_x, text_y, f'pH  {species.ideal_ph}')
        text_y -= 5 * mm

    # Reproduction type
    if species.reproduction_type:
        c.setFont('Helvetica', 7)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(text_x, text_y, species.reproduction_type)

    c.save()

    safe_name = species.common_name.replace(' ', '_').replace('/', '-')
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f'label_{safe_name}.pdf',
        mimetype='application/pdf',
    )


@labels_bp.route('/label/batch', methods=['POST'])
def batch_labels():
    """Generate a single PDF containing multiple labels (one per page)."""
    ids = request.form.getlist('species_ids')
    if not ids:
        flash('Please select at least one species.', 'warning')
        return redirect(url_for('labels.list_labels'))

    generated   = current_app.config['GENERATED_FOLDER']
    upload_dir  = current_app.config['UPLOAD_FOLDER']
    pdf_path    = os.path.join(generated, 'batch_labels.pdf')

    c = canvas.Canvas(pdf_path, pagesize=(LABEL_W, LABEL_H))

    for i, sid_str in enumerate(ids):
        sid     = int(sid_str)
        species = Species.query.get(sid)
        if not species:
            continue

        if i > 0:
            c.showPage()

        # ── Re-use single-label drawing logic via inner call ──────────────────
        # Build QR
        pub_url  = _get_public_url(sid)
        qr_path  = _generate_qr_png(sid, pub_url, generated)

        # Background
        c.setFillColor(colors.white)
        c.rect(0, 0, LABEL_W, LABEL_H, fill=1, stroke=0)

        # Border
        c.setStrokeColor(colors.HexColor('#cccccc'))
        c.setLineWidth(0.5)
        c.rect(0.5 * mm, 0.5 * mm, LABEL_W - 1 * mm, LABEL_H - 1 * mm, fill=0, stroke=1)

        # Accent stripe
        c.setFillColor(colors.HexColor('#2196F3'))
        c.rect(0, LABEL_H - 5.5 * mm, LABEL_W, 5.5 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 7)
        c.drawString(3.5 * mm, LABEL_H - 4 * mm, 'MASON AQUATICS')

        margin    = 3.5 * mm
        pad       = 2.5 * mm
        photo_size = 36 * mm
        photo_x   = margin
        photo_y   = (LABEL_H - 5.5 * mm - photo_size) / 2

        # Photo
        has_photo = False
        if species.display_photo:
            pp = os.path.join(upload_dir, species.display_photo)
            if os.path.exists(pp):
                try:
                    c.drawImage(pp, photo_x, photo_y,
                                width=photo_size, height=photo_size,
                                preserveAspectRatio=True, mask='auto')
                    has_photo = True
                except Exception:
                    pass

        if not has_photo:
            c.setStrokeColor(colors.HexColor('#dddddd'))
            c.setFillColor(colors.HexColor('#f5f5f5'))
            c.rect(photo_x, photo_y, photo_size, photo_size, fill=1, stroke=1)
            c.setFillColor(colors.HexColor('#aaaaaa'))
            c.setFont('Helvetica', 7)
            c.drawCentredString(photo_x + photo_size / 2, photo_y + photo_size / 2 - 3, 'No Photo')

        # QR
        qr_size = 28 * mm
        qr_x    = LABEL_W - margin - qr_size
        qr_y    = (LABEL_H - 5.5 * mm - qr_size) / 2
        try:
            c.drawImage(qr_path, qr_x, qr_y, width=qr_size, height=qr_size)
        except Exception:
            pass
        c.setFillColor(colors.HexColor('#888888'))
        c.setFont('Helvetica', 5.5)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 3.5 * mm, 'Scan for info')

        # Text
        text_x     = photo_x + photo_size + pad
        text_max_w = qr_x - text_x - pad
        text_y     = LABEL_H - 5.5 * mm - pad - 2 * mm

        c.setFillColor(colors.HexColor('#111111'))
        text_y = _draw_wrapped_text(c, species.common_name, text_x, text_y,
                                    text_max_w, 'Helvetica-Bold', 10, 5.5 * mm)
        text_y -= 0.5 * mm

        if species.scientific_name:
            c.setFillColor(colors.HexColor('#555555'))
            text_y = _draw_wrapped_text(c, species.scientific_name, text_x, text_y,
                                        text_max_w, 'Helvetica-Oblique', 8, 4.5 * mm)
            text_y -= 1.5 * mm

        c.setStrokeColor(colors.HexColor('#dddddd'))
        c.setLineWidth(0.4)
        c.line(text_x, text_y + 1.5 * mm, text_x + text_max_w, text_y + 1.5 * mm)
        text_y -= 3 * mm

        c.setFillColor(colors.HexColor('#222222'))
        c.setFont('Helvetica', 8)
        if species.min_temp_c is not None or species.max_temp_c is not None:
            mn = int(species.min_temp_c) if species.min_temp_c is not None else '?'
            mx = int(species.max_temp_c) if species.max_temp_c is not None else '?'
            c.drawString(text_x, text_y, f'{mn}\xb0C \u2013 {mx}\xb0C')
            text_y -= 5 * mm
        if species.ideal_ph is not None:
            c.drawString(text_x, text_y, f'pH  {species.ideal_ph}')
            text_y -= 5 * mm
        if species.reproduction_type:
            c.setFont('Helvetica', 7)
            c.setFillColor(colors.HexColor('#555555'))
            c.drawString(text_x, text_y, species.reproduction_type)

    c.save()

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name='mason_aquatics_labels.pdf',
        mimetype='application/pdf',
    )
