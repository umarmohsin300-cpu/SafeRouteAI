"""
SafeRoute AI - Image helpers for report photos.
Photos are stored in data/uploads/ with a unique name; the database keeps a path
relative to the project folder, so moving the project doesn't break the links.
"""

import os
import io
import base64
import uuid
from datetime import datetime
from PIL import Image

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(PROJECT_DIR, "data", "uploads")


def save_uploaded_photo(uploaded_file, prefix="report"):
    """Save a Streamlit UploadedFile with a unique name. Returns the relative path to store."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(uploaded_file.name)[1].lower() or ".jpg"
    name = f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}{ext}"
    with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    return os.path.join("data", "uploads", name).replace("\\", "/")


def resolve_image_path(stored_path):
    """
    Turn whatever is stored in the DB into a real file path, or None.
    Handles new relative paths, and old absolute paths from before the project was moved.
    """
    if not stored_path:
        return None
    p = str(stored_path)
    candidates = [
        p,
        os.path.join(PROJECT_DIR, p),
        os.path.join(UPLOAD_DIR, os.path.basename(p.replace("\\", "/"))),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def thumbnail_data_uri(stored_path, max_px=320):
    """Small base64 JPEG for embedding in map popups. Returns None if the photo is missing."""
    path = resolve_image_path(stored_path)
    if not path:
        return None
    try:
        img = Image.open(path)
        img.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=75)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None
