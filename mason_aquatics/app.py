"""
Mason Aquatics — Flask Application Entry Point
Run with: python app.py
"""

import os
from flask import Flask
from models import db, AppSettings

# ── Tank IDC choices T#01 – T#30 ──────────────────────────────────────────────
TANK_CHOICES = [f'T#{str(i).zfill(2)}' for i in range(1, 31)]

# ── Dropdown enums (used in templates and forms) ──────────────────────────────
PURCHASED_FROM_CHOICES = [
    'Wharf Aquatics',
    'Mansfield Aquatics',
    'MARP',
    'Private Sale',
    'Other',
]

REPRODUCTION_CHOICES = [
    'Egg Layer',
    'Egg Scatterer',
    'Livebearer',
]

PAYMENT_TYPE_CHOICES = ['Cash', 'Store Credit']

EQUIPMENT_TYPE_CHOICES = ['Heater', 'Filter', 'Light', 'Pump', 'Other']


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # ── Configuration ─────────────────────────────────────────────────────────
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SECRET_KEY'] = 'mason-aquatics-secret-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"sqlite:///{os.path.join(app.instance_path, 'mason_aquatics.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads', 'photos')
    app.config['GENERATED_FOLDER'] = os.path.join(app.root_path, 'static', 'generated')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

    # ── Init extensions ───────────────────────────────────────────────────────
    db.init_app(app)

    # ── Register blueprints ───────────────────────────────────────────────────
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    from routes.species import species_bp                          # Phase 1
    app.register_blueprint(species_bp, url_prefix='/species')

    from routes.tanks import tanks_bp                              # Phase 2
    app.register_blueprint(tanks_bp, url_prefix='/tanks')

    from routes.breeding import breeding_bp                        # Phase 3
    app.register_blueprint(breeding_bp, url_prefix='/breeding')

    from routes.sales import sales_bp                              # Phase 4
    app.register_blueprint(sales_bp, url_prefix='/sales')

    from routes.gallery import gallery_bp                          # Phase 5
    app.register_blueprint(gallery_bp, url_prefix='/gallery')

    from routes.public import public_bp                            # Phase 6
    app.register_blueprint(public_bp, url_prefix='/public')

    from routes.labels import labels_bp                            # Phase 6
    app.register_blueprint(labels_bp, url_prefix='/labels')

    from routes.reports import reports_bp                          # Phase 7
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from routes.costs import costs_bp                              # Phase 8
    app.register_blueprint(costs_bp, url_prefix='/costs')

    from routes.articles import articles_bp                        # Phase 10
    app.register_blueprint(articles_bp, url_prefix='/articles')

    # ── Inject globals into all templates ─────────────────────────────────────
    @app.context_processor
    def inject_globals():
        settings = AppSettings.query.get(1)
        return dict(
            settings=settings,
            tank_choices=TANK_CHOICES,
            purchased_from_choices=PURCHASED_FROM_CHOICES,
            reproduction_choices=REPRODUCTION_CHOICES,
        )

    return app


# ── DB initialisation helper ──────────────────────────────────────────────────
def init_db(app):
    with app.app_context():
        db.create_all()
        if not AppSettings.query.get(1):
            db.session.add(AppSettings(id=1))
            db.session.commit()
        from models import Tank
        for idc in TANK_CHOICES:
            if not Tank.query.filter_by(tank_idc=idc).first():
                db.session.add(Tank(tank_idc=idc))
        db.session.commit()
        print('✓ Database initialised successfully.')


if __name__ == '__main__':
    app = create_app()
    init_db(app)
    app.run(debug=True, host='0.0.0.0', port=5000)
