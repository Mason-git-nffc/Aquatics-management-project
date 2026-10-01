"""
Mason Aquatics — end-to-end regression tests.

Runs every route against an ISOLATED temporary database and upload folder,
so it never touches your real data in instance/ or static/uploads/.

    cd mason_aquatics
    python tests/run_tests.py

Exit code 0 = all passed.
"""
import sys, os, io, tempfile, shutil, warnings, traceback
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from app import create_app, init_db
from models import db, Species, Sales, Customer, BreedingRecord, Photo, TankTest, TankEquipment, FeedLog, PowerCost, Article, AppSettings
from PIL import Image

TMP = tempfile.mkdtemp(prefix='mason_test_')
app = create_app({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(TMP, 'test.db'),
    'UPLOAD_FOLDER': os.path.join(TMP, 'photos'),
    'GENERATED_FOLDER': os.path.join(TMP, 'generated'),
})
import contextlib
with contextlib.redirect_stdout(io.StringIO()):
    init_db(app)
c = app.test_client()
VERBOSE = '-v' in sys.argv
fails = []
passes = 0

def check(method, url, expect_status=None, **kw):
    global passes
    try:
        resp = getattr(c, method)(url, **kw)
        ok = (resp.status_code == expect_status) if expect_status else resp.status_code < 400
        if ok:
            passes += 1
            if VERBOSE: print('OK  ', resp.status_code, method.upper(), url)
        else:
            print('FAIL', resp.status_code, method.upper(), url)
            fails.append((url, resp.status_code))
        return resp
    except Exception as e:
        tb = traceback.format_exc().strip().splitlines()
        print('EXC ', method.upper(), url, '\n     ' + '\n     '.join(tb[-6:]))
        fails.append((url, repr(e)[:200]))

def expect(cond, msg):
    global passes
    if cond:
        passes += 1
        if VERBOSE: print('PASS', msg)
    else:
        print('FAIL', msg); fails.append(('assert', msg))

def png_bytes(color=(30, 120, 200)):
    b = io.BytesIO(); Image.new('RGB', (400, 300), color).save(b, 'PNG'); b.seek(0); return b

# ── 1. Every page renders on an empty database ───────────────────────────────
for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'GET' in r.methods and not r.arguments and not r.rule.startswith('/static'):
        check('get', r.rule)

# ── 2. Full functional walk-through with real data ───────────────────────────
# ── Species ──
check('post', '/species/add', data={
    'common_name': "Kribensis O'Neil", 'scientific_name': 'Pelvicachromis pulcher',
    'native_to': 'Nigeria', 'weather_link': 'https://example.com', 'tank_idc': 'T#01',
    'min_temp_c': '24', 'max_temp_c': '27', 'ideal_ph': '6.8', 'reproduction_type': 'Egg Layer',
    'purchased_from': 'Wharf Aquatics', 'date_purchased': '2026-09-01',
    'price_per_fish_gbp': '4.50', 'quantity_bought': '20',
    'wp_quantity': ['1', '6'], 'wp_price': ['3.00', '15.00'], 'wp_notes': ['', 'six pack']})
check('post', '/species/add', data={'common_name': 'Guppy', 'scientific_name': 'Poecilia reticulata',
    'quantity_bought': '50', 'reproduction_type': 'Livebearer', 'tank_idc': 'T#02', 'date_purchased': '01/09/2026'})
check('post', '/species/add', data={'common_name': 'Zero Stock Tetra', 'quantity_bought': '0'})
check('post', '/species/add', data={'common_name': ''})  # validation
with app.app_context():
    sp = Species.query.filter_by(common_name="Kribensis O'Neil").first()
    expect(sp is not None and len(sp.wharf_prices) == 2, 'species created with 2 wharf tiers')
    expect(Species.query.filter_by(common_name='Guppy').first().date_purchased == '2026-09-01', 'DD/MM/YYYY date parsed to ISO')
    sid = sp.id
    gid = Species.query.filter_by(common_name='Guppy').first().id
    zid = Species.query.filter_by(common_name='Zero Stock Tetra').first().id

check('get', f'/species/{sid}')
check('get', f'/species/{sid}/edit')
check('post', f'/species/{sid}/edit', data={'common_name': "Kribensis O'Neil", 'scientific_name': 'Pelvicachromis pulcher',
    'quantity_bought': '20', 'tank_idc': 'T#01', 'wp_quantity': ['1', '6', '12'], 'wp_price': ['3', '15', '25'], 'wp_notes': ['', '', '']})
with app.app_context():
    expect(len(db.session.get(Species, sid).wharf_prices) == 3, 'wharf tiers replaced on edit')
for q in ['?q=krib', '?sort=stock', '?sort=name', '?tank_idc=T%2301', '?reproduction_type=Livebearer']:
    check('get', '/species/' + q)

# photos
check('post', f'/species/{sid}/photos/upload', data={'photo': (png_bytes(), 'fish.png'), 'caption': 'Pair', 'make_primary': '1'},
      content_type='multipart/form-data')
check('post', f'/species/{sid}/photos/upload', data={'photo': (png_bytes((200, 50, 50)), 'fish2.jpg')}, content_type='multipart/form-data')
check('post', f'/species/{sid}/photos/upload', data={'photo': (io.BytesIO(b'x'), 'bad.exe')}, content_type='multipart/form-data')
with app.app_context():
    photos = Photo.query.filter_by(species_id=sid).all()
    expect(len(photos) == 2, 'two photos uploaded')
    expect(db.session.get(Species, sid).display_photo is not None, 'display photo set')
    pid2 = [p for p in photos if not p.is_primary][0].id if photos else None

# ── Tanks ──
check('get', '/tanks/T%2301')
check('get', '/tanks/T%2301/edit')
check('post', '/tanks/T%2301/edit', data={'volume_litres': '120', 'location': 'Rack A', 'notes': 'Planted'})
check('post', '/tanks/T%2301/test/add', data={'test_date': '2026-09-20', 'temperature_c': '25.5', 'ph': '6.9',
    'ammonia_ppm': '0', 'nitrite_ppm': '0.25', 'nitrate_ppm': '15', 'gh': '6', 'kh': '4', 'recorded_by': 'Mason'})
check('post', '/tanks/T%2301/test/add', data={'test_date': '25/09/2026', 'temperature_c': '26', 'ph': '7.0'})
check('post', '/tanks/T%2301/equipment/add', data={'equipment_type': 'Heater', 'brand': 'Eheim', 'model': 'Jager',
    'wattage': '150', 'hours_per_day': '12'})
check('post', '/tanks/T%2301/equipment/add', data={'equipment_type': 'Filter', 'wattage': '10', 'hours_per_day': '24'})
r = check('get', '/tanks/T%2301/chart-data')
if r is not None: expect(r.is_json and len(r.get_json().get('labels', r.get_json())) >= 1, 'chart data JSON returned')
check('get', '/tanks/T%2301')
check('get', '/tanks/')
check('get', '/tanks/T%2399', expect_status=404)
with app.app_context():
    tid = TankTest.query.first().id; eid = TankEquipment.query.first().id

# ── Breeding ──
check('post', '/breeding/add', data={'species_id': sid, 'record_date': '2026-09-10', 'eggs_laid': '100', 'eggs_hatched': '80', 'tank_idc': 'T#01'})
check('post', f'/breeding/add/{sid}', data={'species_id': sid, 'record_date': '2026-09-15', 'eggs_laid': '50', 'eggs_hatched': '10',
    'tank_idc': 'T#03', 'return_to': 'species'})
check('post', '/breeding/add', data={'species_id': gid, 'eggs_laid': '0'})
check('get', f'/breeding/add/{sid}')
with app.app_context():
    brid = BreedingRecord.query.first().id
check('get', f'/breeding/{brid}/edit')
check('post', f'/breeding/{brid}/edit', data={'species_id': sid, 'record_date': '2026-09-11', 'eggs_laid': '100', 'eggs_hatched': '75', 'tank_idc': 'T#01'})
for q in ['', f'?species_id={sid}', '?tank_idc=T%2301', '?date_from=2026-09-01&date_to=2026-09-30', '?sort=hatch', '?sort=species', '?sort=date_asc']:
    check('get', '/breeding/' + q)
check('get', f'/species/{sid}')

# ── Customers & Sales ──
check('get', '/sales/customers/add')
check('post', '/sales/customers/add', data={'name': "Dave O'Brien", 'phone': '0123', 'email': 'd@x.com', 'store_credit_gbp': '10'})
with app.app_context():
    cid = Customer.query.first().id
check('get', f'/sales/customers/{cid}')
check('get', f'/sales/customers/{cid}/edit')
check('post', f'/sales/customers/{cid}/edit', data={'name': "Dave O'Brien", 'store_credit_gbp': '10', 'notes': 'regular'})
check('post', f'/sales/customers/{cid}/add-credit', data={'amount': '5'})
with app.app_context():
    expect(abs(db.session.get(Customer, cid).store_credit_gbp - 15) < 0.01, 'store credit added (15)')
check('post', '/sales/add', data={'species_id': sid, 'customer_id': cid, 'sale_date': '2026-09-21', 'quantity_sold': '2',
    'price_per_fish_gbp': '3', 'payment_type': 'Store Credit'})
with app.app_context():
    expect(abs(db.session.get(Customer, cid).store_credit_gbp - 9) < 0.01, 'store credit deducted (9)')
    expect(db.session.get(Species, sid).current_stock == 18, 'stock reduced to 18')
check('post', '/sales/add', data={'species_id': sid, 'customer_id': cid, 'quantity_sold': '5', 'price_per_fish_gbp': '3', 'payment_type': 'Store Credit'})
check('post', '/sales/add', data={'species_id': sid, 'quantity_sold': '999', 'price_per_fish_gbp': '3', 'payment_type': 'Cash'})
with app.app_context():
    expect(Sales.query.count() == 1, 'insufficient credit / overstock sales blocked')
check('post', f'/sales/add/{gid}', data={'species_id': gid, 'quantity_sold': '10', 'price_per_fish_gbp': '1.5', 'payment_type': 'Cash', 'sale_date': '2026-09-22'})
check('get', f'/sales/add/{gid}')
with app.app_context():
    saleid = Sales.query.filter_by(species_id=gid).first().id
    credit_sale = Sales.query.filter_by(species_id=sid).first().id
check('get', f'/sales/{saleid}/edit')
check('post', f'/sales/{saleid}/edit', data={'species_id': gid, 'quantity_sold': '8', 'price_per_fish_gbp': '1.5', 'payment_type': 'Cash', 'sale_date': '2026-09-22'})
for q in ['', f'?species_id={sid}', f'?customer_id={cid}', '?payment_type=Cash', '?date_from=2026-09-01&date_to=2026-09-30']:
    check('get', '/sales/' + q)
check('get', '/sales/customers')
check('get', f'/sales/customers/{cid}')

# ── Costs ──
check('post', '/costs/feed/add', data={'feed_date': '2026-09-05', 'brand': 'NLS', 'feed_type': 'Pellet', 'amount_grams': '250',
    'cost_per_kg_gbp': '40', 'tank_idc': 'T#01'})
check('post', '/costs/feed/add', data={'feed_date': '2026-09-06', 'brand': 'Hikari', 'amount_grams': '100', 'cost_per_kg_gbp': '30'})
with app.app_context():
    expect(abs((FeedLog.query.first().cost_this_entry or 0) - 10) < 0.01, 'feed cost computed (£10)')
    fid = FeedLog.query.first().id
check('post', '/costs/power/add', data={'month_year': '2026-09', 'tariff_per_kwh_gbp': '0.27', 'total_kwh': '120'})
check('post', '/costs/power/add', data={'month_year': '2026-09', 'tariff_per_kwh_gbp': '0.25', 'total_kwh': '100'})  # upsert
with app.app_context():
    expect(PowerCost.query.count() == 1, 'power month upserted')
    pcid = PowerCost.query.first().id
for u in ['/costs/', '/costs/feed', '/costs/feed?month=2026-09', '/costs/feed?tank_idc=T%2301', '/costs/power']:
    check('get', u)

# ── Articles ──
check('get', f'/articles/new?species_id={sid}')
check('get', '/articles/new?tank_idc=T%2301')
check('post', '/articles/new', data={'title': "Kribs' breeding guide", 'content_html': '<p><b>Hello</b></p>', 'species_id': sid, 'tank_idc': 'T#01'})
check('post', '/articles/new', data={'title': ''})
with app.app_context():
    aid = Article.query.first().id
check('get', f'/articles/{aid}')
check('get', f'/articles/{aid}/edit')
check('post', f'/articles/{aid}/edit', data={'title': 'Kribs guide v2', 'content_html': '<p>Updated</p>', 'species_id': sid})
check('get', '/articles/')
check('get', '/articles/?q=krib')
check('get', f'/species/{sid}')
check('get', '/tanks/T%2301')

# ── Gallery / public / labels ──
for u in ['/gallery/', '/gallery/?view=all', f'/gallery/?species_id={sid}', f'/public/species/{sid}', f'/public/species/{zid}', '/labels/']:
    check('get', u)
r = check('get', f'/labels/qr/{sid}');   expect(r is not None and r.data[:4] == b'\x89PNG', 'QR is PNG')
r = check('get', f'/labels/label/{sid}'); expect(r is not None and r.data[:4] == b'%PDF', 'label is PDF')
r = check('get', f'/labels/label/{zid}'); expect(r is not None and r.data[:4] == b'%PDF', 'label (no photo) is PDF')
r = check('post', '/labels/label/batch', data={'species_ids': [sid, gid, zid]}); expect(r is not None and r.data[:4] == b'%PDF', 'batch label PDF')
check('post', '/labels/label/batch', data={})
check('get', '/public/species/9999', expect_status=404)

# ── Reports ──
for data in [{}, {'filter_mode': 'all'}, {'filter_mode': 'threshold', 'threshold': '15'}, {'filter_mode': 'selected', 'species_ids': [sid, zid]}]:
    check('post', '/reports/available-list', data=data)
    r = check('post', '/reports/available-list/pdf', data=data)
    expect(r is not None and r.data[:4] == b'%PDF', f'available list PDF {data}')
r = check('get', '/reports/available-list')
expect(r is not None and b'Kribensis' in r.data and b'Zero Stock' not in r.data.split(b'<tbody')[-1] if r else False, 'default preview hides zero stock')

# ── Settings / theme / dashboard ──
check('post', '/settings', data={'theme': 'light', 'accent_colour': '#ff5722', 'font_size': 'lg'})
with app.app_context():
    s = db.session.get(AppSettings, 1); expect(s.theme == 'light' and s.accent_colour == '#ff5722' and s.font_size == 'lg', 'settings saved')
check('post', '/settings/theme', json={'theme': 'dark'})
check('post', '/settings/theme', data={'theme': 'dark'})
check('get', '/settings')
check('get', '/')

# ── Deletes ──
check('post', f'/sales/{credit_sale}/delete')
with app.app_context():
    expect(abs(db.session.get(Customer, cid).store_credit_gbp - 15) < 0.01, 'store credit refunded on sale delete')
check('post', f'/breeding/{brid}/delete', data={'return_to': 'species'})
check('post', f'/tanks/test/{tid}/delete')
check('post', f'/tanks/equipment/{eid}/delete')
check('post', f'/costs/feed/{fid}/delete')
check('post', f'/costs/power/{pcid}/delete')
if pid2: check('post', f'/species/photos/{pid2}/delete')
check('post', f'/species/{gid}/delete')
check('post', f'/species/{sid}/delete')
with app.app_context():
    expect(db.session.get(Species, sid) is None, 'species deleted')
    expect(Sales.query.count() >= 1, 'sales history kept after species delete')
for u in ['/', '/sales/', f'/sales/customers/{cid}', f'/sales/{saleid}/edit', '/articles/', f'/articles/{aid}', f'/articles/{aid}/edit', '/breeding/', '/reports/available-list', '/gallery/']:
    check('get', u)
check('post', f'/articles/{aid}/delete')
check('post', f'/sales/customers/{cid}/delete')

# final sweep on remaining data
for rr in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'GET' in rr.methods and not rr.arguments and not rr.rule.startswith('/static'):
        check('get', rr.rule)


# ── 3. Edge cases: blank / junk input everywhere, then re-render every page ──
def hit(m, u, **kw):
    global passes
    try:
        r = getattr(c, m)(u, **kw)
        if r.status_code >= 400 and r.status_code != 404:
            print('FAIL', r.status_code, m.upper(), u); fails.append((u, r.status_code))
        else:
            passes += 1
        return r
    except Exception as e:
        print('EXC ', m.upper(), u, repr(e)[:250]); fails.append((u, repr(e)[:250]))

with app.app_context():
    for s in Species.query.all(): db.session.delete(s)
    db.session.commit()
hit('post', '/species/add', data={'common_name': 'Bare'})
hit('post', '/species/add', data={'common_name': 'Junk', 'min_temp_c': 'abc', 'quantity_bought': '-5', 'date_purchased': 'nonsense',
    'wp_quantity': ['x', '2'], 'wp_price': ['1', ''], 'ideal_ph': '7,2'})
hit('post', '/tanks/T%2305/test/add', data={})
hit('post', '/tanks/T%2305/test/add', data={'test_date': 'garbage', 'ph': 'x'})
hit('post', '/tanks/T%2305/equipment/add', data={})
hit('post', '/tanks/T%2305/edit', data={'volume_litres': 'abc'})
hit('post', '/breeding/add', data={'species_id': '1'})
hit('post', '/breeding/add', data={'species_id': '1', 'eggs_laid': '10', 'eggs_hatched': '0', 'tank_idc': 'T#05'})
hit('post', '/breeding/add', data={'species_id': '1', 'eggs_laid': '0', 'eggs_hatched': '5'})
hit('post', '/breeding/add', data={})
hit('post', '/sales/add', data={'species_id': '1'})
hit('post', '/sales/add', data={})
hit('post', '/sales/customers/add', data={'name': 'C', 'store_credit_gbp': 'abc'})
hit('post', '/sales/customers/1/add-credit', data={'amount': ''})
hit('post', '/sales/customers/1/add-credit', data={'amount': '-50'})
hit('post', '/costs/feed/add', data={})
hit('post', '/costs/power/add', data={})
hit('post', '/costs/power/add', data={'month_year': '2026-13'})
hit('post', '/costs/power/add', data={'month_year': '2026-08'})
hit('post', '/articles/new', data={'title': 'T', 'species_id': '999', 'tank_idc': 'T#77'})
hit('post', '/settings', data={'accent_colour': '#zzzzzz', 'font_size': 'huge', 'theme': 'blue'})
hit('post', '/settings/theme', data='not json', content_type='application/json')
hit('post', '/labels/label/batch', data={'species_ids': ['abc', '999']})
hit('post', '/reports/available-list/pdf', data={'filter_mode': 'threshold', 'threshold': 'abc'})
hit('post', '/reports/available-list/pdf', data={'filter_mode': 'selected'})
hit('post', '/reports/available-list', data={'filter_mode': 'selected', 'species_ids': ['abc']})
hit('get', '/reports/available-list?filter_mode=threshold&threshold=abc')
hit('get', '/breeding/?species_id=abc&date_from=bad&sort=zzz')
hit('get', '/sales/?species_id=abc&customer_id=x&date_from=bad')
hit('get', '/costs/feed?month=bad&tank_idc=T%2399')
hit('get', '/species/?sort=zzz&q=%27')
hit('get', '/articles/?q=%27&species_id=abc')

pages = [r.rule for r in app.url_map.iter_rules() if 'GET' in r.methods and not r.arguments and not r.rule.startswith('/static')]
pages += ['/species/1', '/species/2', '/species/1/edit', '/species/2/edit', '/tanks/T%2305', '/tanks/T%2305/edit', '/tanks/T%2305/chart-data',
          '/breeding/1/edit', '/sales/customers/1', '/sales/customers/1/edit', '/public/species/1', '/public/species/2',
          '/labels/qr/1', '/labels/label/1', '/labels/label/2', '/articles/1', '/articles/1/edit', '/gallery/?view=all']
for u in pages: hit('get', u)



shutil.rmtree(TMP, ignore_errors=True)
print(f'\n{passes} checks passed, {len(fails)} failed')
for f in fails: print('   ', f)
sys.exit(1 if fails else 0)
