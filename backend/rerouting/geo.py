"""Geography helpers for return-logistics distance.

Locations are coarse (city centroids) — enough to make the seller <-> buyer
distance, and therefore the logistics cost, vary realistically. Distance is the
great-circle (haversine) distance in km between two lat/lng points.
"""

import math

# A handful of Indian cities with approximate centroids (lat, lng). Used to seed
# users and as a fallback when a user has no explicit coordinates.
CITY_COORDS = {
    "Bengaluru": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.7041, 77.1025),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
}

# Where the central processing facility sits — the anchor for routing legs when a
# party's own location is unknown.
FACILITY_CITY = "Bengaluru"


def haversine_km(a, b) -> float:
    """Great-circle distance in km between two (lat, lng) tuples."""
    if not a or not b:
        return 0.0
    lat1, lng1 = a
    lat2, lng2 = b
    r = 6371.0  # Earth radius, km
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return round(2 * r * math.asin(min(1.0, math.sqrt(h))), 1)


def coords_for(user) -> tuple:
    """Best-effort (lat, lng) for a user: explicit fields, then city, then None."""
    if user is None:
        return None
    lat = getattr(user, "lat", None)
    lng = getattr(user, "lng", None)
    if lat is not None and lng is not None:
        return (lat, lng)
    city = (getattr(user, "city", "") or "").strip()
    return CITY_COORDS.get(city)


def facility_coords() -> tuple:
    return CITY_COORDS[FACILITY_CITY]


def distance_between(seller, buyer) -> float:
    """Distance in km between two users, falling back to the facility location
    for whichever side has no known coordinates."""
    a = coords_for(seller) or facility_coords()
    b = coords_for(buyer) or facility_coords()
    return haversine_km(a, b)
