from app.extensions import db
from app.models import Budget


def calculate_budget(trip, persist=True):
    """Build a transparent starter estimate using the trip's dates and preferences."""
    days = max(trip.days, 1)
    available = trip.total_budget or trip.budget
    lodging_factor = {
        "hostel": 0.7,
        "budget hotel": 0.85,
        "hotel": 1,
        "luxury hotel": 1.5,
    }.get(trip.accommodation_preference.lower(), 1)
    accommodation = available * 0.30 * lodging_factor
    if trip.selected_hotel:
        accommodation = trip.selected_hotel.price_per_night * max(days - 1, 1)
    transport_factor = {
        "walking": 0.5,
        "public transport": 1,
        "car": 1.8,
        "cab": 1.5,
    }.get(trip.transport_preference.lower(), 1)
    transport = available * 0.15 * transport_factor
    food = available * 0.25
    activities = sum(
        item.estimated_cost
        for day in trip.days_plan
        for item in day.items
        if item.place.currency == trip.currency
    )
    if not activities:
        activities = available * 0.10
    shopping = available * 0.05
    emergency = available * 0.10
    estimated = accommodation + transport + food + activities + shopping + emergency
    actual = sum(expense.amount for expense in trip.expenses)

    categories = {
        "Accommodation": round(accommodation, 2),
        "Transport": round(transport, 2),
        "Food": round(food, 2),
        "Activities": round(activities, 2),
        "Shopping": round(shopping, 2),
        "Emergency": round(emergency, 2),
    }
    estimated = round(estimated, 2)
    actual = round(actual, 2)
    if persist:
        budget = trip.budget_plan or Budget(trip=trip)
        budget.accommodation = categories["Accommodation"]
        budget.transport = categories["Transport"]
        budget.food = categories["Food"]
        budget.activities = categories["Activities"]
        budget.shopping = categories["Shopping"]
        budget.emergency = categories["Emergency"]
        budget.total_estimated = estimated
        budget.actual_total = actual
        budget.remaining = round(available - actual, 2)
        db.session.add(budget)
        db.session.flush()
    return {
        "currency": trip.currency,
        "total_budget": round(available, 2),
        "estimated_total": estimated,
        "actual_total": actual,
        "remaining": round(available - actual, 2),
        "percentage_used": round(actual / available * 100, 1) if available else 0,
        "over_budget": estimated > available,
        "categories": [
            {"name": name, "estimated": value} for name, value in categories.items()
        ],
    }
