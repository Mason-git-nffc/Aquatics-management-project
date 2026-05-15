# Mason Aquatics — Session Resume Guide

## How to Resume This Project in a New Claude Session

### Step 1 — Download These Files
Save all output files from this session to your computer before closing.

### Step 2 — Start a New Claude Session
Open a new conversation at claude.ai

### Step 3 — Upload Your Files
Upload the following at the start of your message:
- `README.md`
- `PHASE_PLAN.md`
- `DATABASE_SCHEMA.md`
- `SESSION_RESUME.md` (this file)
- All `.py` and `.html` files built so far

### Step 4 — Paste the Resume Prompt Below

---

## ✅ READY-TO-USE RESUME PROMPT — PHASE 10

Copy and paste this exactly into your next session (after uploading files):

```
I am building the Mason Aquatics fish room management system.

Attached files:
- README.md          — project overview and stack
- PHASE_PLAN.md      — full 10-phase build plan
- DATABASE_SCHEMA.md — all table definitions
- SESSION_RESUME.md  — this resume guide
- models.py          — all SQLAlchemy models (complete, do not modify)
- app.py             — Flask app with all blueprints registered (Phases 1–9)
- routes/main.py     — dashboard + theme toggle + GET/POST /settings
- routes/species.py  — species CRUD, photo upload, wharf prices
- routes/tanks.py    — tank list, detail, water tests, equipment, primer calc
- routes/breeding.py — breeding CRUD, central log, inline add from species page
- routes/sales.py    — sales CRUD, customer CRUD, store credit management
- routes/gallery.py  — central gallery, grouped by species + flat view, filterable
- routes/public.py   — public species page at /public/species/<id> (no auth)
- routes/labels.py   — QR code PNG generator, single PDF label, batch PDF labels
- routes/reports.py  — available list HTML preview + PDF download (ReportLab A4)
- routes/costs.py    — cost dashboard, feed log CRUD, power cost CRUD
- templates/base.html                       (all sidebar links live — Phases 1–9;
                                             Settings footer btn → url_for('main.settings');
                                             gear icon shortcut in topbar)
- templates/dashboard.html
- templates/settings.html                   ← NEW Phase 9
- templates/species/list.html
- templates/species/form.html
- templates/species/detail.html
- templates/tanks/list.html
- templates/tanks/detail.html
- templates/tanks/edit.html
- templates/breeding/list.html
- templates/breeding/form.html
- templates/sales/list.html
- templates/sales/form.html
- templates/sales/customer_list.html
- templates/sales/customer_detail.html
- templates/sales/customer_form.html
- templates/gallery/index.html
- templates/public/species.html
- templates/labels/index.html
- templates/reports/available_list.html
- templates/costs/dashboard.html
- templates/costs/feed_log.html
- templates/costs/power.html

Phases completed: 1 (Foundation), 2 (Tank Management), 3 (Breeding Records),
4 (Sales System), 5 (Gallery System), 6 (QR Codes & Labels),
7 (Reports & Available List PDF), 8 (Cost Controls), 9 (Settings Page).

Phase 9 delivered:
- routes/main.py — updated main_bp with two new endpoints:
    GET  /settings  → renders templates/settings.html
    POST /settings  → validates + saves theme, accent_colour, font_size to
                      AppSettings (id=1), flashes success, redirects back
    POST /settings/theme already existed — kept unchanged (topbar quick toggle)
- templates/settings.html — full settings page extending base.html:
    * Theme section: Dark / Light visual preview cards with radio buttons;
      selecting applies theme live to the page AND pings /settings/theme
      so the topbar toggle stays in sync
    * Accent Colour section: 8 preset swatches (Blue, Emerald, Purple, Amber,
      Red, Pink, Teal, Indigo) + <input type="color"> custom picker;
      either updates CSS --accent live; selected swatch shows checkmark ring
    * Font Size section: four buttons (Small / Medium / Large / XL);
      clicking previews the size live via document.documentElement.style.fontSize
    * Sticky save bar at bottom with Cancel + Save Settings buttons
    * Side nav links scroll to each section smoothly
- templates/base.html — updated:
    * Sidebar footer Settings button: href → url_for('main.settings'),
      gains .active class (blue ring + tinted bg) when on settings page
    * Gear icon shortcut added to topbar actions row alongside theme toggle,
      also with active state when request.endpoint == 'main.settings'
    * --accent and --font-size-base :root vars now guard against None values

Please continue with Phase 10 — Documentation Pages:

Phase 10 should deliver:
- models.py already has an Article model with fields:
    id, title, content_html, species_id (nullable FK → species),
    tank_idc (nullable), created_at, updated_at
  Do not modify models.py — the model is already complete.
- routes/articles.py — new blueprint at /articles:
    GET  /articles/                        → list all articles
    GET  /articles/new                     → blank editor form
    GET  /articles/new?species_id=<id>     → pre-linked to species
    GET  /articles/new?tank_idc=<idc>      → pre-linked to tank
    POST /articles/new                     → save new article → redirect to detail
    GET  /articles/<id>                    → read-only article view (rendered HTML)
    GET  /articles/<id>/edit               → editor form pre-filled
    POST /articles/<id>/edit               → save edits → redirect to detail
    POST /articles/<id>/delete             → delete → redirect to list
- templates/articles/list.html   — article index: title, linked species/tank, date, actions
- templates/articles/form.html   — create/edit form using Quill.js rich text editor (CDN):
    * Title input
    * Link to Species dropdown (optional — all species, populated from DB)
    * Link to Tank dropdown (optional — T#01–T#30)
    * Quill editor for content_html (toolbar: bold, italic, headings, lists,
      blockquote, link, code block, clean)
    * Save and Cancel buttons
- templates/articles/detail.html — clean read-only rendered article view:
    * Article title as <h1>
    * Linked species name (with link to species detail) if set
    * Linked tank IDC (with link to tank detail) if set
    * Rendered content_html in a styled content area
    * Edit and Delete buttons
    * "Back to list" breadcrumb
- templates/species/detail.html — updated: add a "Further Information" button/section
  that links to the article if species.article_id is set, or shows
  "Add Documentation" linking to /articles/new?species_id=<id> if not
- templates/tanks/detail.html   — same pattern: "Documentation" section linking to
  the article or offering to create one via /articles/new?tank_idc=<idc>
- app.py — register articles blueprint at /articles
- base.html — add "Documentation" nav link under Reports section pointing to
  url_for('articles.list_articles') with active state when request.blueprint == 'articles'

Stack: SQLite + Python Flask + HTML/CSS/JS + Quill.js (CDN, free).
Brand everything as "Mason Aquatics".
Keep the same dark/light CSS variable theme from base.html.
Do not rewrite models.py or DATABASE_SCHEMA.md — they are complete.
Use Quill.js from CDN: https://cdn.quilljs.com/1.3.7/quill.min.js
                  CSS: https://cdn.quilljs.com/1.3.7/quill.snow.css
The Article model already exists in models.py — import it from there.
```

---

## Phase Completion Notes

### Phase 1 — Foundation & Database
- Status: ✅ Complete
- Files produced:
  - `requirements.txt`
  - `models.py` — all SQLAlchemy models
  - `app.py` — Flask skeleton
  - `routes/__init__.py`
  - `routes/main.py` — dashboard, theme toggle
  - `routes/species.py` — full species CRUD + photos
  - `templates/base.html` — dark/light theme, sidebar nav
  - `templates/dashboard.html`
  - `templates/species/list.html`
  - `templates/species/form.html`
  - `templates/species/detail.html`
- Key decisions:
  - Dates stored as ISO internally, displayed as DD/MM/YYYY
  - Stock = quantity_bought − SUM(quantity_sold) computed as a property
  - Photos stored in `static/uploads/photos/` with timestamped filenames
  - Wharf prices stored in separate `wharf_prices` table, replaced on every save
  - Theme persisted to both localStorage and DB (AppSettings row id=1)

### Phase 2 — Tank Management
- Status: ✅ Complete
- Files produced:
  - `routes/tanks.py`
  - `templates/tanks/list.html`
  - `templates/tanks/detail.html`
  - `templates/tanks/edit.html`
  - `app.py` — updated (tanks blueprint registered)
  - `templates/base.html` — updated (Tanks sidebar link live)
- Key decisions:
  - Primer formula: `(volume_litres × change%) / 200 × 5ml` (Seachem Prime dose rate)
  - Chart uses dual Y-axes: temperature (left, accent colour) and pH (right, green dashed)
  - Water params colour-coded: ammonia/nitrite >0 = warning/danger; nitrate <20 = ok
  - Equipment kWh: `(wattage × hours_per_day) / 1000` per item
  - All add/delete forms use inline collapsible panels

### Phase 3 — Breeding Records
- Status: ✅ Complete
- Files produced:
  - `routes/breeding.py`
  - `templates/breeding/list.html`
  - `templates/breeding/form.html`
  - `templates/species/detail.html` — updated (inline breeding form)
  - `app.py` — updated (breeding blueprint registered)
  - `templates/base.html` — updated (Breeding sidebar link live)
- Key decisions:
  - Inline "Add Breeding Record" form posts with `return_to=species`
  - Central breeding log at /breeding/ — filter by species, tank, date range
  - Sort options: newest first, oldest first, species A–Z, best hatch rate
  - Hatch rate colour bands: ≥70% = green, 40–69% = amber, <40% = red
  - Best tank per species calculated from per-tank peak hatch rate

### Phase 4 — Sales System
- Status: ✅ Complete
- Files produced:
  - `routes/sales.py`
  - `templates/sales/list.html`
  - `templates/sales/form.html`
  - `templates/sales/customer_list.html`
  - `templates/sales/customer_detail.html`
  - `templates/sales/customer_form.html`
  - `app.py` — updated (sales blueprint registered)
  - `templates/base.html` — updated (Sales + Customers links live)
- Key decisions:
  - Store credit auto-deducted on sale, auto-refunded on delete
  - Warn + block if insufficient credit for store-credit payment
  - Delete customer nulls sale customer_id rather than cascade-deleting sales
  - Live total preview (qty × price) calculated client-side on form
  - Stock validation on add: blocks sale if qty > current_stock

### Phase 5 — Gallery System
- Status: ✅ Complete
- Files produced:
  - `routes/gallery.py`
  - `templates/gallery/index.html`
  - `app.py` — updated (gallery blueprint registered)
  - `templates/base.html` — updated (Gallery sidebar link live)
- Key decisions:
  - Two view modes: "Grouped by Species" (default) and "All Photos" flat grid
  - Filter by species via dropdown (auto-submits form)
  - Keyboard-navigable lightbox: arrow keys prev/next, Escape to close
  - Photo upload still happens on species detail page; gallery is read-only aggregate
  - Primary photo badge shown in both gallery and species sections

### Phase 6 — QR Codes & Labels
- Status: ✅ Complete
- Files produced:
  - `routes/public.py` — public species page (no auth)
  - `routes/labels.py` — QR generator, single label PDF, batch label PDF
  - `templates/public/species.html` — standalone light-mode public page
  - `templates/labels/index.html` — label manager with batch select
  - `app.py` — updated (public + labels blueprints registered)
  - `templates/base.html` — updated (Tank Labels sidebar link live)
- Key decisions:
  - Public URL built from `request.host_url` — works on localhost and deployed
  - QR codes use ERROR_CORRECT_M, saved to `static/generated/qr_<id>.png`
  - Labels are 99×57mm (Avery L7636 compatible), one label per PDF page
  - Label layout: blue accent stripe header, photo left, names+params centre, QR right
  - Batch endpoint accepts `species_ids[]` POST list, returns multi-page PDF
  - Public page is fully standalone HTML (no base.html, no sidebar)
  - Label route function is named `generate_label` — templates must use `labels.generate_label`

### Phase 7 — Reports & Available List PDF
- Status: ✅ Complete
- Files produced:
  - `routes/reports.py` — blueprint at /reports
  - `templates/reports/available_list.html` — filter panel + live HTML preview + PDF download
  - `app.py` — updated (reports blueprint registered)
  - `templates/base.html` — updated (Available List sidebar link live)
- Key decisions:
  - Four filter modes: in-stock only (default), all species, stock ≥ threshold, selected by checkbox
  - PDF generated via ReportLab into a BytesIO buffer and streamed directly — no temp file
  - HTML preview mirrors the PDF table exactly; "Download PDF" clones current filter state
    into a hidden form via JS and POSTs to /reports/available-list/pdf
  - PDF has branded header (Mason Aquatics + date), accent HR rule, alternating row colours,
    colour-coded stock numbers (green/amber/red), page numbers in footer
  - Species picker in filter panel scrollable, supports Select All / Clear

### Phase 8 — Cost Controls
- Status: ✅ Complete
- Files produced:
  - `routes/costs.py` — blueprint at /costs (dashboard, feed log, power costs)
  - `templates/costs/dashboard.html` — cost overview with Chart.js bar charts
  - `templates/costs/feed_log.html` — feed log with inline add + live cost calculator
  - `templates/costs/power.html` — power records + equipment-based estimate + kWh bars
  - `app.py` — updated (costs blueprint registered)
  - `templates/base.html` — updated (Cost Dashboard, Feed Log, Power Costs links live)
- Key decisions:
  - Feed cost per entry calculated server-side: `(grams / 1000) × cost_per_kg`
  - Power records upsert on month_year — adding same month updates rather than duplicates
  - Monthly kWh estimate derived from TankEquipment.daily_kwh × 30 across all tanks
  - Cost per fish = (feed this month + power this month) / total fish in stock
  - Feed log filterable by month (auto-populated from existing entries) and by tank IDC
  - Dashboard shows last 6 months of feed and power as separate bar charts

### Phase 9 — Settings Page
- Status: ✅ Complete
- Files produced:
  - `routes/main.py` — updated: GET /settings + POST /settings added to main_bp
  - `templates/settings.html` — full settings page with live preview
  - `templates/base.html` — updated (Settings footer button + topbar gear icon live)
- Key decisions:
  - Theme radio cards apply change live to DOM + ping /settings/theme to keep topbar in sync
  - 8 preset accent swatches + custom <input type="color"> picker; both update --accent live
  - Four font size buttons apply font size live via document.documentElement.style.fontSize
  - All three settings (theme, accent_colour, font_size) validated server-side before saving
  - Settings footer button shows active state (blue ring + tint) when on settings page
  - Gear icon shortcut added to topbar alongside the theme toggle button
  - base.html :root now guards --accent and --font-size-base against None/missing values

### Phase 10 — Documentation Pages
- Status: ⬜ Not Started

---

## File Tree (current state after Phase 9)

```
mason_aquatics/
├── README.md
├── PHASE_PLAN.md
├── DATABASE_SCHEMA.md
├── SESSION_RESUME.md
├── requirements.txt
├── app.py                          ← Phases 1–9 all registered
├── models.py                       ← All SQLAlchemy models (complete, do not modify)
├── routes/
│   ├── __init__.py
│   ├── main.py                     ← Dashboard, theme toggle, GET+POST /settings ← UPDATED Phase 9
│   ├── species.py                  ← Species CRUD, photos, wharf prices
│   ├── tanks.py                    ← Tanks, water tests, equipment
│   ├── breeding.py                 ← Breeding CRUD
│   ├── sales.py                    ← Sales + Customer CRUD
│   ├── gallery.py                  ← Central gallery
│   ├── public.py                   ← Public species pages (no auth)
│   ├── labels.py                   ← QR codes + PDF labels
│   ├── reports.py                  ← Available list HTML preview + PDF
│   └── costs.py                    ← Feed log + Power costs + Dashboard
├── templates/
│   ├── base.html                   ← Settings link live, gear in topbar ← UPDATED Phase 9
│   ├── dashboard.html
│   ├── settings.html               ← NEW Phase 9
│   ├── species/
│   │   ├── list.html
│   │   ├── form.html
│   │   └── detail.html
│   ├── tanks/
│   │   ├── list.html
│   │   ├── detail.html
│   │   └── edit.html
│   ├── breeding/
│   │   ├── list.html
│   │   └── form.html
│   ├── sales/
│   │   ├── list.html
│   │   ├── form.html
│   │   ├── customer_list.html
│   │   ├── customer_detail.html
│   │   └── customer_form.html
│   ├── gallery/
│   │   └── index.html
│   ├── public/
│   │   └── species.html
│   ├── labels/
│   │   └── index.html
│   ├── reports/
│   │   └── available_list.html
│   └── costs/
│       ├── dashboard.html
│       ├── feed_log.html
│       └── power.html
├── static/
│   ├── uploads/photos/             ← Uploaded fish photos
│   └── generated/                  ← QR PNGs + label PDFs written here
└── instance/
    └── mason_aquatics.db
```

---

## Running the App

```bash
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

The database is created automatically on first run. All 30 tanks (T#01–T#30) and a default AppSettings row are seeded automatically.

---

## Blueprint URL Reference

| Blueprint    | Prefix       | Key routes                                                                        |
|--------------|--------------|-----------------------------------------------------------------------------------|
| `main`       | `/`          | `GET /` dashboard                                                                 |
| `main`       | `/`          | `GET /settings`, `POST /settings`                                                 |
| `main`       | `/`          | `POST /settings/theme` (quick topbar toggle)                                      |
| `species`    | `/species`   | `/`, `/add`, `/<id>`, `/<id>/edit`, `/<id>/delete`                                |
| `species`    | `/species`   | `/<id>/photos/upload`, `/photos/<id>/delete`                                      |
| `tanks`      | `/tanks`     | `/`, `/<idc>`, `/<idc>/edit`                                                      |
| `tanks`      | `/tanks`     | `/<idc>/test/add`, `/test/<id>/delete`                                            |
| `tanks`      | `/tanks`     | `/<idc>/equipment/add`, `/equipment/<id>/delete`                                  |
| `tanks`      | `/tanks`     | `/<idc>/chart-data` (JSON)                                                        |
| `breeding`   | `/breeding`  | `/`, `/add`, `/add/<species_id>`, `/<id>/edit`, `/<id>/delete`                    |
| `sales`      | `/sales`     | `/`, `/add`, `/add/<species_id>`, `/<id>/edit`, `/<id>/delete`                    |
| `sales`      | `/sales`     | `/customers`, `/customers/<id>`, `/customers/add`                                 |
| `sales`      | `/sales`     | `/customers/<id>/edit`, `/customers/<id>/delete`, `/customers/<id>/add-credit`    |
| `gallery`    | `/gallery`   | `/` (view=grouped\|all, species_id filter)                                        |
| `public`     | `/public`    | `/species/<id>` — no auth, QR-linked                                              |
| `labels`     | `/labels`    | `/`, `/qr/<id>` PNG, `/label/<id>` PDF (fn: generate_label), `/label/batch` POST |
| `reports`    | `/reports`   | `GET /available-list`, `POST /available-list/pdf`                                 |
| `costs`      | `/costs`     | `/` dashboard, `/feed`, `/feed/add`, `/feed/<id>/delete`                          |
| `costs`      | `/costs`     | `/power`, `/power/add`, `/power/<id>/delete`                                      |

---

## Known Notes

- The labels blueprint route for single-label PDF is named `generate_label` — any template
  link must use `url_for('labels.generate_label', species_id=id)`.
- The `FeedLog.feed_date` field stores ISO date strings. Templates display it directly;
  no `feed_date_display` property exists on the model — use `f.feed_date` in templates.
- `AppSettings` (id=1) holds `theme`, `accent_colour`, and `font_size` — all three are
  injected into every template via the `settings` context processor variable in app.py.
- `base.html` `:root` now uses fallback defaults for both `--accent` and `--font-size-base`
  to prevent rendering errors if AppSettings is missing or fields are null.
- The `Article` model already exists in `models.py` and is ready for Phase 10 — do not
  modify models.py. Fields: id, title, content_html, species_id, tank_idc, created_at, updated_at.

---

## Deployment Notes

| Option         | Cost      | Notes                                            |
|----------------|-----------|--------------------------------------------------|
| Local (PC/Pi)  | Free      | Best for home fish room, always on your network  |
| PythonAnywhere | Free tier | Hosts Flask apps, 512MB storage                  |
| Render.com     | Free tier | Auto-deploy from GitHub                          |
| Railway.app    | Free tier | Simple Flask deployment                          |

**Important for QR codes on deployed apps:** The QR code encodes the full URL using
`request.host_url`, so it will automatically use whatever domain the app is running on.
For local use this will be `http://localhost:5000/public/species/<id>`.
If deploying, the QR codes will encode the correct public URL automatically.
