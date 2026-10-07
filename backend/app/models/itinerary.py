from app.extensions import db


class ItineraryDay(db.Model):
    __tablename__ = "itinerary_days"
    __table_args__ = (db.UniqueConstraint("trip_id", "day_number"),)

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, index=True)
    day_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)

    trip = db.relationship("Trip", back_populates="days_plan")
    items = db.relationship(
        "ItineraryItem",
        back_populates="itinerary_day",
        cascade="all, delete-orphan",
        order_by="ItineraryItem.order_index",
    )


class ItineraryItem(db.Model):
    __tablename__ = "itinerary_items"

    id = db.Column(db.Integer, primary_key=True)
    itinerary_day_id = db.Column(
        db.Integer, db.ForeignKey("itinerary_days.id"), nullable=False, index=True
    )
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    travel_time = db.Column(db.Integer, nullable=False, default=0)
    distance = db.Column(db.Float, nullable=False, default=0)
    estimated_cost = db.Column(db.Float, nullable=False, default=0)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.String(500), nullable=False, default="")

    itinerary_day = db.relationship("ItineraryDay", back_populates="items")
    place = db.relationship("Place", back_populates="itinerary_items")
