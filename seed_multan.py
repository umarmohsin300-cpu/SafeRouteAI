"""
SafeRoute AI - Seed Multan Road Hazards & Streetlights
"""

import database as db

def seed_multan():
    print("Seeding Multan road hazards...")

    hazards = [
        # Bosan Road & Gulgasht
        {"type": "Pothole", "location": "Bosan Road near Chungi No 9, Multan", "lat": 30.2090, "lng": 71.4720, "desc": "Large pothole in middle lane near traffic signal", "severity": "Critical", "source": "AI Detection"},
        {"type": "Road Crack", "location": "Bosan Road near Mall of Multan", "lat": 30.2420, "lng": 71.4840, "desc": "Longitudinal cracks across road section", "severity": "Medium", "source": "Manual"},
        {"type": "Pothole", "location": "Gulgasht Colony Gol Bagh Road, Multan", "lat": 30.2285, "lng": 71.4750, "desc": "Deep crater near commercial area", "severity": "High", "source": "Manual"},
        {"type": "Road Crack", "location": "Bosan Road near BZU Main Gate, Multan", "lat": 30.2645, "lng": 71.5075, "desc": "Alligator cracking after road works", "severity": "Medium", "source": "AI Detection"},

        # Abdali Road & Cantt
        {"type": "Pothole", "location": "Abdali Road near Nawan Shehr Chowk, Multan", "lat": 30.1940, "lng": 71.4640, "desc": "Sunken manhole cover causing severe bump", "severity": "Critical", "source": "AI Detection"},
        {"type": "Road Crack", "location": "Multan Cantt near Mall Road", "lat": 30.1860, "lng": 71.4320, "desc": "Surface asphalt fatigue and cracks", "severity": "Low", "source": "Manual"},
        {"type": "Pothole", "location": "Nishtar Road near Nishtar Hospital, Multan", "lat": 30.2020, "lng": 71.4455, "desc": "Pothole causing traffic obstruction outside emergency", "severity": "Critical", "source": "Manual"},

        # Kutchery Chowk & LMQ Road
        {"type": "Pothole", "location": "LMQ Road near Kutchery Chowk, Multan", "lat": 30.2088, "lng": 71.4650, "desc": "Damaged asphalt patch near court entrance", "severity": "High", "source": "AI Detection"},
        {"type": "Road Crack", "location": "Old Bahawalpur Road near SP Chowk, Multan", "lat": 30.1955, "lng": 71.4595, "desc": "Transverse cracks extending 8 meters", "severity": "Medium", "source": "AI Detection"},
        {"type": "Pothole", "location": "Khanewal Road near Chungi No 6, Multan", "lat": 30.2030, "lng": 71.4880, "desc": "Deep potholes on slow lane", "severity": "High", "source": "Manual"}
    ]

    for h in hazards:
        db.insert_hazard_report(
            hazard_type=h["type"],
            location=h["location"],
            latitude=h["lat"],
            longitude=h["lng"],
            description=h["desc"],
            severity=h["severity"],
            source=h["source"]
        )

    streetlights = [
        {"status": "Broken / Not Working", "location": "Bosan Road near BZU Campus, Multan", "lat": 30.2580, "lng": 71.5020, "desc": "4 consecutive poles dark, dangerous for student bikers", "severity": "Critical"},
        {"status": "Dim / Poorly Illuminated", "location": "Abdali Road near SP Chowk, Multan", "lat": 30.1950, "lng": 71.4610, "desc": "Very dim lighting near turn", "severity": "Medium"},
        {"status": "Broken / Not Working", "location": "Nishtar Road near Medical College, Multan", "lat": 30.2032, "lng": 71.4430, "desc": "Completely blacked out section", "severity": "High"},
        {"status": "Flickering", "location": "Gulgasht Commercial Market, Multan", "lat": 30.2290, "lng": 71.4730, "desc": "Rapid flickering light pole", "severity": "Low"}
    ]

    for s in streetlights:
        db.insert_streetlight_report(
            status=s["status"],
            location=s["location"],
            latitude=s["lat"],
            longitude=s["lng"],
            description=s["desc"],
            severity=s["severity"]
        )

    print("Multan demo hazards & streetlights seeded successfully!")

if __name__ == "__main__":
    seed_multan()
