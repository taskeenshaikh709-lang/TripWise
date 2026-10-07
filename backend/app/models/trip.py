from datetime import datetime

from app.extensions import db


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination = db.Column(db.String(150), nullable=False)
    start_location = db.Column(db.String(150))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Integer, nullable=False, default=1)
    travelers = db.Column(db.Integer, nullable=False, default=1)
    budget = db.Column(db.Float, nullable=False, default=0)
    total_budget = db.Column(db.Float, nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default="INR")
    travel_style = db.Column(db.String(50), nullable=False, default="balanced")
    transport_preference = db.Column(db.String(50), nullable=False, default="public transport")
    accommodation_preference = db.Column(db.String(50), nullable=False, default="hotel")
    interests = db.Column(db.JSON, nullable=False, default=list)
    selected_hotel_id = db.Column(db.Integer, db.ForeignKey("hotels.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="trips")
    days_plan = db.relationship("ItineraryDay", back_populates="trip", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    budget_plan = db.relationship("Budget", back_populates="trip", uselist=False, cascade="all, delete-orphan")
    selected_hotel = db.relationship("Hotel", foreign_keys=[selected_hotel_id])

    def __repr__(self):
        return f"<Trip {self.destination}>"