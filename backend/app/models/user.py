from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(30), nullable=False, default="traveler")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trips = db.relationship("Trip", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        hashed = generate_password_hash(password)
        self.password_hash = hashed
        self.password = hashed

    def check_password(self, password):
        hashed = self.password_hash or self.password
        return bool(hashed and check_password_hash(hashed, password))

    def __repr__(self):
        return f"<User {self.email}>"