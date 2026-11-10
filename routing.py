"""
SafeRoute AI - Routing Module
Handles route calculation and hazard-aware route recommendations
using OSRM (Open Source Routing Machine) public API.
"""

import math
import requests
import re

# OSRM public demo server
OSRM_BASE_URL = "https://router.project-osrm.org"

ROUTING_VERSION = "3.2"

# Route recommendation tuning
MAX_DETOUR_RATIO = 1.3      # never recommend a route >30% longer/slower than the best one
KM_PER_HAZARD_POINT = 0.5   # 1 severity point of risk is worth up to 0.5 km of detour


# ─────────────────────────────────────────────────────────────
# Known landmarks (checked BEFORE the online geocoder)
# Coordinates verified against Wikipedia / OSM-derived sources, Nov 2026.
# Each entry: canonical key -> {lat, lng, display_name, aliases}
# ─────────────────────────────────────────────────────────────

MULTAN_LANDMARKS = {
    "kutchery chowk": {"lat": 30.2091, "lng": 71.4646,
                       "display_name": "Kutchery (Kachehri) Chowk, Multan",
                       "aliases": ["kutchery", "katchery", "kachehri", "kachehry", "kacheri",
                                   "kutchehry", "chowk kutchery", "chowk katchery",
                                   "kachehri chowk", "katchery chowk", "district courts"]},
    "ghanta ghar": {"lat": 30.1986, "lng": 71.4678,
                    "display_name": "Ghanta Ghar (Clock Tower), Multan",
                    "aliases": ["clock tower", "ghanta ghar chowk"]},
    "shah rukn-e-alam": {"lat": 30.1989, "lng": 71.4714,
                         "display_name": "Tomb of Shah Rukn-e-Alam, Qila Kohna Qasim Bagh, Multan",
                         "aliases": ["rukn-e-alam", "rukn e alam", "shah rukn e alam", "qasim bagh", "multan fort"]},
    "nishtar hospital": {"lat": 30.2025, "lng": 71.4444,
                         "display_name": "Nishtar Hospital, Nishtar Road, Multan",
                         "aliases": ["nishtar", "nishtar medical university", "nishtar medical college", "nmu"]},
    "bahauddin zakariya university": {"lat": 30.2636, "lng": 71.5097,
                                      "display_name": "Bahauddin Zakariya University (BZU), Bosan Road, Multan",
                                      "aliases": ["bzu", "zakariya university", "bahauddin zakariya", "bzu multan"]},
    "chungi no 9": {"lat": 30.2084, "lng": 71.4716,
                    "display_name": "Chungi No 9, Multan",
                    "aliases": ["chungi 9", "chungi number 9", "chungi no. 9"]},
    "mall of multan": {"lat": 30.2426, "lng": 71.4847,
                       "display_name": "Mall of Multan, Bosan Road, Shalimar Colony, Multan",
                       "aliases": []},
    "gulgasht colony": {"lat": 30.2210, "lng": 71.4740,
                        "display_name": "Gulgasht Colony, Multan",
                        "aliases": ["gulgasht", "gul gasht"]},
    # Approximate (area-level) entries — not individually verified
    "bosan road": {"lat": 30.2271, "lng": 71.4782,
                   "display_name": "Bosan Road, Multan", "aliases": []},
    "multan cantt": {"lat": 30.1850, "lng": 71.4600,
                     "display_name": "Multan Cantonment, Multan",
                     "aliases": ["cantt", "cantonment"]},
}

LAHORE_LANDMARKS = {
    "liberty market": {"lat": 31.5115, "lng": 74.3441, "display_name": "Liberty Market, Gulberg III, Lahore", "aliases": ["liberty"]},
    "gulberg": {"lat": 31.5204, "lng": 74.3487, "display_name": "Main Boulevard Gulberg, Lahore", "aliases": []},
    "mall road": {"lat": 31.5546, "lng": 74.3262, "display_name": "The Mall Road, Lahore", "aliases": []},
    "kalma chowk": {"lat": 31.5035, "lng": 74.3318, "display_name": "Kalma Chowk, Ferozepur Road, Lahore", "aliases": []},
    "lahore railway station": {"lat": 31.5794, "lng": 74.3332, "display_name": "Lahore Junction Railway Station", "aliases": ["railway station"]},
    "punjab university": {"lat": 31.5005, "lng": 74.3025, "display_name": "University of the Punjab, New Campus, Lahore", "aliases": []},
    "lahore museum": {"lat": 31.5682, "lng": 74.3095, "display_name": "Lahore Museum, Mall Road, Lahore", "aliases": []},
    "badshahi mosque": {"lat": 31.5881, "lng": 74.3105, "display_name": "Badshahi Mosque, Walled City, Lahore", "aliases": []},
    "johar town": {"lat": 31.4697, "lng": 74.2728, "display_name": "Johar Town, Lahore", "aliases": []},
    "dha": {"lat": 31.4780, "lng": 74.3790, "display_name": "DHA Phase 3, Lahore", "aliases": ["dha phase 3"]},
    "model town": {"lat": 31.4855, "lng": 74.3211, "display_name": "Model Town, Lahore", "aliases": []},
    "canal road": {"lat": 31.5165, "lng": 74.3180, "display_name": "Canal Bank Road, Lahore", "aliases": []},
}

CITY_LANDMARKS = {"multan": MULTAN_LANDMARKS, "lahore": LAHORE_LANDMARKS}

CITY_CENTERS = {
    "multan": (30.1984, 71.4687),
    "lahore": (31.5204, 74.3587),
    "islamabad": (33.6844, 73.0479),
    "karachi": (24.8607, 67.0011),
}

# Results further than this from the active city centre are rejected as wrong matches
MAX_CITY_RADIUS_KM = 30

_STOPWORDS = {"pakistan", "punjab", "multan", "lahore", "islamabad", "karachi", "near", "the", "road"}


def _normalize(text):
    """Lowercase, drop punctuation and city/country words, collapse spaces."""
    text = text.lower().replace("-", " ").replace(".", " ")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return [t for t in text.split() if t]


def _match_landmark(text, landmarks):
    """
    Match free text against landmark keys and aliases.
    A landmark matches when ALL words of a key/alias appear in the text.
    The longest (most specific) match wins, so 'mall of multan' beats 'multan'.
    """
    words = set(_normalize(text))
    best, best_len = None, 0
    for key, val in landmarks.items():
        for name in [key] + val.get("aliases", []):
            name_words = [w for w in _normalize(name) if w not in _STOPWORDS] or _normalize(name)
            if name_words and all(w in words for w in name_words) and len(" ".join(name_words)) > best_len:
                best, best_len = val, len(" ".join(name_words))
    if best is None:
        return None
    return {"lat": best["lat"], "lng": best["lng"], "display_name": best["display_name"], "source": "landmark"}


def _detect_city(text, city):
    """City mentioned in the text wins over the sidebar selection."""
    lower = text.lower()
    for c in CITY_CENTERS:
        if c in lower:
            return c
    return (city or "multan").lower()


def geocode_location(location_name, city="Multan"):
    """
    Convert an address, landmark or 'lat, lng' string into coordinates.

    Order:
      1. Raw coordinates
      2. Built-in landmark table (fuzzy word match, verified coordinates)
      3. OpenStreetMap Nominatim, restricted to a box around the active city
      4. Approximate city-centre fallback (flagged with approximate=True)
    """
    if not location_name or not str(location_name).strip():
        return None

    raw_text = str(location_name).strip()
    active_city = _detect_city(raw_text, city)

    # 1. Direct coordinates: '30.1984, 71.4687'
    m = re.match(r"^\s*([-+]?\d{1,2}(?:\.\d+)?)\s*[,;/ ]\s*([-+]?\d{1,3}(?:\.\d+)?)\s*$", raw_text)
    if m:
        lat, lng = float(m.group(1)), float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            addr_name = reverse_geocode(lat, lng)
            return {"lat": lat, "lng": lng, "source": "coordinates",
                    "display_name": addr_name or f"Coordinates: {lat:.4f}, {lng:.4f}"}

    # 2. Built-in landmarks for the active city
    landmarks = CITY_LANDMARKS.get(active_city)
    if landmarks:
        hit = _match_landmark(raw_text, landmarks)
        if hit:
            return hit

    # 3. Nominatim, bounded to the active city
    center = CITY_CENTERS.get(active_city)
    headers = {
        "User-Agent": "SafeRouteAI-Pakistan/3.1 (hackathon prototype)",
        "Accept-Language": "en",
    }
    city_name = active_city.title()
    queries = [raw_text] if city_name.lower() in raw_text.lower() else [f"{raw_text}, {city_name}", raw_text]

    for q in queries:
        params = {"q": q, "format": "json", "limit": 5, "countrycodes": "pk"}
        if center:
            d = 0.25  # ~25 km box around the city centre
            params["viewbox"] = f"{center[1]-d},{center[0]+d},{center[1]+d},{center[0]-d}"
            params["bounded"] = 1
        try:
            response = requests.get("https://nominatim.openstreetmap.org/search",
                                    params=params, headers=headers, timeout=8)
            if response.status_code != 200:
                continue
            for item in response.json():
                lat, lng = float(item["lat"]), float(item["lon"])
                if center and haversine_distance(lat, lng, center[0], center[1]) > MAX_CITY_RADIUS_KM * 1000:
                    continue
                return {"lat": lat, "lng": lng, "source": "nominatim",
                        "display_name": item.get("display_name", raw_text)}
        except Exception:
            continue

    # 4. Last resort: city centre, clearly flagged as approximate
    if center:
        return {"lat": center[0], "lng": center[1], "source": "city_center", "approximate": True,
                "display_name": f"{raw_text} — exact place not found, using {city_name} city centre"}

    return None


def reverse_geocode(lat, lng):
    """
    Get human-readable address from coordinates.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json"
        }
        headers = {
            "User-Agent": "SafeRouteAI-Hackathon/2.0 (contact: info@saferoute.ai)",
            "Accept-Language": "en"
        }
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("display_name", f"{lat:.4f}, {lng:.4f}")
    except Exception:
        pass
    return f"{lat:.4f}, {lng:.4f}"


def get_routes(start_lat, start_lng, end_lat, end_lng, alternatives=True):
    """
    Get routes between two points using OSRM.

    Args:
        start_lat, start_lng: Starting coordinates
        end_lat, end_lng: Destination coordinates
        alternatives: Whether to request alternative routes

    Returns:
        dict with 'success', 'routes' (list), 'error'
    """
    result = {
        "success": False,
        "routes": [],
        "error": None
    }

    try:
        # OSRM uses lng,lat order
        url = f"{OSRM_BASE_URL}/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "alternatives": "true" if alternatives else "false",
            "steps": "true"
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok":
            result["error"] = f"Routing service error: {data.get('message', 'Unknown error')}"
            return result

        routes = []
        for i, route in enumerate(data.get("routes", [])):
            # Extract coordinates (GeoJSON is [lng, lat], convert to [lat, lng])
            geojson_coords = route["geometry"]["coordinates"]
            coords = [[c[1], c[0]] for c in geojson_coords]

            distance_m = route.get("distance", 0)
            duration_s = route.get("duration", 0)

            routes.append({
                "index": i,
                "coordinates": coords,
                "distance_km": round(distance_m / 1000, 2),
                "duration_min": round(duration_s / 60, 1),
                "hazard_count": 0,  # Will be calculated later
                "hazard_score": 0.0
            })

        result["success"] = True
        result["routes"] = routes

    except requests.exceptions.ConnectionError:
        result["error"] = "Could not connect to routing service. Please check your internet connection."
    except requests.exceptions.Timeout:
        result["error"] = "Routing service timed out. Please try again."
    except Exception as e:
        result["error"] = f"Route calculation error: {str(e)}"

    return result


def haversine_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in meters using Haversine formula."""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def calculate_hazard_exposure(routes, hazard_locations, radius_m=100):
    """
    Calculate hazard exposure for each route.

    For each route, count how many known hazards are within `radius_m` meters
    of the route path.

    Args:
        routes: List of route dicts with 'coordinates'
        hazard_locations: List of hazard dicts with 'latitude', 'longitude', 'severity'
        radius_m: Search radius in meters

    Returns:
        Updated routes list with hazard_count and hazard_score
    """
    if not hazard_locations:
        return routes

    severity_weights = {
        "Critical": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    for route in routes:
        hazard_count = 0
        hazard_score = 0.0
        coords = route.get("coordinates", [])

        # Sample route points (check every few points for performance)
        step = max(1, len(coords) // 100)  # Check ~100 points along route
        sampled_coords = coords[::step]

        for hazard in hazard_locations:
            h_lat = hazard.get("latitude", 0)
            h_lng = hazard.get("longitude", 0)
            if h_lat == 0 and h_lng == 0:
                continue

            # Check if hazard is near any point on the route
            for coord in sampled_coords:
                dist = haversine_distance(coord[0], coord[1], h_lat, h_lng)
                if dist <= radius_m:
                    hazard_count += 1
                    weight = severity_weights.get(hazard.get("severity", "Medium"), 2)
                    hazard_score += weight
                    break  # Count each hazard only once per route

        route["hazard_count"] = hazard_count
        route["hazard_score"] = round(hazard_score, 1)

    return routes


def find_safest_route(start_name, end_name, hazard_locations, radius_m=100, city="Multan"):
    """
    Complete workflow: geocode locations, find routes, calculate hazard exposure,
    and recommend the safest route.

    Args:
        start_name: Starting location name/address
        end_name: Destination name/address
        hazard_locations: List of known hazard locations
        radius_m: Hazard search radius in meters
        city: Active city region context (defaults to Multan)

    Returns:
        dict with full results including routes, recommendations, map data
    """
    result = {
        "success": False,
        "start": None,
        "end": None,
        "routes": [],
        "recommended_index": 0,
        "error": None
    }

    # Geocode start
    start_geo = geocode_location(start_name, city=city)
    if not start_geo:
        result["error"] = f"Could not find location: '{start_name}'. Try a more specific address or landmark."
        return result
    result["start"] = start_geo

    # Geocode end
    end_geo = geocode_location(end_name, city=city)
    if not end_geo:
        result["error"] = f"Could not find location: '{end_name}'. Try a more specific address or landmark."
        return result
    result["end"] = end_geo

    # Get routes
    route_result = get_routes(
        start_geo["lat"], start_geo["lng"],
        end_geo["lat"], end_geo["lng"],
        alternatives=True
    )

    if not route_result["success"]:
        result["error"] = route_result["error"]
        return result

    routes = route_result["routes"]

    # Calculate hazard exposure
    routes = calculate_hazard_exposure(routes, hazard_locations, radius_m)

    # Recommend a route: safest among routes that are not much longer than the shortest.
    # (Previously hazard_score*1000 + km, which happily picked huge detours to dodge one crack.)
    if routes:
        shortest_km = min(r["distance_km"] for r in routes) or 0.001
        fastest_min = min(r["duration_min"] for r in routes) or 0.001
        for r in routes:
            r["extra_km"] = round(r["distance_km"] - shortest_km, 2)
            r["extra_pct"] = round((r["distance_km"] / shortest_km - 1) * 100)
            r["acceptable"] = (r["distance_km"] <= shortest_km * MAX_DETOUR_RATIO and
                               r["duration_min"] <= fastest_min * MAX_DETOUR_RATIO)

        candidates = [i for i, r in enumerate(routes) if r["acceptable"]] or list(range(len(routes)))
        # Each extra km must "buy" at least KM_PER_HAZARD_POINT of risk reduction to be worth it
        result["recommended_index"] = min(
            candidates,
            key=lambda i: (routes[i]["hazard_score"] + routes[i]["extra_km"] / KM_PER_HAZARD_POINT,
                           routes[i]["distance_km"]))

    result["success"] = True
    result["routes"] = routes
    return result


def google_maps_url(route, max_waypoints=8):
    """Google Maps directions link that follows the same path (start, ~8 waypoints, end)."""
    coords = route.get("coordinates", [])
    if len(coords) < 2:
        return "https://www.google.com/maps"
    o, d = coords[0], coords[-1]
    inner = coords[1:-1]
    step = max(1, len(inner) // (max_waypoints + 1))
    wps = inner[step::step][:max_waypoints]
    url = (f"https://www.google.com/maps/dir/?api=1&travelmode=driving"
           f"&origin={o[0]:.6f},{o[1]:.6f}&destination={d[0]:.6f},{d[1]:.6f}")
    if wps:
        url += "&waypoints=" + "%7C".join(f"{p[0]:.6f},{p[1]:.6f}" for p in wps)
    return url
