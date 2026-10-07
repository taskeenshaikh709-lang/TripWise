import math


def distance_km(first, second):
    """Haversine straight-line distance; this is not a road-route distance."""
    if None in (first.latitude, first.longitude, second.latitude, second.longitude):
        return 0.0
    lat1, lon1, lat2, lon2 = map(
        math.radians,
        (first.latitude, first.longitude, second.latitude, second.longitude),
    )
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 6371 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def estimated_travel_minutes(kilometers, preference):
    speeds = {"walking": 4, "public transport": 18, "car": 28, "cab": 24}
    speed = speeds.get((preference or "").lower(), 18)
    return 0 if kilometers < 0.1 else max(10, math.ceil(kilometers / speed * 60 / 5) * 5)
