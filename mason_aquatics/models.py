"""
Mason Aquatics — SQLAlchemy Models
All tables for the fish room management system.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ── App Settings ──────────────────────────────────────────────────────────────

class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    id            = db.Column(db.Integer, primary_key=True)
    theme         = db.Column(db.String(10),  default='dark')
    accent_colour = db.Column(db.String(20),  default='#2196F3')
    font_size     = db.Column(db.String(5),   default='md')


# ── Species ───────────────────────────────────────────────────────────────────

class Species(db.Model):
    __tablename__ = 'species'

    id                   = db.Column(db.Integer,  primary_key=True)
    common_name          = db.Column(db.String(120), nullable=False)
    scientific_name      = db.Column(db.String(120))
    native_to            = db.Column(db.String(120))
    weather_link         = db.Column(db.String(500))
    tank_idc             = db.Column(db.String(10))
    min_temp_c           = db.Column(db.Float)
    max_temp_c           = db.Column(db.Float)
    ideal_ph             = db.Column(db.Float)
    reproduction_type    = db.Column(db.String(60))
    purchased_from       = db.Column(db.String(120))
    purchased_from_notes = db.Column(db.String(300))
    date_purchased       = db.Column(db.String(10))   # ISO date string
    price_per_fish_gbp   = db.Column(db.Float)
    quantity_bought      = db.Column(db.Integer, default=0)
    display_photo        = db.Column(db.String(300))  # filename only

    # Relationships
    photos           = db.relationship('Photo',          backref='species',
                                        lazy=True, cascade='all, delete-orphan')
    wharf_prices     = db.relationship('WharfPrice',     backref='species',
                                        lazy=True, cascade='all, delete-orphan')
    breeding_records = db.relationship('BreedingRecord', backref='species', lazy=True)
    sales            = db.relationship('Sales',          backref='species', lazy=True)
    articles         = db.relationship('Article',        backref='species', lazy=True,
                                        foreign_keys='Article.species_id')

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def current_stock(self):
        sold = sum(s.quantity_sold or 0 for s in self.sales)
        return max(0, (self.quantity_bought or 0) - sold)

    @property
    def date_purchased_display(self):
        if not self.date_purchased:
            return ''
        try:
            return datetime.fromisoformat(self.date_purchased).strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return self.date_purchased or ''


class WharfPrice(db.Model):
    """Tiered wharf sale prices per species (e.g. 1 for £3, 6 for £15)."""
    __tablename__ = 'wharf_prices'

    id         = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False, default=1)
    price_gbp  = db.Column(db.Float,   nullable=False)
    notes      = db.Column(db.String(300))


class Photo(db.Model):
    """Photo attached to a species."""
    __tablename__ = 'photos'

    id          = db.Column(db.Integer, primary_key=True)
    species_id  = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    filename    = db.Column(db.String(300), nullable=False)
    caption     = db.Column(db.String(300))
    is_primary  = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.String(10))  # ISO date string


# ── Tanks ─────────────────────────────────────────────────────────────────────

class Tank(db.Model):
    __tablename__ = 'tanks'

    tank_idc      = db.Column(db.String(10), primary_key=True)
    volume_litres = db.Column(db.Float)
    location      = db.Column(db.String(200))
    notes         = db.Column(db.Text)

    @property
    def latest_test(self):
        return (TankTest.query
                .filter_by(tank_idc=self.tank_idc)
                .order_by(TankTest.test_date.desc())
                .first())

    @property
    def primer_amount_ml(self):
        """Seachem Prime dose for a 25% water change."""
        if not self.volume_litres:
            return None
        change_litres = self.volume_litres * 0.25
        return round((change_litres / 200) * 5, 1)


class TankTest(db.Model):
    """Water test reading for a tank."""
    __tablename__ = 'tank_tests'

    id            = db.Column(db.Integer, primary_key=True)
    tank_idc      = db.Column(db.String(10), db.ForeignKey('tanks.tank_idc'))
    test_date     = db.Column(db.String(10))   # ISO date string
    temperature_c = db.Column(db.Float)
    ph            = db.Column(db.Float)
    ammonia_ppm   = db.Column(db.Float)
    nitrite_ppm   = db.Column(db.Float)
    nitrate_ppm   = db.Column(db.Float)
    gh            = db.Column(db.Float)
    kh            = db.Column(db.Float)
    notes         = db.Column(db.Text)
    recorded_by   = db.Column(db.String(100))

    @property
    def test_date_display(self):
        if not self.test_date:
            return ''
        try:
            return datetime.fromisoformat(self.test_date).strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return self.test_date or ''


class TankEquipment(db.Model):
    """Equipment item registered to a tank (heater, filter, etc.)."""
    __tablename__ = 'tank_equipment'

    id             = db.Column(db.Integer, primary_key=True)
    tank_idc       = db.Column(db.String(10), db.ForeignKey('tanks.tank_idc'))
    equipment_type = db.Column(db.String(50))
    brand          = db.Column(db.String(100))
    model          = db.Column(db.String(100))
    wattage        = db.Column(db.Float)
    hours_per_day  = db.Column(db.Float, default=24.0)
    notes          = db.Column(db.Text)

    @property
    def daily_kwh(self):
        if self.wattage and self.hours_per_day:
            return round((self.wattage * self.hours_per_day) / 1000, 6)
        return 0.0


# ── Breeding ──────────────────────────────────────────────────────────────────

class BreedingRecord(db.Model):
    __tablename__ = 'breeding_records'

    id           = db.Column(db.Integer, primary_key=True)
    species_id   = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    record_date  = db.Column(db.String(10))   # ISO date string
    eggs_laid    = db.Column(db.Integer)
    eggs_hatched = db.Column(db.Integer)
    tank_idc     = db.Column(db.String(10))
    notes        = db.Column(db.Text)

    @property
    def hatch_rate(self):
        if self.eggs_laid and self.eggs_hatched and self.eggs_laid > 0:
            return round((self.eggs_hatched / self.eggs_laid) * 100, 1)
        return None

    @property
    def record_date_display(self):
        if not self.record_date:
            return ''
        try:
            return datetime.fromisoformat(self.record_date).strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return self.record_date or ''


# ── Sales & Customers ─────────────────────────────────────────────────────────

class Customer(db.Model):
    __tablename__ = 'customers'

    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(150), nullable=False)
    phone            = db.Column(db.String(30))
    email            = db.Column(db.String(200))
    store_credit_gbp = db.Column(db.Float, default=0.0)
    notes            = db.Column(db.Text)
    sales            = db.relationship('Sales', backref='customer', lazy=True)


class Sales(db.Model):
    __tablename__ = 'sales'

    id                 = db.Column(db.Integer, primary_key=True)
    species_id         = db.Column(db.Integer, db.ForeignKey('species.id'),  nullable=True)
    customer_id        = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    sale_date          = db.Column(db.String(10))  # ISO date string
    quantity_sold      = db.Column(db.Integer, nullable=False)
    price_per_fish_gbp = db.Column(db.Float,   nullable=False)
    payment_type       = db.Column(db.String(20))  # 'Cash' | 'Store Credit'
    notes              = db.Column(db.Text)

    @property
    def total_gbp(self):
        if self.quantity_sold is not None and self.price_per_fish_gbp is not None:
            return round(self.quantity_sold * self.price_per_fish_gbp, 2)
        return 0.0

    @property
    def sale_date_display(self):
        if not self.sale_date:
            return ''
        try:
            return datetime.fromisoformat(self.sale_date).strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return self.sale_date or ''


# ── Cost Controls ─────────────────────────────────────────────────────────────

class FeedLog(db.Model):
    __tablename__ = 'feed_logs'

    id              = db.Column(db.Integer, primary_key=True)
    feed_date       = db.Column(db.String(10))   # ISO date string
    brand           = db.Column(db.String(100))
    feed_type       = db.Column(db.String(100))
    amount_grams    = db.Column(db.Float)
    cost_per_kg_gbp = db.Column(db.Float)
    cost_this_entry = db.Column(db.Float)
    tank_idc        = db.Column(db.String(10))
    notes           = db.Column(db.Text)


class PowerCost(db.Model):
    __tablename__ = 'power_costs'

    id                 = db.Column(db.Integer, primary_key=True)
    month_year         = db.Column(db.String(7))   # YYYY-MM
    tariff_per_kwh_gbp = db.Column(db.Float)
    total_kwh          = db.Column(db.Float)
    total_cost_gbp     = db.Column(db.Float)
    notes              = db.Column(db.Text)


# ── Documentation Articles ────────────────────────────────────────────────────

class Article(db.Model):
    __tablename__ = 'articles'

    id           = db.Column(db.Integer,  primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    content_html = db.Column(db.Text)
    species_id   = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=True)
    tank_idc     = db.Column(db.String(10))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)
