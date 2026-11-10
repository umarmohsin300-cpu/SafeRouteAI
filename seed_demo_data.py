"""
SafeRoute AI - Seed Initial Demo Data
Populates the database with realistic road hazards and streetlight issues
across major routes in Lahore, Pakistan.
"""

import database as db

def seed_data():
    print("Seeding initial road hazards for Lahore, Pakistan...")

    # Potholes and Cracks along major roads
    hazards = [
        # Mall Road & Lower Mall
        {"type": "Pothole", "location": "Mall Road near Charing Cross, Lahore", "lat": 31.5546, "lng": 74.3262, "desc": "Deep pothole on right lane causing vehicle slowdown", "severity": "Critical", "source": "Manual"},
        {"type": "Road Crack", "location": "Mall Road near Lahore Museum", "lat": 31.5682, "lng": 74.3095, "desc": "Longitudinal cracks expanding across lanes", "severity": "Medium", "source": "AI Detection"},
        
        # Gulberg & Main Boulevard
        {"type": "Pothole", "location": "Main Boulevard Gulberg near Siddique Trade Center", "lat": 31.5204, "lng": 74.3487, "desc": "Multiple potholes near intersection", "severity": "High", "source": "AI Detection"},
        {"type": "Road Crack", "location": "Gulberg III near Liberty Roundabout", "lat": 31.5110, "lng": 74.3440, "desc": "Alligator cracking after monsoon rain", "severity": "Medium", "source": "Manual"},
        {"type": "Pothole", "location": "Zafar Ali Road near Gulberg", "lat": 31.5350, "lng": 74.3460, "desc": "Pavement depression near drainage cover", "severity": "High", "source": "Manual"},

        # Ferozepur Road
        {"type": "Pothole", "location": "Ferozepur Road near Kalma Chowk Underpass", "lat": 31.5035, "lng": 74.3318, "desc": "Sharp pothole edge on service road", "severity": "Critical", "source": "AI Detection"},
        {"type": "Road Crack", "location": "Ferozepur Road near Ichhra", "lat": 31.5270, "lng": 74.3210, "desc": "Transverse cracks extending 10m", "severity": "Medium", "source": "AI Detection"},

        # Canal Road
        {"type": "Road Crack", "location": "Canal Bank Road near Muslim Town Flyover", "lat": 31.5165, "lng": 74.3180, "desc": "Severe road fatigue and cracks", "severity": "High", "source": "AI Detection"},
        {"type": "Pothole", "location": "Canal Bank Road near Campus Bridge", "lat": 31.5030, "lng": 74.3015, "desc": "Large pothole on entry ramp", "severity": "Critical", "source": "Manual"},

        # Johar Town & Faisal Town
        {"type": "Pothole", "location": "Shaukat Khanum Chowk, Johar Town", "lat": 31.4682, "lng": 74.2755, "desc": "Hazardous crater near u-turn", "severity": "High", "source": "Manual"},
        {"type": "Road Crack", "location": "Faisal Town Main Boulevard", "lat": 31.4880, "lng": 74.3050, "desc": "Surface erosion and fine cracks", "severity": "Low", "source": "AI Detection"},

        # DHA Phase 3 & 5
        {"type": "Pothole", "location": "DHA Phase 3 Commercial Area", "lat": 31.4780, "lng": 74.3790, "desc": "Damaged asphalt patch", "severity": "Medium", "source": "Manual"},
        {"type": "Road Crack", "location": "Ghazi Road near Ring Road Interchange", "lat": 31.4710, "lng": 74.4020, "desc": "Stress fractures across road shoulder", "severity": "Low", "source": "AI Detection"}
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

    # Streetlight Reports
    streetlights = [
        {"status": "Broken / Not Working", "location": "Canal Road near Doctors Hospital", "lat": 31.4980, "lng": 74.2810, "desc": "3 consecutive poles not turning on, dark area", "severity": "Critical"},
        {"status": "Dim / Poorly Illuminated", "location": "Jail Road near Services Hospital", "lat": 31.5380, "lng": 74.3360, "desc": "Yellow sodium bulb very dim, poor visibility", "severity": "Medium"},
        {"status": "Broken / Not Working", "location": "Lawrence Road near Bagh-e-Jinnah", "lat": 31.5520, "lng": 74.3310, "desc": "Completely blacked out section along park wall", "severity": "High"},
        {"status": "Flickering", "location": "MM Alam Road near Mini Market", "lat": 31.5160, "lng": 74.3540, "desc": "Flickering rapidly, distracting oncoming drivers", "severity": "Medium"},
        {"status": "Broken / Not Working", "location": "Band Road near Babu Sabu", "lat": 31.5450, "lng": 74.2590, "desc": "Damaged wire connection, unlit stretch", "severity": "Critical"}
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

    print("Demo data seeded successfully!")

if __name__ == "__main__":
    seed_data()
