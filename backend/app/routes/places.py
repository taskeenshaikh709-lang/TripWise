from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from app.extensions import db
from app.models import Place
from app.services.place_service import seed_sample_places

places_bp = Blueprint("places", __name__)


def place_data(place):
    return {
        "id": place.id,
        "name": place.name,
        "destination": place.destination,
        "currency": place.currency,
        "category": place.category,
        "description": place.description,
        "estimated_cost": place.estimated_cost,
        "visit_duration": place.visit_duration,
        "latitude": place.latitude,
        "longitude": place.longitude,
        "rating": place.rating,
        "sample_data": place.sample_data,
    }


@places_bp.get("")
@places_bp.get("/")
def list_places():
    seed_sample_places()
    destination = request.args.get("destination", "").strip()
    query = Place.query
    if destination:
        query = query.filter(db.func.lower(Place.destination) == destination.casefold())
    places = query.order_by(Place.destination, Place.name).all()
    return jsonify(status="success", places=[place_data(place) for place in places])


@places_bp.get("/search")
def search_places():
    seed_sample_places()
    term = request.args.get("q", "").strip()
    destination = request.args.get("destination", "").strip()
    if not term and not destination:
        return jsonify(status="success", places=[])
    query = Place.query
    if destination:
        query = query.filter(db.func.lower(Place.destination) == destination.casefold())
    if term:
        phrase = f"%{term[:100]}%"
        query = query.filter(or_(Place.name.ilike(phrase), Place.destination.ilike(phrase)))
    return jsonify(status="success", places=[place_data(place) for place in query.limit(50).all()])
