"""
SafeRoute AI - Database Module
Handles all SQLite database operations for hazard reports,
AI detection results, and streetlight reports.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "saferoute.db")


def get_connection():
    """Get a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all required database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Hazard reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hazard_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hazard_type TEXT NOT NULL,
            location TEXT,
            latitude REAL,
            longitude REAL,
            description TEXT,
            severity TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            source TEXT DEFAULT 'Manual',
            image_path TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    # AI detection results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            hazard_type TEXT NOT NULL,
            confidence REAL,
            bbox_x1 REAL,
            bbox_y1 REAL,
            bbox_x2 REAL,
            bbox_y2 REAL,
            location TEXT,
            latitude REAL,
            longitude REAL,
            severity TEXT DEFAULT 'Medium',
            timestamp TEXT NOT NULL
        )
    """)

    # Streetlight reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streetlight_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            description TEXT,
            severity TEXT DEFAULT 'Medium',
            report_status TEXT DEFAULT 'Open',
            image_path TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---- Insert Functions ----

def insert_hazard_report(hazard_type, location="", latitude=0.0, longitude=0.0,
                         description="", severity="Medium", source="Manual",
                         image_path=""):
    """Insert a new hazard report."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO hazard_reports
        (hazard_type, location, latitude, longitude, description,
         severity, source, image_path, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (hazard_type, location, latitude, longitude, description,
          severity, source, image_path, datetime.now().isoformat()))
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id


def insert_ai_detection(image_path, hazard_type, confidence,
                        bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                        location="", latitude=0.0, longitude=0.0,
                        severity="Medium"):
    """Insert an AI detection result."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ai_detections
        (image_path, hazard_type, confidence, bbox_x1, bbox_y1,
         bbox_x2, bbox_y2, location, latitude, longitude, severity, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_path, hazard_type, confidence, bbox_x1, bbox_y1,
          bbox_x2, bbox_y2, location, latitude, longitude, severity,
          datetime.now().isoformat()))
    conn.commit()
    detection_id = cursor.lastrowid
    conn.close()
    return detection_id


def insert_streetlight_report(status, location, latitude=0.0, longitude=0.0,
                              description="", severity="Medium", image_path=""):
    """Insert a new streetlight report."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO streetlight_reports
        (status, location, latitude, longitude, description,
         severity, image_path, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (status, location, latitude, longitude, description,
          severity, image_path, datetime.now().isoformat()))
    conn.commit()
    report_id = cursor.lastrowid
    conn.close()
    return report_id


# ---- Retrieve Functions ----

def get_all_hazard_reports():
    """Get all hazard reports."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hazard_reports ORDER BY timestamp DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_ai_detections():
    """Get all AI detection results."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_detections ORDER BY timestamp DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_streetlight_reports():
    """Get all streetlight reports."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM streetlight_reports ORDER BY timestamp DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_recent_reports(limit=10):
    """Get recent reports from all tables combined."""
    conn = get_connection()
    cursor = conn.cursor()

    reports = []

    cursor.execute(
        "SELECT id, hazard_type as type, location, severity, timestamp, 'Hazard' as category FROM hazard_reports ORDER BY timestamp DESC LIMIT ?",
        (limit,))
    reports.extend([dict(row) for row in cursor.fetchall()])

    cursor.execute(
        "SELECT id, hazard_type as type, location, severity, timestamp, 'AI Detection' as category FROM ai_detections ORDER BY timestamp DESC LIMIT ?",
        (limit,))
    reports.extend([dict(row) for row in cursor.fetchall()])

    cursor.execute(
        "SELECT id, status as type, location, severity, timestamp, 'Streetlight' as category FROM streetlight_reports ORDER BY timestamp DESC LIMIT ?",
        (limit,))
    reports.extend([dict(row) for row in cursor.fetchall()])

    # Sort by timestamp descending and limit
    reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    conn.close()
    return reports[:limit]


# ---- Count Functions ----

def count_hazards_by_type():
    """Count hazards grouped by type across all tables."""
    conn = get_connection()
    cursor = conn.cursor()

    counts = {
        "Pothole": 0,
        "Road Crack": 0,
        "Streetlight Issue": 0,
        "Critical": 0,
        "Total": 0
    }

    # Count from hazard_reports
    cursor.execute("SELECT hazard_type, COUNT(*) as cnt FROM hazard_reports GROUP BY hazard_type")
    for row in cursor.fetchall():
        row = dict(row)
        htype = row["hazard_type"]
        cnt = row["cnt"]
        counts["Total"] += cnt
        if "pothole" in htype.lower():
            counts["Pothole"] += cnt
        elif "crack" in htype.lower():
            counts["Road Crack"] += cnt

    # Count from ai_detections
    cursor.execute("SELECT hazard_type, COUNT(*) as cnt FROM ai_detections GROUP BY hazard_type")
    for row in cursor.fetchall():
        row = dict(row)
        htype = row["hazard_type"]
        cnt = row["cnt"]
        counts["Total"] += cnt
        if "pothole" in htype.lower() or htype.lower() == "d40":
            counts["Pothole"] += cnt
        elif "crack" in htype.lower() or htype.lower().startswith("d0") or htype.lower().startswith("d1") or htype.lower().startswith("d2"):
            counts["Road Crack"] += cnt

    # Count streetlights
    cursor.execute("SELECT COUNT(*) as cnt FROM streetlight_reports")
    sl_count = dict(cursor.fetchone())["cnt"]
    counts["Streetlight Issue"] = sl_count
    counts["Total"] += sl_count

    # Count critical
    cursor.execute("SELECT COUNT(*) as cnt FROM hazard_reports WHERE severity = 'Critical'")
    counts["Critical"] += dict(cursor.fetchone())["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM ai_detections WHERE severity = 'Critical'")
    counts["Critical"] += dict(cursor.fetchone())["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM streetlight_reports WHERE severity = 'Critical'")
    counts["Critical"] += dict(cursor.fetchone())["cnt"]

    conn.close()
    return counts


def get_all_hazard_locations():
    """Get all hazard locations with type for map display."""
    conn = get_connection()
    cursor = conn.cursor()
    locations = []

    cursor.execute("""
        SELECT latitude, longitude, hazard_type, severity, location, description, timestamp, image_path
        FROM hazard_reports WHERE latitude != 0 AND longitude != 0
    """)
    for row in cursor.fetchall():
        r = dict(row)
        r["category"] = "hazard"
        locations.append(r)

    cursor.execute("""
        SELECT latitude, longitude, hazard_type, severity, location,
               '' as description, timestamp, '' as image_path
        FROM ai_detections WHERE latitude != 0 AND longitude != 0
    """)
    for row in cursor.fetchall():
        r = dict(row)
        r["category"] = "ai_detection"
        locations.append(r)

    cursor.execute("""
        SELECT latitude, longitude, status as hazard_type, severity,
               location, description, timestamp, image_path
        FROM streetlight_reports WHERE latitude != 0 AND longitude != 0
    """)
    for row in cursor.fetchall():
        r = dict(row)
        r["category"] = "streetlight"
        locations.append(r)

    conn.close()
    return locations


def update_report_status(table, report_id, new_status):
    """Update the status of a report."""
    conn = get_connection()
    cursor = conn.cursor()
    if table == "hazard_reports":
        cursor.execute("UPDATE hazard_reports SET status = ? WHERE id = ?",
                       (new_status, report_id))
    elif table == "streetlight_reports":
        cursor.execute("UPDATE streetlight_reports SET report_status = ? WHERE id = ?",
                       (new_status, report_id))
    conn.commit()
    conn.close()


# Initialize tables on import
create_tables()
