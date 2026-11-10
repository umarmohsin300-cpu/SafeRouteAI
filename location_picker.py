"""
SafeRoute AI - Location Picker
A reusable "where is it?" widget so users never have to type coordinates.

Three ways to set the location (all end up as a pin on the map):
  1. Search a place name (landmarks + OpenStreetMap search)
  2. Tap / click the exact spot on the map (the address is filled in automatically)
  3. "Use my current location" (browser GPS - needs the optional streamlit-js-eval package)
"""

import streamlit as st
import folium
from streamlit_folium import st_folium

import routing

try:
    from streamlit_js_eval import get_geolocation
    GPS_AVAILABLE = True
except ImportError:
    GPS_AVAILABLE = False


def _short_address(full_name, parts=3):
    """'Madni Chowk, Bosan Road, Multan, Punjab, 60000, Pakistan' -> first 3 parts."""
    if not full_name:
        return ""
    bits = [b.strip() for b in str(full_name).split(",") if b.strip()]
    return ", ".join(bits[:parts])


def _set_pin(state, lat, lng, name):
    state["lat"], state["lng"], state["name"] = float(lat), float(lng), name


def reset_location(key):
    """Clear a picker (e.g. after a report is submitted)."""
    st.session_state.pop(f"lp_{key}", None)


def location_picker(key, city="Multan", height=360):
    """
    Render the picker and return the chosen location, or None if nothing is picked yet.

    Returns: {"lat": float, "lng": float, "name": str}
    """
    sk = f"lp_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = {"lat": None, "lng": None, "name": "", "last_click": None,
                                "msg": "", "gps": False}
    state = st.session_state[sk]

    # ── 1. Search ──────────────────────────────────────────────
    c1, c2, c3 = st.columns([5, 1.3, 2.2] if GPS_AVAILABLE else [5, 1.3, 0.01])
    with c1:
        query = st.text_input("Search a place", key=f"{sk}_q",
                              placeholder="Search a place, e.g. Madni Chowk, Nishtar Hospital, Bosan Road",
                              label_visibility="collapsed")
    with c2:
        find = st.button("🔍 Find", key=f"{sk}_find", use_container_width=True)
    with c3:
        if GPS_AVAILABLE and st.button("📍 My location", key=f"{sk}_gpsbtn", use_container_width=True):
            state["gps"] = True

    if find and query.strip():
        geo = routing.geocode_location(query, city=city)
        if geo and not geo.get("approximate"):
            label = query.strip() if geo.get("source") == "nominatim" else geo["display_name"]
            _set_pin(state, geo["lat"], geo["lng"], label)
            state["msg"] = "found"
        else:
            state["msg"] = "notfound"

    # ── 3. GPS (optional) ──────────────────────────────────────
    if GPS_AVAILABLE and state.get("gps"):
        loc = get_geolocation(component_key=f"{sk}_gps")
        if loc and isinstance(loc, dict) and loc.get("coords"):
            lat, lng = loc["coords"]["latitude"], loc["coords"]["longitude"]
            _set_pin(state, lat, lng, _short_address(routing.reverse_geocode(lat, lng)))
            state["gps"], state["msg"] = False, "gps"
            st.rerun()
        elif loc and isinstance(loc, dict) and loc.get("error"):
            state["gps"], state["msg"] = False, "gpsfail"
        else:
            st.caption("📡 Getting your location… allow location access in the browser if asked.")

    if state["msg"] == "notfound":
        st.warning("Couldn't find that place automatically — just tap the exact spot on the map below.")
    elif state["msg"] == "gpsfail":
        st.warning("Location access was blocked or unavailable — search or tap the map instead.")

    # ── 2. Map (tap to place / move the pin) ───────────────────
    has_pin = state["lat"] is not None
    if has_pin:
        center, zoom = [state["lat"], state["lng"]], 17
    else:
        center = [float(st.session_state.get("city_lat", 30.1984)),
                  float(st.session_state.get("city_lng", 71.4687))]
        zoom = 13

    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
    if has_pin:
        folium.Marker([state["lat"], state["lng"]], tooltip=state["name"] or "Selected location",
                      icon=folium.Icon(color="red", icon="map-marker", prefix="fa")).add_to(m)

    out = st_folium(m, key=f"{sk}_map_{round(center[0], 4)}_{round(center[1], 4)}",
                    height=height, width=None, returned_objects=["last_clicked"])
    lc = out.get("last_clicked") if out else None
    if lc:
        pt = (round(lc["lat"], 6), round(lc["lng"], 6))
        if pt != state["last_click"]:
            state["last_click"] = pt
            _set_pin(state, pt[0], pt[1], _short_address(routing.reverse_geocode(pt[0], pt[1])))
            state["msg"] = "clicked"
            st.rerun()

    if has_pin:
        st.success(f"📍 **Selected:** {state['name'] or 'Pinned location'}  "
                   f"— tap the map again to adjust the pin.")
        return {"lat": state["lat"], "lng": state["lng"], "name": state["name"]}

    st.caption("👆 Search a place, or tap the exact spot on the map to drop a pin.")
    return None
