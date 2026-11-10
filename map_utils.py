"""
SafeRoute AI - Map Utilities
Creates interactive Folium maps for hazard visualization.
"""

import folium
from image_utils import thumbnail_data_uri
from folium.plugins import MarkerCluster

# Default center: Multan, Pakistan
DEFAULT_LAT = 30.1984
DEFAULT_LNG = 71.4687
DEFAULT_ZOOM = 13


def get_marker_color(hazard_type, category=""):
    """Get marker color based on hazard type."""
    hazard_lower = hazard_type.lower()
    cat_lower = category.lower()

    if "pothole" in hazard_lower or "d40" in hazard_lower:
        return "red"
    elif "crack" in hazard_lower or "d00" in hazard_lower or "d10" in hazard_lower or "d20" in hazard_lower:
        return "orange"
    elif "streetlight" in cat_lower or "broken" in hazard_lower or "non-functional" in hazard_lower or "dim" in hazard_lower or "poorly" in hazard_lower:
        return "cadetblue"
    else:
        return "gray"


def get_marker_icon(hazard_type, category=""):
    """Get marker icon based on hazard type."""
    hazard_lower = hazard_type.lower()
    cat_lower = category.lower()

    if "pothole" in hazard_lower or "d40" in hazard_lower:
        return "exclamation-circle"
    elif "crack" in hazard_lower or "d00" in hazard_lower or "d10" in hazard_lower or "d20" in hazard_lower:
        return "road"
    elif "streetlight" in cat_lower or "broken" in hazard_lower or "non-functional" in hazard_lower:
        return "lightbulb-o"
    else:
        return "warning"


def create_hazard_map(locations, center_lat=None, center_lng=None, zoom=None):
    """
    Create an interactive Folium map with hazard markers.

    Args:
        locations: List of dicts with lat, lng, hazard_type, severity, etc.
        center_lat: Center latitude (defaults to Lahore)
        center_lng: Center longitude (defaults to Lahore)
        zoom: Initial zoom level

    Returns:
        folium.Map object
    """
    lat = center_lat or DEFAULT_LAT
    lng = center_lng or DEFAULT_LNG
    z = zoom or DEFAULT_ZOOM

    # Create base map with clean OpenStreetMap tiles
    m = folium.Map(
        location=[lat, lng],
        zoom_start=z,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # Create marker cluster for better performance
    marker_cluster = MarkerCluster(name="Hazard Reports").add_to(m)

    # Add markers
    for loc in locations:
        if loc.get("latitude", 0) == 0 and loc.get("longitude", 0) == 0:
            continue

        hazard_type = loc.get("hazard_type", "Unknown")
        category = loc.get("category", "")
        severity = loc.get("severity", "Medium")
        location_name = loc.get("location", "Unknown Location")
        description = loc.get("description", "")
        timestamp = loc.get("timestamp", "")
        photo_uri = thumbnail_data_uri(loc.get("image_path"))
        photo_html = (f'<img src="{photo_uri}" style="width:100%;max-width:280px;border-radius:6px;'
                      f'margin-top:8px;display:block;">' if photo_uri else "")

        color = get_marker_color(hazard_type, category)
        icon_name = get_marker_icon(hazard_type, category)

        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="color: #0a1628; margin: 0 0 8px 0; border-bottom: 2px solid #00d4ff;">
                ⚠️ {hazard_type}
            </h4>
            <table style="width: 100%; font-size: 13px;">
                <tr>
                    <td><b>📍 Location:</b></td>
                    <td>{location_name}</td>
                </tr>
                <tr>
                    <td><b>⚡ Severity:</b></td>
                    <td><span style="color: {'red' if severity == 'Critical' else 'orange' if severity == 'High' else '#333'}; font-weight: bold;">{severity}</span></td>
                </tr>
                <tr>
                    <td><b>📂 Source:</b></td>
                    <td>{category}</td>
                </tr>
                {'<tr><td><b>📝 Note:</b></td><td>' + description + '</td></tr>' if description else ''}
                <tr>
                    <td><b>🕐 Time:</b></td>
                    <td>{timestamp[:16] if timestamp else 'N/A'}</td>
                </tr>
            </table>
            {photo_html}
        </div>
        """

        folium.Marker(
            location=[loc["latitude"], loc["longitude"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{hazard_type} - {severity}" + (" 📷" if photo_uri else ""),
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
        ).add_to(marker_cluster)

    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
                background: rgba(10, 22, 40, 0.92); padding: 15px 20px;
                border-radius: 10px; border: 1px solid #00d4ff;
                font-family: Arial, sans-serif; color: white; font-size: 13px;
                box-shadow: 0 4px 15px rgba(0,212,255,0.2);">
        <h4 style="margin: 0 0 10px 0; color: #00d4ff;">🗺️ SafeRoute AI Legend</h4>
        <div style="margin: 4px 0;"><span style="color: #ff4444;">●</span> Pothole</div>
        <div style="margin: 4px 0;"><span style="color: #ff8c00;">●</span> Road Crack</div>
        <div style="margin: 4px 0;"><span style="color: #5f9ea0;">●</span> Streetlight Issue</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def create_route_map(routes_data, hazard_locations=None, recommended_index=0):
    """
    Create a map showing route alternatives with hazard overlay.

    Args:
        routes_data: List of route dicts with 'geometry', 'distance', 'duration', 'hazard_count'
        hazard_locations: Optional list of hazard location dicts

    Returns:
        folium.Map object
    """
    if not routes_data:
        return create_hazard_map([])

    # Center on the first route's midpoint
    first_route = routes_data[0]
    coords = first_route.get("coordinates", [])
    if coords:
        mid = len(coords) // 2
        center = coords[mid]
    else:
        center = [DEFAULT_LAT, DEFAULT_LNG]

    m = folium.Map(
        location=center,
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    # Draw alternatives first (thin, grey-ish), recommended route last so it sits on top
    alt_colors = ["#ff6b6b", "#ffd93d", "#6bcb77"]
    order = [i for i in range(len(routes_data)) if i != recommended_index] + [recommended_index]

    for draw_pos, i in enumerate(order):
        if i >= len(routes_data):
            continue
        route = routes_data[i]
        coords = route.get("coordinates", [])
        if not coords:
            continue

        is_rec = (i == recommended_index)
        color = "#0077ff" if is_rec else alt_colors[draw_pos % len(alt_colors)]
        label = f"Route {i + 1}" + (" (Recommended)" if is_rec else "")

        distance_km = route.get("distance_km", 0)
        duration_min = route.get("duration_min", 0)
        hazard_count = route.get("hazard_count", 0)

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=7 if is_rec else 4,
            opacity=0.95 if is_rec else 0.55,
            dash_array=None if is_rec else "8 8",
            popup=f"""
            <div style="font-family: Arial; min-width: 180px;">
                <h4 style="color: #0a1628;">{label}</h4>
                <p>📏 Distance: {distance_km:.1f} km</p>
                <p>⏱️ Duration: {duration_min:.0f} min</p>
                <p>⚠️ Nearby Hazards: {hazard_count}</p>
            </div>
            """,
            tooltip=f"{label} — {distance_km:.1f} km, {hazard_count} hazard(s)"
        ).add_to(m)

    # Start / destination markers (once, from the recommended route)
    rec_coords = routes_data[recommended_index].get("coordinates", []) if recommended_index < len(routes_data) else []
    if rec_coords:
        folium.Marker(location=rec_coords[0], popup="Start", tooltip="Start",
                      icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(m)
        folium.Marker(location=rec_coords[-1], popup="Destination", tooltip="Destination",
                      icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")).add_to(m)
        m.fit_bounds([[min(c[0] for c in rec_coords), min(c[1] for c in rec_coords)],
                      [max(c[0] for c in rec_coords), max(c[1] for c in rec_coords)]])

    # Add hazard markers if provided
    if hazard_locations:
        hazard_group = folium.FeatureGroup(name="Reported Hazards")
        for loc in hazard_locations:
            if loc.get("latitude", 0) == 0 and loc.get("longitude", 0) == 0:
                continue
            color = get_marker_color(loc.get("hazard_type", ""), loc.get("category", ""))
            folium.CircleMarker(
                location=[loc["latitude"], loc["longitude"]],
                radius=8,
                color=color,
                fill=True,
                fillOpacity=0.7,
                popup=f"{loc.get('hazard_type', 'Hazard')} - {loc.get('severity', 'N/A')}"
            ).add_to(hazard_group)
        hazard_group.add_to(m)

    folium.LayerControl().add_to(m)
    return m
