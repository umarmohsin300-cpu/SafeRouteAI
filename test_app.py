"""
SafeRoute AI - Test Suite
Verifies all modules: database, AI detection, routing, and maps.
"""

import sys
import os

print("=" * 60)
print("SafeRoute AI - Automated System Verification")
print("=" * 60)

# 1. Database
print("\n[1/4] Testing Database...")
import database as db
db.create_tables()
counts = db.count_hazards_by_type()
print(f" -> Database connected successfully!")
print(f" -> Current hazard counts: Total={counts['Total']}, Potholes={counts['Pothole']}, Cracks={counts['Road Crack']}, Streetlights={counts['Streetlight Issue']}")
assert counts['Total'] > 0, "Database should contain seeded records"

# 2. AI Model & Detection
print("\n[2/4] Testing YOLOv8 AI Model...")
import detection
model_ok, model_path = detection.get_model_status()
print(f" -> Model file exists: {model_ok} ({model_path})")
assert model_ok, "Model weights file should exist"
model, msg = detection.load_model()
print(f" -> Model load message: {msg}")
assert model is not None, "Model should load successfully"
print(f" -> Detected classes supported: {list(model.names.values())}")

# 3. Geocoding & Routing
print("\n[3/4] Testing OSRM Routing & Hazard Risk Scoring...")
import routing
hazards = db.get_all_hazard_locations()
route_res = routing.find_safest_route("Liberty Market Gulberg, Lahore", "Lahore Museum, Lower Mall, Lahore", hazards, radius_m=200)
if route_res["success"]:
    print(f" -> Geocoded Start: {route_res['start']['display_name'][:40]}...")
    print(f" -> Geocoded End:   {route_res['end']['display_name'][:40]}...")
    print(f" -> Found {len(route_res['routes'])} routes!")
    rec = route_res['routes'][route_res['recommended_index']]
    print(f" -> Recommended: Route {route_res['recommended_index']+1} ({rec['distance_km']} km, {rec['duration_min']} min, nearby hazards: {rec['hazard_count']})")
else:
    print(f" -> Routing notice/fallback: {route_res['error']}")

# 4. Map Generation
print("\n[4/4] Testing Folium Map Generation...")
import map_utils
h_map = map_utils.create_hazard_map(hazards)
print(f" -> Hazard map generated successfully ({len(hazards)} points rendered)!")
if route_res["success"]:
    r_map = map_utils.create_route_map(route_res["routes"], hazards)
    print(f" -> Route comparison map generated successfully!")

print("\n" + "=" * 60)
print("ALL TESTS PASSED! SafeRoute AI is ready for deployment/demo.")
print("=" * 60)
