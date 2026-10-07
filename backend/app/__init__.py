from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=[Config.FRONTEND_URL])

    db.init_app(app)
    jwt.init_app(app)

    from .routes.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/api")
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    from .routes.trips import trips_bp
    app.register_blueprint(trips_bp, url_prefix="/api/trips")
    from .routes.places import places_bp
    app.register_blueprint(places_bp, url_prefix="/api/places")

    from .models import Budget, Expense, Hotel, ItineraryDay, ItineraryItem, Place, Trip, User

    with app.app_context():
        _upgrade_legacy_schema()
        db.create_all()

    return app


def _upgrade_legacy_schema():
    """Add new nullable/defaulted columns without discarding existing SQLite data."""
    from sqlalchemy import inspect, text

    additions = {
        "users": {
            "password_hash": "VARCHAR(255)",
            "role": "VARCHAR(30) NOT NULL DEFAULT 'traveler'",
        },
        "trips": {
            "start_location": "VARCHAR(150)",
            "end_date": "DATE",
            "travelers": "INTEGER NOT NULL DEFAULT 1",
            "total_budget": "FLOAT NOT NULL DEFAULT 0",
            "currency": "VARCHAR(3) NOT NULL DEFAULT 'INR'",
            "transport_preference": "VARCHAR(50) NOT NULL DEFAULT 'public transport'",
            "accommodation_preference": "VARCHAR(50) NOT NULL DEFAULT 'hotel'",
            "interests": "JSON",
            "updated_at": "DATETIME",
            "selected_hotel_id": "INTEGER",
        },
        "hotels": {"currency": "VARCHAR(3) NOT NULL DEFAULT 'INR'"},
        "places": {"currency": "VARCHAR(3) NOT NULL DEFAULT 'INR'"},
    }
    inspector = inspect(db.engine)
    for table, columns in additions.items():
        if not inspector.has_table(table):
            continue
        existing = {column["name"] for column in inspector.get_columns(table)}
        for name, definition in columns.items():
            if name not in existing:
                db.session.execute(
                    text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}')
                )
    db.session.commit()

    if inspector.has_table("users"):
        db.session.execute(
            text(
                "UPDATE users SET password_hash = password "
                "WHERE password_hash IS NULL AND password IS NOT NULL"
            )
        )
        db.session.commit()