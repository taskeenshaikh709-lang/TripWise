from app.extensions import db
from app.models import Hotel


SAMPLE_HOTELS = {
    "jaipur": [
        ("Jaipur Sample Guesthouse", "INR", 1800, 4.1, 26.9200, 75.8200, ["Wi-Fi", "Breakfast"]),
        ("Pink City Sample Hotel", "INR", 3200, 4.4, 26.9230, 75.8280, ["Wi-Fi", "Restaurant", "Air conditioning"]),
        ("Amber View Sample Stay", "INR", 5200, 4.6, 26.9900, 75.8500, ["Wi-Fi", "Pool", "Breakfast"]),
    ],
    "paris": [
        ("Paris Sample Guesthouse", "EUR", 85, 4.0, 48.8550, 2.3500, ["Wi-Fi"]),
        ("Left Bank Sample Hotel", "EUR", 145, 4.3, 48.8500, 2.3400, ["Wi-Fi", "Breakfast"]),
        ("Central Paris Sample Stay", "EUR", 240, 4.6, 48.8600, 2.3300, ["Wi-Fi", "Restaurant", "Air conditioning"]),
    ],
}


def seed_sample_hotels():
    for destination, entries in SAMPLE_HOTELS.items():
        if Hotel.query.filter(db.func.lower(Hotel.destination) == destination).first():
            continue
        for name, currency, price, rating, latitude, longitude, amenities in entries:
            db.session.add(
                Hotel(
                    name=name,
                    destination=destination.title(),
                    currency=currency,
                    price_per_night=price,
                    rating=rating,
                    latitude=latitude,
                    longitude=longitude,
                    amenities=amenities,
                    sample_data=True,
                )
            )
    db.session.commit()
