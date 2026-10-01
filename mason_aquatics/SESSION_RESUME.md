# Mason Aquatics — Session Resume Guide

## Current state (01/10/2026)

All 10 phases are built **and verified working**. A debug/stabilisation pass on
01/10/2026 fixed every defect found by an automated end-to-end test sweep (see
"Stabilisation pass" below). `python tests/run_tests.py` exercises every route
against an isolated temp database — 262 checks, all passing.

The GitHub repo `Mason-git-nffc/Aquatics-management-project` is the source of
truth. Everything lives under `mason_aquatics/` in the organised layout
(`routes/`, `templates/<area>/`, `static/vendor/`). The old flat duplicate files
at the folder root have been removed — do not re-upload flat copies.

## How to resume in a new Claude session

Attach the project (or the repo) and say what you want next. Suggested prompt:

```
Mason Aquatics fish room app — all 10 phases complete and tested.
Repo: Mason-git-nffc/Aquatics-management-project (mason_aquatics/ folder).
Read SESSION_RESUME.md first. Run `python tests/run_tests.py` before and after
changes. Do not modify models.py. Keep UK conventions (£, DD/MM/YYYY), the
dark/light CSS variable theme from base.html, and the Mason Aquatics branding.

Next task: <describe it>
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
- Status: ✅ Complete
- Files produced:
  - `routes/articles.py` — blueprint at /articles (list, new, detail, edit, delete)
  - `templates/articles/list.html`, `form.html`, `detail.html`
  - `routes/tanks.py` + `templates/tanks/detail.html` — linked articles section
  - `templates/species/detail.html` — linked articles section
- Key decisions:
  - Quill.js rich-text editor; HTML stored in `Article.content_html`
  - Articles optionally linked to a species and/or a tank; "new" accepts
    `?species_id=` / `?tank_idc=` to pre-fill the link

### Stabilisation pass — 01/10/2026
Automated sweep (every route, real data, blank/junk input, headless Chromium for JS)
found and fixed:
- **Species add/edit page and customer add/edit page crashed (500)** — invalid Jinja
  escaping in delete-confirm `onsubmit`. All confirm/JS strings now use `| tojson`
  inside single-quoted attributes (also fixed in articles list/detail, customer detail).
- **Gallery always empty** — route passed `grouped_list`/`photos`, template expects
  `groups`/`photos_flat`/`selected_species`. `routes/gallery.py` rewritten to match.
- **Gallery lightbox + species delete button broke on names with apostrophes**
  (e.g. "Kribensis O'Neil") — JS string built by hand; now `| tojson`.
- **Deleting a species with breeding records crashed** (NOT NULL FK). Breeding records
  are now deleted with the species; sales/articles are kept and unlinked. Its QR PNG is removed.
- **Species detail crashed** if any breeding record had blank eggs laid/hatched.
- **Charts, rich-text editor and icons failed without internet** — Chart.js 4.4.1,
  Quill 1.3.7 and Font Awesome 6.5.2 are now vendored in `static/vendor/` (works offline / on the Pi).
  Google Fonts (Inter) still loads from the web and falls back to system fonts.
- **Theme chosen on the Settings page reverted** — a stale `localStorage` value overrode
  the DB. The DB is now the source of truth; localStorage just mirrors it.
- **Topbar search box did nothing** — now searches species, tanks, customers and
  articles (`GET /search?q=`, `templates/search.html`).
- Label PDF showed a missing-glyph box before the temperature and truncated 24.5 °C to 24.
- Batch label PDF could start with a blank page when an ID was missing; junk IDs in
  filters (`?species_id=abc`) no longer 500.
- `app.py`: debug mode is **off by default** (Werkzeug debugger on 0.0.0.0 = remote code
  execution for anyone on the LAN). Enable with `MASON_DEBUG=1`. Secret key from
  `MASON_SECRET_KEY`, port from `MASON_PORT`. Startup message is ASCII (Windows console safe).
  `create_app(test_config)` accepts overrides for tests.
- Added `requirements.txt`, `.gitignore`, `tests/run_tests.py`.
- `Install-MasonAquaticsNEw.ps1` now copies `routes/`, `templates/` and `static/vendor/`
  recursively (it previously used a hard-coded file list that would have missed new files).
  The old root `Install-MasonAquatics.ps1` (which installed stale flat files) was removed.

Known, deliberately not changed (models.py is frozen):
- `BreedingRecord.hatch_rate` returns `None` (shown as "—") when 0 eggs hatched, rather than 0%.
- `Model.query.get()` is SQLAlchemy-legacy and emits deprecation warnings; still works on SQLAlchemy 2.x.

---

## File Tree

```
mason_aquatics/
├── INSTALL.md                    ← Windows install guide
├── Install-MasonAquaticsNEw.ps1  ← Windows installer (safe to re-run as an upgrade)
├── SESSION_RESUME.md
├── requirements.txt
├── app.py                        ← all blueprints registered
├── models.py                     ← complete — do not modify
├── routes/
│   ├── main.py      ← dashboard, settings, theme toggle, global search
│   ├── species.py   ← species CRUD, photos, wharf prices
│   ├── tanks.py     ← tanks, water tests, equipment, chart data
│   ├── breeding.py  ← breeding CRUD + central log
│   ├── sales.py     ← sales + customers + store credit
│   ├── gallery.py   ← central gallery
│   ├── public.py    ← public species page (no auth, QR target)
│   ├── labels.py    ← QR PNG, label PDF, batch label PDF
│   ├── reports.py   ← available stock list (HTML preview + PDF)
│   ├── costs.py     ← cost dashboard, feed log, power costs
│   └── articles.py  ← documentation pages (Quill)
├── templates/
│   ├── base.html, dashboard.html, settings.html, search.html
│   ├── species/ tanks/ breeding/ sales/ gallery/ public/
│   ├── labels/ reports/ costs/ articles/
├── static/
│   ├── vendor/      ← Chart.js, Quill, Font Awesome (committed)
│   ├── uploads/photos/   (runtime, git-ignored)
│   └── generated/        (runtime, git-ignored)
├── tests/run_tests.py
└── instance/mason_aquatics.db    (runtime, git-ignored)
```

---

## Running the App

```bash
pip install -r requirements.txt
python app.py                 # http://localhost:5000
MASON_DEBUG=1 python app.py   # development only — never on a shared network
```

The database is created automatically on first run, with T#01–T#30 and the AppSettings row seeded.

## Testing

```bash
python tests/run_tests.py      # add -v for every check
```
Uses a throwaway temp DB and upload folder — safe to run on a live install.

---

## Blueprint URL Reference

| Blueprint  | Prefix      | Key routes                                                                       |
|------------|-------------|----------------------------------------------------------------------------------|
| `main`     | `/`         | `GET /` dashboard, `GET/POST /settings`, `POST /settings/theme`, `GET /search?q=` |
| `species`  | `/species`  | `/`, `/add`, `/<id>`, `/<id>/edit`, `/<id>/delete`                               |
| `species`  | `/species`  | `/<id>/photos/upload`, `/photos/<id>/delete`                                     |
| `tanks`    | `/tanks`    | `/`, `/<idc>`, `/<idc>/edit`, `/<idc>/chart-data` (JSON)                         |
| `tanks`    | `/tanks`    | `/<idc>/test/add`, `/test/<id>/delete`, `/<idc>/equipment/add`, `/equipment/<id>/delete` |
| `breeding` | `/breeding` | `/`, `/add`, `/add/<species_id>`, `/<id>/edit`, `/<id>/delete`                   |
| `sales`    | `/sales`    | `/`, `/add`, `/add/<species_id>`, `/<id>/edit`, `/<id>/delete`                   |
| `sales`    | `/sales`    | `/customers`, `/customers/add`, `/customers/<id>`, `/customers/<id>/edit`, `/customers/<id>/delete`, `/customers/<id>/add-credit` |
| `gallery`  | `/gallery`  | `/` (view=grouped\|all, species_id filter)                                       |
| `public`   | `/public`   | `/species/<id>` — no auth, QR-linked                                             |
| `labels`   | `/labels`   | `/`, `/qr/<id>` PNG, `/label/<id>` PDF (fn: generate_label), `/label/batch` POST |
| `reports`  | `/reports`  | `GET/POST /available-list`, `POST /available-list/pdf`                           |
| `costs`    | `/costs`    | `/`, `/feed`, `/feed/add`, `/feed/<id>/delete`, `/power`, `/power/add`, `/power/<id>/delete` |
| `articles` | `/articles` | `/`, `/new`, `/<id>`, `/<id>/edit`, `/<id>/delete`                               |

---

## Conventions & gotchas

- Any value interpolated into inline JS or an `onclick`/`onsubmit` attribute must use
  `{{ value | tojson }}` inside a **single-quoted** attribute. Never hand-escape quotes.
- When a route and template disagree on variable names, Jinja renders nothing silently —
  check `render_template(...)` kwargs against the template when something is blank.
- Front-end libraries are local (`static/vendor/`). Don't reintroduce CDN links.
- `FeedLog.feed_date` has no `_display` property — templates use `f.feed_date`.
- `AppSettings` (id=1) holds theme / accent_colour / font_size, injected as `settings`.

## Deployment Notes

| Option        | Notes                                                    |
|---------------|----------------------------------------------------------|
| Windows PC    | `Install-MasonAquaticsNEw.ps1` — see INSTALL.md          |
| Raspberry Pi  | systemd service on port 5000, LAN access                  |
| Cloud hosts   | PythonAnywhere / Render / Railway free tiers will run it |

QR codes encode `request.host_url`, so print labels from the address customers will
actually reach (e.g. `http://mason-aquatics.local:5000`), not `localhost`.
