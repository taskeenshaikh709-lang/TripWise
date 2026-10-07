from datetime import timedelta

from app.extensions import db
from app.models import ItineraryDay, ItineraryItem, Place
from app.services.place_service import recommend_places, seed_sample_places
from app.services.routing_service import distance_km, estimated_travel_minutes


def generate_itinerary(trip):
    seed_sample_places()
    places = Place.query.filter(
        db.func.lower(Place.destination) == trip.destination.casefold()
    ).all()
    if not places:
        return None

    recommendations = recommend_places(trip, places)
    trip.days_plan.clear()
    db.session.flush()
    used_ids = set()
    daily_activity_limit = max(
        1,
        int(((trip.total_budget or trip.budget) * 0.30) / max(trip.days, 1) / 500),
    )
    daily_activity_limit = min(daily_activity_limit, 3)
    for day_number in range(1, trip.days + 1):
        day = ItineraryDay(
            trip=trip,
            day_number=day_number,
            date=trip.start_date + timedelta(days=day_number - 1),
        )
        db.session.add(day)
        clock = 9 * 60
        previous_place = None
        daily_cost = 0
        order = 0
        for entry in recommendations:
            place = entry["place"]
            if place.id in used_ids or order >= daily_activity_limit:
                continue
            activity_cost = place.estimated_cost if place.currency == trip.currency else 0
            if daily_cost + activity_cost > (trip.total_budget or trip.budget) * 0.3 / trip.days:
                continue
            travel_distance = distance_km(previous_place, place) if previous_place else 0
            travel_minutes = (
                estimated_travel_minutes(travel_distance, trip.transport_preference)
                if previous_place else 0
            )
            start = clock + travel_minutes
            finish = start + place.visit_duration
            if finish > 18 * 60:
                continue
            day.items.append(
                ItineraryItem(
                    place=place,
                    start_time=f"{start // 60:02d}:{start % 60:02d}",
                    end_time=f"{finish // 60:02d}:{finish % 60:02d}",
                    travel_time=travel_minutes,
                    distance=round(travel_distance, 2),
                    estimated_cost=place.estimated_cost,
                    order_index=order,
                    notes=f"Recommendation score: {entry['score']:.1f}/100. Travel duration is an estimate.",
                )
            )
            used_ids.add(place.id)
            daily_cost += activity_cost
            order += 1
            clock = finish + 45
            previous_place = place
    db.session.flush()
    return trip.days_plan
