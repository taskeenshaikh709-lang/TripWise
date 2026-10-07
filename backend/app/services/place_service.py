from app.extensions import db
from app.models import Place


SAMPLE_PLACES = {
    "jaipur": [
        ("Amber Fort", "Historical", "Hilltop fort complex and museum.", 500, 150, 26.9855, 75.8513, 4.8, "INR"),
        ("Hawa Mahal", "Historical", "Landmark palace facade in the old city.", 200, 60, 26.9239, 75.8267, 4.6, "INR"),
        ("City Palace", "Culture", "Royal residence with galleries and courtyards.", 400, 120, 26.9258, 75.8237, 4.7, "INR"),
        ("Jantar Mantar", "Historical", "Historic astronomical observatory.", 200, 90, 26.9248, 75.8246, 4.5, "INR"),
        ("Jal Mahal viewpoint", "Photography", "Lakeside viewpoint of the water palace.", 0, 45, 26.9535, 75.8461, 4.4, "INR"),
        ("Albert Hall Museum", "Culture", "Museum of art and regional history.", 150, 120, 26.9117, 75.8197, 4.5, "INR"),
        ("Johari Bazaar", "Shopping", "Traditional market for textiles and crafts.", 0, 90, 26.9192, 75.8265, 4.3, "INR"),
        ("Central Park", "Nature", "Public garden with walking paths.", 0, 60, 26.9025, 75.8128, 4.2, "INR"),
    ],
    "paris": [
        ("Eiffel Tower gardens", "Photography", "Public grounds around the Eiffel Tower.", 0, 90, 48.8584, 2.2945, 4.8, "EUR"),
        ("Louvre Museum", "Culture", "Art museum; check official opening information before visiting.", 22, 180, 48.8606, 2.3376, 4.9, "EUR"),
        ("Musée d'Orsay", "Culture", "Museum in a former railway station.", 16, 150, 48.8600, 2.3266, 4.7, "EUR"),
        ("Luxembourg Gardens", "Nature", "Historic garden with public walking paths.", 0, 75, 48.8462, 2.3372, 4.6, "EUR"),
        ("Le Marais", "Food", "Historic neighborhood with cafes and shops.", 0, 100, 48.8566, 2.3622, 4.5, "EUR"),
        ("Île de la Cité", "Historical", "Historic island in the River Seine.", 0, 90, 48.8540, 2.3470, 4.6, "EUR"),
        ("Montmartre", "Culture", "Hilltop neighborhood with art studios and views.", 0, 120, 48.8867, 2.3431, 4.6, "EUR"),
    ],
}


def seed_sample_places():
    for destination, entries in SAMPLE_PLACES.items():
        if Place.query.filter(db.func.lower(Place.destination) == destination).first():
            continue
        for name, category, description, cost, duration, lat, lon, rating, currency in entries:
            db.session.add(
                Place(
                    name=name,
                    destination=destination.title(),
                    currency=currency,
                    category=category,
                    description=description,
                    estimated_cost=cost,
                    visit_duration=duration,
                    latitude=lat,
                    longitude=lon,
                    rating=rating,
                    sample_data=True,
                )
            )
    db.session.commit()


def recommend_places(trip, places):
    """Explainable weighted score with normalized 0–1 input features."""
    interests = {value.casefold() for value in (trip.interests or [])}
    budget_per_day = (trip.total_budget or trip.budget) / max(trip.days, 1)
    candidates = []
    center_lat = sum(place.latitude or 0 for place in places) / max(len(places), 1)
    center_lon = sum(place.longitude or 0 for place in places) / max(len(places), 1)
    for place in places:
        match = 1.0 if place.category.casefold() in interests else (
            0.45 if any(key in place.category.casefold() or place.category.casefold() in key for key in interests) else 0.2
        )
        popularity = min(max(place.rating / 5, 0), 1)
        distance = 1.0
        if place.latitude is not None and place.longitude is not None:
            km = ((place.latitude - center_lat) ** 2 + (place.longitude - center_lon) ** 2) ** 0.5 * 111
            distance = 1 / (1 + km / 5)
        cost = (
            min(1.0, budget_per_day / max(place.estimated_cost * 3, 1))
            if place.currency == trip.currency else 0.5
        )
        time = 1.0 if place.visit_duration <= 240 else max(0.0, 1 - (place.visit_duration - 240) / 240)
        score = match * 0.40 + popularity * 0.20 + distance * 0.15 + cost * 0.15 + time * 0.10
        candidates.append((score, place))
    candidates.sort(key=lambda candidate: (-candidate[0], candidate[1].name.casefold()))
    recommendations = []
    for score, place in candidates:
        match = 1.0 if place.category.casefold() in interests else (
            0.45 if any(
                key in place.category.casefold() or place.category.casefold() in key
                for key in interests
            ) else 0.2
        )
        distance = 1.0
        if place.latitude is not None and place.longitude is not None:
            km = ((place.latitude - center_lat) ** 2 + (place.longitude - center_lon) ** 2) ** 0.5 * 111
            distance = 1 / (1 + km / 5)
        cost = (
            min(1.0, budget_per_day / max(place.estimated_cost * 3, 1))
            if place.currency == trip.currency else 0.5
        )
        time = 1.0 if place.visit_duration <= 240 else max(
            0.0, 1 - (place.visit_duration - 240) / 240
        )
        recommendations.append({
            "place": place,
            "score": round(score * 100, 1),
            "score_breakdown": {
                "interest_match": round(match * 100, 1),
                "popularity": round(min(max(place.rating / 5, 0), 1) * 100, 1),
                "distance_efficiency": round(distance * 100, 1),
                "budget_compatibility": round(cost * 100, 1),
                "time_compatibility": round(time * 100, 1),
            },
        })
    return recommendations
