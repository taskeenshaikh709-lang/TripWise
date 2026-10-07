from app.extensions import db


class Place(db.Model):
    __tablename__ = "places"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    destination = db.Column(db.String(150), nullable=False, index=True)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    estimated_cost = db.Column(db.Float, nullable=False, default=0)
    visit_duration = db.Column(db.Integer, nullable=False, default=90)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    rating = db.Column(db.Float, nullable=False, default=0)
    sample_data = db.Column(db.Boolean, nullable=False, default=False)

    itinerary_items = db.relationship("ItineraryItem", back_populates="place")
