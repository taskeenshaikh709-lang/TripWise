from app.extensions import db


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id"), nullable=False, unique=True)
    accommodation = db.Column(db.Float, nullable=False, default=0)
    transport = db.Column(db.Float, nullable=False, default=0)
    food = db.Column(db.Float, nullable=False, default=0)
    activities = db.Column(db.Float, nullable=False, default=0)
    shopping = db.Column(db.Float, nullable=False, default=0)
    emergency = db.Column(db.Float, nullable=False, default=0)
    total_estimated = db.Column(db.Float, nullable=False, default=0)
    actual_total = db.Column(db.Float, nullable=False, default=0)
    remaining = db.Column(db.Float, nullable=False, default=0)

    trip = db.relationship("Trip", back_populates="budget_plan")
