from app.extensions import db


class Hotel(db.Model):
    __tablename__ = "hotels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    destination = db.Column(db.String(150), nullable=False, index=True)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    price_per_night = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, nullable=False, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    amenities = db.Column(db.JSON, nullable=False, default=list)
    sample_data = db.Column(db.Boolean, nullable=False, default=True)
