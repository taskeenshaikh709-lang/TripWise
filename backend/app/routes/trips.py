from datetime import date, datetime
from io import BytesIO
from math import isfinite

from flask import Blueprint, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.extensions import db
from app.models import Expense, Hotel, Place, Trip
from app.services.budget_service import calculate_budget
from app.services.hotel_service import seed_sample_hotels
from app.services.itinerary_service import generate_itinerary
from app.services.place_service import recommend_places, seed_sample_places

trips_bp = Blueprint("trips", __name__)
EXPENSE_CATEGORIES = {"food", "transport", "hotel", "activities", "shopping", "other"}


def _current_user_id():
    return int(get_jwt_identity())


def _owned_trip(trip_id):
    trip = Trip.query.filter_by(id=trip_id, user_id=_current_user_id()).first()
    if trip is None:
        return None, (jsonify(status="error", message="Trip not found."), 404)
    return trip, None


def _trip_data(trip, include_itinerary=False):
    data = {
        "id": trip.id,
        "destination": trip.destination,
        "start_location": trip.start_location,
        "start_date": trip.start_date.isoformat() if trip.start_date else None,
        "end_date": trip.end_date.isoformat() if trip.end_date else None,
        "days": trip.days,
        "travelers": trip.travelers,
        "budget": trip.total_budget or trip.budget,
        "currency": trip.currency,
        "travel_style": trip.travel_style,
        "transport_preference": trip.transport_preference,
        "accommodation_preference": trip.accommodation_preference,
        "interests": trip.interests or [],
        "created_at": trip.created_at.isoformat() if trip.created_at else None,
        "selected_hotel": _hotel_data(trip.selected_hotel) if trip.selected_hotel else None,
    }
    if trip.budget_plan:
        data["budget_summary"] = calculate_budget(trip, persist=False)
    if include_itinerary:
        data["itinerary"] = _itinerary_data(trip)
    return data


def _hotel_data(hotel):
    return {
        "id": hotel.id,
        "name": hotel.name,
        "destination": hotel.destination,
        "currency": hotel.currency,
        "price_per_night": hotel.price_per_night,
        "rating": hotel.rating,
        "amenities": hotel.amenities or [],
        "latitude": hotel.latitude,
        "longitude": hotel.longitude,
        "sample_data": hotel.sample_data,
    }


def _expense_data(expense):
    return {
        "id": expense.id,
        "category": expense.category,
        "description": expense.description,
        "amount": expense.amount,
        "date": expense.date.isoformat(),
        "notes": expense.notes,
    }


def _itinerary_data(trip):
    return [
        {
            "id": day.id,
            "day_number": day.day_number,
            "date": day.date.isoformat(),
            "items": [
                {
                    "id": item.id,
                    "place_id": item.place.id,
                    "place": item.place.name,
                    "category": item.place.category,
                    "description": item.place.description,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "travel_time": item.travel_time,
                    "distance": item.distance,
                    "estimated_cost": item.estimated_cost,
                    "currency": item.place.currency,
                    "latitude": item.place.latitude,
                    "longitude": item.place.longitude,
                    "sample_data": item.place.sample_data,
                    "notes": item.notes,
                }
                for item in day.items
            ],
        }
        for day in sorted(trip.days_plan, key=lambda entry: entry.day_number)
    ]


def _parse_trip_fields(data, trip=None):
    destination = data.get("destination", trip.destination if trip else "")
    destination = destination.strip() if isinstance(destination, str) else ""
    start_location = data.get("start_location", trip.start_location if trip else "")
    start_location = start_location.strip() if isinstance(start_location, str) else ""
    try:
        start_date = date.fromisoformat(data.get("start_date", trip.start_date.isoformat() if trip and trip.start_date else ""))
        end_date = date.fromisoformat(data.get("end_date", trip.end_date.isoformat() if trip and trip.end_date else ""))
        raw_travelers = data.get("travelers", trip.travelers if trip else 1)
        if isinstance(raw_travelers, bool):
            return None, "Travelers must be a whole number."
        travelers = int(raw_travelers)
        if isinstance(raw_travelers, float) and raw_travelers != travelers:
            return None, "Travelers must be a whole number."
        raw_budget = data.get("budget", data.get("total_budget", (trip.total_budget or trip.budget) if trip else 0))
        if isinstance(raw_budget, bool):
            return None, "Budget must be a valid amount."
        budget = float(raw_budget)
    except (TypeError, ValueError):
        return None, "Enter valid dates, traveler count, and budget."
    days = (end_date - start_date).days + 1
    if not destination or len(destination) > 150:
        return None, "Enter a destination of up to 150 characters."
    if start_date > end_date or days > 30:
        return None, "Choose a valid trip of no more than 30 days."
    if travelers < 1 or travelers > 20:
        return None, "Travelers must be between 1 and 20."
    if not isfinite(budget) or budget <= 0 or budget > 1_000_000_000:
        return None, "Budget must be greater than zero."
    interests = data.get("interests", trip.interests if trip else [])
    if not isinstance(interests, list) or any(not isinstance(item, str) for item in interests):
        return None, "Interests must be a list of text values."
    fields = {
        "destination": destination,
        "start_location": start_location[:150] or None,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "travelers": travelers,
        "budget": budget,
        "currency": data.get("currency", trip.currency if trip else "INR"),
        "travel_style": data.get("travel_style", trip.travel_style if trip else "balanced"),
        "transport_preference": data.get(
            "transport_preference", trip.transport_preference if trip else "public transport"
        ),
        "accommodation_preference": data.get(
            "accommodation_preference", trip.accommodation_preference if trip else "hotel"
        ),
        "interests": [item.strip()[:40] for item in interests if item.strip()][:20],
    }
    if not isinstance(fields["currency"], str) or fields["currency"] not in {"INR", "USD", "EUR", "GBP", "JPY"}:
        return None, "Choose a supported currency."
    for field, choices in (
        ("travel_style", {"budget", "balanced", "comfort", "luxury"}),
        ("transport_preference", {"walking", "public transport", "car", "cab"}),
        ("accommodation_preference", {"hostel", "budget hotel", "hotel", "luxury hotel"}),
    ):
        if not isinstance(fields[field], str) or fields[field].casefold() not in choices:
            return None, f"Choose a valid {field.replace('_', ' ')}."
        fields[field] = fields[field].casefold()
    return fields, None


def _set_trip_fields(trip, fields):
    for key, value in fields.items():
        if key == "budget":
            trip.budget = value
            trip.total_budget = value
        else:
            setattr(trip, key, value)


def _parse_expense(data, current=None):
    if not isinstance(data, dict):
        return None, "A JSON request body is required."
    category = data.get("category", current.category if current else "")
    description = data.get("description", current.description if current else "")
    try:
        raw_amount = data.get("amount", current.amount if current else 0)
        if isinstance(raw_amount, bool):
            return None, "Expense amount must be a valid number."
        amount = float(raw_amount)
        expense_date = date.fromisoformat(data.get("date", current.date.isoformat() if current else date.today().isoformat()))
    except (TypeError, ValueError):
        return None, "Enter a valid amount and date."
    if not isinstance(category, str) or category.casefold() not in EXPENSE_CATEGORIES:
        return None, "Choose a valid expense category."
    if not isinstance(description, str) or not description.strip() or len(description) > 200:
        return None, "Enter a description of up to 200 characters."
    if not isfinite(amount) or amount <= 0 or amount > 1_000_000_000:
        return None, "Expense amount must be greater than zero."
    notes = data.get("notes", current.notes if current else "")
    if not isinstance(notes, str):
        return None, "Notes must be text."
    return {
        "category": category.casefold(),
        "description": description.strip(),
        "amount": amount,
        "date": expense_date,
        "notes": notes.strip()[:500],
    }, None


@trips_bp.get("")
@trips_bp.get("/")
@jwt_required()
def list_trips():
    trips = Trip.query.filter_by(user_id=_current_user_id()).order_by(Trip.created_at.desc()).all()
    return jsonify(status="success", trips=[_trip_data(trip) for trip in trips])


@trips_bp.post("")
@trips_bp.post("/")
@jwt_required()
def create_trip():
    data = request.get_json(silent=True)
    fields, error = _parse_trip_fields(data if isinstance(data, dict) else {})
    if error:
        return jsonify(status="error", message=error), 400
    trip = Trip(user_id=_current_user_id())
    _set_trip_fields(trip, fields)
    db.session.add(trip)
    db.session.flush()
    calculate_budget(trip)
    db.session.commit()
    return jsonify(status="success", trip=_trip_data(trip)), 201


@trips_bp.get("/<int:trip_id>")
@jwt_required()
def get_trip(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    return jsonify(status="success", trip=_trip_data(trip, include_itinerary=True))


@trips_bp.put("/<int:trip_id>")
@jwt_required()
def update_trip(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    data = request.get_json(silent=True)
    fields, validation_error = _parse_trip_fields(data if isinstance(data, dict) else {}, trip)
    if validation_error:
        return jsonify(status="error", message=validation_error), 400
    if trip.selected_hotel and trip.selected_hotel.currency != fields["currency"]:
        return jsonify(
            status="error",
            message="Remove the selected hotel before changing the trip currency.",
        ), 400
    itinerary_settings = (
        "destination",
        "start_date",
        "end_date",
        "interests",
        "budget",
        "travelers",
        "travel_style",
        "transport_preference",
        "accommodation_preference",
    )
    itinerary_changed = any(
        (
            (trip.total_budget or trip.budget) != fields["budget"]
            if key == "budget" else getattr(trip, key) != fields[key]
        )
        for key in itinerary_settings
    )
    if itinerary_changed and trip.days_plan:
        trip.days_plan.clear()
    _set_trip_fields(trip, fields)
    trip.updated_at = datetime.utcnow()
    calculate_budget(trip)
    db.session.commit()
    return jsonify(
        status="success",
        trip=_trip_data(trip),
        message=(
            "Trip details saved. Generate a fresh itinerary to reflect the changes."
            if itinerary_changed else "Trip details saved."
        ),
    )


@trips_bp.delete("/<int:trip_id>")
@jwt_required()
def delete_trip(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    db.session.delete(trip)
    db.session.commit()
    return jsonify(status="success", message="Trip deleted.")


@trips_bp.post("/<int:trip_id>/duplicate")
@jwt_required()
def duplicate_trip(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    duplicate = Trip(user_id=_current_user_id())
    for field in (
        "destination", "start_location", "start_date", "end_date", "days", "travelers",
        "budget", "total_budget", "currency", "travel_style", "transport_preference",
        "accommodation_preference",
    ):
        setattr(duplicate, field, getattr(trip, field))
    duplicate.interests = list(trip.interests or [])
    db.session.add(duplicate)
    db.session.flush()
    calculate_budget(duplicate)
    db.session.commit()
    return jsonify(status="success", trip=_trip_data(duplicate)), 201


@trips_bp.post("/<int:trip_id>/generate")
@trips_bp.post("/<int:trip_id>/reoptimize")
@jwt_required()
def generate_trip_itinerary(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    if generate_itinerary(trip) is None:
        db.session.rollback()
        return jsonify(
            status="error",
            message="No sample place catalog is available for this destination yet.",
        ), 422
    budget = calculate_budget(trip)
    db.session.commit()
    return jsonify(
        status="success",
        itinerary=_itinerary_data(trip),
        budget=budget,
        message="Itinerary optimized using the available sample place catalog.",
    )


@trips_bp.get("/<int:trip_id>/itinerary")
@jwt_required()
def get_itinerary(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    return jsonify(status="success", itinerary=_itinerary_data(trip))


@trips_bp.get("/<int:trip_id>/recommendations")
@jwt_required()
def get_recommendations(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    seed_sample_places()
    candidates = Place.query.filter(
        func.lower(Place.destination) == trip.destination.casefold()
    ).all()
    return jsonify(
        status="success",
        sample_data=True,
        recommendations=[
            {
                "place": {
                    "id": entry["place"].id,
                    "name": entry["place"].name,
                    "category": entry["place"].category,
                    "description": entry["place"].description,
                    "estimated_cost": entry["place"].estimated_cost,
                    "currency": entry["place"].currency,
                    "visit_duration": entry["place"].visit_duration,
                },
                "score": entry["score"],
                "score_breakdown": entry["score_breakdown"],
            }
            for entry in recommend_places(trip, candidates)
        ],
    )


@trips_bp.get("/<int:trip_id>/budget")
@trips_bp.post("/<int:trip_id>/budget/calculate")
@jwt_required()
def get_budget(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    budget = calculate_budget(trip, persist=request.method == "POST")
    if request.method == "POST":
        db.session.commit()
    return jsonify(status="success", budget=budget)


@trips_bp.get("/<int:trip_id>/expenses")
@jwt_required()
def list_expenses(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    expenses = Expense.query.filter_by(trip_id=trip.id).order_by(
        Expense.date.desc(), Expense.id.desc()
    ).all()
    return jsonify(status="success", expenses=[_expense_data(item) for item in expenses])


@trips_bp.post("/<int:trip_id>/expenses")
@jwt_required()
def add_expense(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    fields, validation_error = _parse_expense(request.get_json(silent=True))
    if validation_error:
        return jsonify(status="error", message=validation_error), 400
    expense = Expense(trip=trip, **fields)
    db.session.add(expense)
    calculate_budget(trip)
    db.session.commit()
    return jsonify(status="success", expense=_expense_data(expense)), 201


@trips_bp.put("/<int:trip_id>/expenses/<int:expense_id>")
@jwt_required()
def update_expense(trip_id, expense_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    expense = Expense.query.filter_by(id=expense_id, trip_id=trip.id).first()
    if expense is None:
        return jsonify(status="error", message="Expense not found."), 404
    fields, validation_error = _parse_expense(request.get_json(silent=True), expense)
    if validation_error:
        return jsonify(status="error", message=validation_error), 400
    for key, value in fields.items():
        setattr(expense, key, value)
    calculate_budget(trip)
    db.session.commit()
    return jsonify(status="success", expense=_expense_data(expense))


@trips_bp.delete("/<int:trip_id>/expenses/<int:expense_id>")
@jwt_required()
def delete_expense(trip_id, expense_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    expense = Expense.query.filter_by(id=expense_id, trip_id=trip.id).first()
    if expense is None:
        return jsonify(status="error", message="Expense not found."), 404
    trip.expenses.remove(expense)
    db.session.delete(expense)
    calculate_budget(trip)
    db.session.commit()
    return jsonify(status="success", message="Expense deleted.")


@trips_bp.get("/<int:trip_id>/hotels")
@jwt_required()
def recommend_hotels(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    seed_sample_hotels()
    hotels = Hotel.query.filter(func.lower(Hotel.destination) == trip.destination.casefold()).all()
    return jsonify(
        status="success",
        sample_data=True,
        hotels=[
            {**_hotel_data(hotel), "estimated_stay": hotel.price_per_night * max(trip.days - 1, 1)}
            for hotel in sorted(hotels, key=lambda item: (item.price_per_night, -item.rating))
        ],
    )


@trips_bp.post("/<int:trip_id>/hotels/<int:hotel_id>")
@jwt_required()
def select_hotel(trip_id, hotel_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    hotel = Hotel.query.filter_by(id=hotel_id).first()
    if hotel is None or hotel.destination.casefold() != trip.destination.casefold():
        return jsonify(status="error", message="Hotel not found for this destination."), 404
    if hotel.currency != trip.currency:
        return jsonify(
            status="error",
            message=f"This sample price is in {hotel.currency}. Set your trip currency to {hotel.currency} before selecting it; no exchange rate is assumed.",
        ), 400
    trip.selected_hotel = hotel
    calculate_budget(trip)
    db.session.commit()
    return jsonify(status="success", trip=_trip_data(trip))


@trips_bp.delete("/<int:trip_id>/hotels")
@jwt_required()
def remove_selected_hotel(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    trip.selected_hotel = None
    calculate_budget(trip)
    db.session.commit()
    return jsonify(status="success", trip=_trip_data(trip))


@trips_bp.get("/<int:trip_id>/weather")
@jwt_required()
def weather_unavailable(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    return jsonify(
        status="unavailable",
        destination=trip.destination,
        message="Live weather is unavailable because no weather provider is configured. No forecast is being estimated.",
    )


@trips_bp.get("/<int:trip_id>/export.pdf")
@jwt_required()
def export_trip_pdf(trip_id):
    trip, error = _owned_trip(trip_id)
    if error:
        return error
    output = BytesIO()
    page = canvas.Canvas(output, pagesize=letter)
    _, height = letter
    y = height - 48

    def line(text, gap=18):
        nonlocal y
        if y < 55:
            page.showPage()
            y = height - 48
        safe_text = str(text).encode("cp1252", "replace").decode("cp1252")
        page.drawString(48, y, safe_text[:100])
        y -= gap

    page.setTitle(f"TripWise plan - {trip.destination}")
    line("TripWise - Trip plan", 24)
    line(f"Destination: {trip.destination}")
    line(f"Dates: {trip.start_date} to {trip.end_date} ({trip.days} days)")
    line(f"Travelers: {trip.travelers}")
    line(f"Budget: {trip.currency} {trip.total_budget or trip.budget:,.2f}")
    summary = calculate_budget(trip, persist=False)
    line(f"Estimated spend: {trip.currency} {summary['estimated_total']:,.2f}")
    line(f"Recorded expenses: {trip.currency} {summary['actual_total']:,.2f}")
    line(f"Budget remaining: {trip.currency} {summary['remaining']:,.2f}")
    line("Estimated categories", 18)
    for category in summary["categories"]:
        line(f"  {category['name']}: {trip.currency} {category['estimated']:,.2f}")
    if trip.selected_hotel:
        line(f"Selected sample hotel: {trip.selected_hotel.name}")
    line("Itinerary", 24)
    days = _itinerary_data(trip)
    if not days:
        line("No itinerary generated yet.")
    for day in days:
        line(f"Day {day['day_number']} - {day['date']}", 18)
        for item in day["items"]:
            line(
                f"  {item['start_time']}-{item['end_time']} {item['place']} "
                f"(estimated {item['currency']} {item['estimated_cost']:,.2f})",
            )
    line("Travel-time and cost figures are estimates, not live quotes.")
    page.save()
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="tripwise-{trip.id}.pdf"'
    return response
