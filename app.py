"""
SafeRoute AI - Main Application
AI-Powered Road Hazards & Streetlight Safety Mapping

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
from PIL import Image
import io

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))

import database as db
import routing
import negotiator
from map_utils import create_hazard_map, create_route_map, DEFAULT_LAT, DEFAULT_LNG
from location_picker import location_picker, reset_location
from image_utils import save_uploaded_photo, resolve_image_path

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG & GLOBAL STYLES
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SafeRoute AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional dark navy + cyan theme
st.markdown("""
<style>
    /* ── Main background ── */
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #0f2037 40%, #132a45 100%);
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #0d1b30 100%);
        border-right: 1px solid #00d4ff33;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #00d4ff !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: #b0c4de !important;
    }
    section[data-testid="stSidebar"] .stRadio label span {
        color: #b0c4de !important;
    }

    /* ── Headers ── */
    h1, h2, h3 { color: #e0f0ff !important; }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0d1f3c 0%, #132d4f 100%);
        border: 1px solid #00d4ff33;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.08);
    }
    div[data-testid="stMetric"] label {
        color: #6ec8e4 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
        color: #0a1628 !important;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #33e0ff 0%, #00b8e6 100%);
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
        transform: translateY(-1px);
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #0d1f3c;
        border: 1px solid #00d4ff33;
        border-radius: 8px 8px 0 0;
        color: #6ec8e4;
        font-weight: 600;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4ff22 0%, #00d4ff11 100%);
        border-color: #00d4ff;
        color: #00d4ff !important;
    }

    /* ── Input fields ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: #0d1f3c !important;
        border: 1px solid #00d4ff33 !important;
        color: #e0f0ff !important;
        border-radius: 8px !important;
    }

    /* ── Cards / containers ── */
    .css-card {
        background: linear-gradient(135deg, #0d1f3c 0%, #132d4f 100%);
        border: 1px solid #00d4ff22;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: #0d1f3c;
        border: 1px solid #00d4ff33;
        border-radius: 8px;
        color: #00d4ff !important;
    }

    /* ── Divider styling ── */
    hr { border-color: #00d4ff22 !important; }

    /* ── Success / warning / error boxes ── */
    .stAlert {
        border-radius: 10px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0a1628; }
    ::-webkit-scrollbar-thumb { background: #00d4ff44; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #00d4ff88; }

    /* ── Selectbox text ── */
    div[data-baseweb="select"] > div {
        background: #0d1f3c !important;
        border-color: #00d4ff33 !important;
        color: #e0f0ff !important;
    }

    /* ── File uploader ── */
    section[data-testid="stFileUploader"] {
        border: 2px dashed #00d4ff44;
        border-radius: 12px;
        padding: 10px;
    }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, #0d2240 0%, #0a3055 50%, #0d2240 100%);
        border: 1px solid #00d4ff33;
        border-radius: 16px;
        padding: 30px 40px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
    }
    .hero-banner h1 {
        background: linear-gradient(135deg, #00d4ff, #00ff88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        margin-bottom: 8px !important;
    }
    .hero-banner p {
        color: #6ec8e4;
        font-size: 1.1rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 1.8rem; margin: 0;">🛡️ SafeRoute AI</h1>
        <p style="color: #6ec8e4; font-size: 0.9rem; margin: 4px 0 0 0;">
            Smarter Roads. Safer Journeys.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    selected_city = st.selectbox(
        "🏙️ Active City / Region",
        ["Multan", "Lahore", "Islamabad", "Karachi", "All Pakistan"],
        index=0
    )

    # City coordinates
    CITY_CENTERS = {
        "Multan": (30.1984, 71.4687),
        "Lahore": (31.5204, 74.3587),
        "Islamabad": (33.6844, 73.0479),
        "Karachi": (24.8607, 67.0011),
        "All Pakistan": (30.3753, 69.3451)
    }
    cur_lat, cur_lng = CITY_CENTERS.get(selected_city, (30.1984, 71.4687))
    st.session_state.active_city = selected_city
    st.session_state.city_lat = cur_lat
    st.session_state.city_lng = cur_lng
    active_city = selected_city

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🤖 AI Detection",
            "💡 Streetlight Report",
            "🗺️ Hazard Map",
            "🧭 Safe Route",
            "🤝 AI Negotiator"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    # Quick stats in sidebar
    counts = db.count_hazards_by_type()
    st.markdown("### 📈 Quick Stats")
    st.caption(f"🔴 Potholes: **{counts['Pothole']}**")
    st.caption(f"🟠 Road Cracks: **{counts['Road Crack']}**")
    st.caption(f"🟡 Streetlights: **{counts['Streetlight Issue']}**")
    st.caption(f"⚠️ Total Reports: **{counts['Total']}**")

    st.divider()
    st.caption(f"© 2026 SafeRoute AI • Hackathon Project • routing v{routing.ROUTING_VERSION}")


# ─────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────

if page == "📊 Dashboard":
    # Hero banner
    st.markdown("""
    <div class="hero-banner">
        <h1>🛡️ SafeRoute AI</h1>
        <p>Smarter Roads. Safer Journeys. — AI-Powered Road Hazard Detection & Safety Mapping</p>
    </div>
    """, unsafe_allow_html=True)

    # Metric cards
    counts = db.count_hazards_by_type()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Hazards", counts["Total"])
    with col2:
        st.metric("Potholes", counts["Pothole"])
    with col3:
        st.metric("Road Cracks", counts["Road Crack"])
    with col4:
        st.metric("Streetlight Issues", counts["Streetlight Issue"])
    with col5:
        st.metric("⚠️ Critical", counts["Critical"])

    st.divider()

    # Charts and recent reports
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📊 Hazard Distribution")
        chart_data = {
            "Category": ["Potholes", "Road Cracks", "Streetlight Issues"],
            "Count": [counts["Pothole"], counts["Road Crack"], counts["Streetlight Issue"]]
        }
        df_chart = pd.DataFrame(chart_data)

        if df_chart["Count"].sum() > 0:
            st.bar_chart(df_chart.set_index("Category"), color="#00d4ff")
        else:
            st.info("📭 No hazards reported yet. Start by using AI Detection or filing a Streetlight Report!")

    with col_right:
        st.markdown("### 🕐 Recent Reports")
        recent = db.get_recent_reports(limit=8)
        if recent:
            for r in recent:
                severity_color = "🔴" if r.get("severity") == "Critical" else "🟠" if r.get("severity") == "High" else "🟡" if r.get("severity") == "Medium" else "🟢"
                ts = r.get("timestamp", "")[:16]
                st.markdown(
                    f"{severity_color} **{r.get('type', 'Unknown')}** — "
                    f"{r.get('location', 'N/A')[:30]}  \n"
                    f"<small style='color:#6ec8e4;'>_{r.get('category', '')} • {ts}_</small>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No reports yet.")

    st.divider()

    # Road Safety Overview
    st.markdown("### 🛣️ Road Safety Overview")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        <div class="css-card">
            <h4 style="color:#00d4ff;">🤖 AI Detection</h4>
            <p style="color:#b0c4de;">Upload road images to automatically detect potholes, cracks, and damage using computer vision.</p>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="css-card">
            <h4 style="color:#00d4ff;">💡 Streetlight Reports</h4>
            <p style="color:#b0c4de;">Report broken or dim streetlights to help improve nighttime road safety in your area.</p>
        </div>
        """, unsafe_allow_html=True)
    with col_c:
        st.markdown("""
        <div class="css-card">
            <h4 style="color:#00d4ff;">🧭 Smart Routing</h4>
            <p style="color:#b0c4de;">Get route recommendations that consider known hazards to help you travel safer.</p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PAGE: AI DETECTION
# ─────────────────────────────────────────────────────────────

elif page == "🤖 AI Detection":
    st.markdown("## 🤖 AI Road Damage Detection")
    st.caption("Upload a road image to detect potholes, cracks, and pavement damage using YOLOv8 computer vision.")

    # Check model status
    from detection import get_model_status, detect_road_damage, get_download_instructions

    model_available, model_path = get_model_status()

    if model_available:
        st.success(f"✅ AI Model loaded — Ready for detection")
    else:
        st.warning("⚠️ AI Model weights not found. Please follow the setup instructions below.")
        with st.expander("📥 How to set up the AI model", expanded=True):
            st.markdown(get_download_instructions())

    st.divider()

    # Image upload with Demo Sample option
    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader(
            "📸 Upload a road image for analysis",
            type=["jpg", "jpeg", "png"],
            help="Supported formats: JPG, JPEG, PNG"
        )
    with col_up2:
        st.write("")
        st.write("")
        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_road_pothole.jpg")
        use_sample = False
        if os.path.exists(sample_path):
            use_sample = st.button("🧪 Try Sample Image", use_container_width=True)

    active_image = None
    image_source_name = ""

    if use_sample:
        st.session_state.ai_use_sample = True
        st.session_state.pop("ai_result", None)
    if uploaded_file is not None:
        st.session_state.ai_use_sample = False

    if uploaded_file is not None:
        active_image = Image.open(uploaded_file)
        image_source_name = uploaded_file.name
    elif st.session_state.get("ai_use_sample") and os.path.exists(sample_path):
        active_image = Image.open(sample_path)
        image_source_name = "sample_road_pothole.jpg"

    if active_image is not None:
        # Display uploaded image
        image = active_image

        col_img, col_result = st.columns([1, 1])

        with col_img:
            st.markdown("#### 📷 Road Image")
            st.image(image, use_container_width=True)

        # Confidence threshold
        conf_threshold = st.slider(
            "🎯 Confidence Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.25,
            step=0.05,
            help="Lower values detect more objects but may include false positives."
        )

        if st.button("🔍 Analyze Image", use_container_width=True):
            if not model_available:
                st.error("❌ Cannot run detection: Model weights not found. Please follow the setup instructions above.")
            else:
                with st.spinner("🔄 Running AI analysis..."):
                    res = detect_road_damage(image, confidence_threshold=conf_threshold)
                # keep the result so the Save step survives Streamlit reruns
                st.session_state.ai_result = res
                st.session_state.ai_result_image = image_source_name
                reset_location("ai_detection")

        result = st.session_state.get("ai_result")
        if result and st.session_state.get("ai_result_image") != image_source_name:
            result = None  # a different image is loaded now

        if result:
            if result["success"]:
                with col_result:
                    st.markdown("#### 🎯 Detection Results")
                    if result["annotated_image"] is not None:
                        st.image(result["annotated_image"], use_container_width=True)

                st.divider()

                total = result["total_hazards"]
                if total > 0:
                    st.success(f"🎯 Detected **{total}** hazard(s) in the image!")
                    det_data = [{
                        "Type": d["class_name"],
                        "Confidence": f"{d['confidence']}%",
                        "Severity": d["severity"],
                        "Category": d["hazard_category"]
                    } for d in result["detections"]]
                    st.dataframe(pd.DataFrame(det_data), use_container_width=True, hide_index=True)

                    # Save — location chosen by search / map tap
                    st.divider()
                    st.markdown("#### 💾 Save Detection Report")
                    st.markdown("**📍 Where was this photo taken?**")
                    ai_loc = location_picker("ai_detection", city=active_city, height=320)

                    if st.button("💾 Save Report to Database", use_container_width=True):
                        if not ai_loc:
                            st.error("❌ Please choose where the photo was taken: search a place or tap the map.")
                        else:
                            for d in result["detections"]:
                                bbox = d["bbox"]
                                db.insert_ai_detection(
                                    image_path=image_source_name,
                                    hazard_type=d["class_name"],
                                    confidence=d["confidence"],
                                    bbox_x1=bbox[0], bbox_y1=bbox[1],
                                    bbox_x2=bbox[2], bbox_y2=bbox[3],
                                    location=ai_loc["name"] or "Pinned location",
                                    latitude=ai_loc["lat"],
                                    longitude=ai_loc["lng"],
                                    severity=d["severity"]
                                )
                            st.session_state.pop("ai_result", None)
                            reset_location("ai_detection")
                            st.success(f"✅ Saved {total} detection(s) to the database and the Hazard Map!")
                else:
                    st.info("✅ No road damage detected in this image. The road appears to be in good condition!")
            else:
                st.error(f"❌ Detection failed: {result['error']}")

    # Show past detections
    st.divider()
    st.markdown("### 📋 Past AI Detections")
    past = db.get_all_ai_detections()
    if past:
        df = pd.DataFrame(past)
        display_cols = ["id", "hazard_type", "confidence", "location", "severity", "timestamp"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No AI detections recorded yet.")


# ─────────────────────────────────────────────────────────────
# PAGE: STREETLIGHT REPORT
# ─────────────────────────────────────────────────────────────

elif page == "💡 Streetlight Report":
    st.markdown("## 💡 Streetlight Safety Reporting")
    st.caption("Report broken, non-functional, or poorly illuminated streetlights to improve nighttime road safety.")

    st.markdown("#### 📍 Step 1 — Where is the streetlight?")
    sl_loc = location_picker("streetlight", city=active_city)

    with st.form("streetlight_form", clear_on_submit=True):
        st.markdown("#### 📝 Step 2 — Report details")

        col1, col2 = st.columns(2)
        with col1:
            sl_status = st.selectbox(
                "💡 Streetlight Status",
                ["Broken / Not Working", "Dim / Poorly Illuminated", "Flickering", "Missing", "Damaged / Vandalized"]
            )
            sl_location = st.text_input(
                "🏷️ Location name / nearby landmark",
                value=sl_loc["name"] if sl_loc else "",
                key=f"sl_name_{sl_loc['lat']:.6f}_{sl_loc['lng']:.6f}" if sl_loc else "sl_name_empty",
                placeholder="Filled in automatically from the pin — edit if you like"
            )
            sl_severity = st.selectbox(
                "⚡ Severity",
                ["Low", "Medium", "High", "Critical"],
                index=1
            )

        with col2:
            sl_description = st.text_area(
                "📝 Description",
                placeholder="e.g., 3 poles dark near the mosque, very risky at night",
                height=120
            )
            sl_image = st.file_uploader(
                "📸 Photo (optional)",
                type=["jpg", "jpeg", "png"],
                key="sl_image"
            )

        submitted = st.form_submit_button("📨 Submit Report", use_container_width=True)

        if submitted:
            if not sl_loc:
                st.error("❌ Please choose the location first (Step 1): search a place or tap the map.")
            else:
                image_path = save_uploaded_photo(sl_image, prefix="streetlight") if sl_image else ""

                db.insert_streetlight_report(
                    status=sl_status,
                    location=sl_location or sl_loc["name"] or "Pinned location",
                    latitude=sl_loc["lat"],
                    longitude=sl_loc["lng"],
                    description=sl_description,
                    severity=sl_severity,
                    image_path=image_path
                )
                reset_location("streetlight")
                st.success("✅ Streetlight report submitted and added to the Hazard Map! Thank you for improving road safety. 🙏")

    st.divider()

    # Show existing reports
    st.markdown("### 📋 Reported Streetlight Issues")
    reports = db.get_all_streetlight_reports()
    if reports:
        f1, f2 = st.columns([2, 1])
        with f1:
            sl_view = st.radio("View", ["🖼️ Cards with photos", "📊 Table"], horizontal=True,
                               label_visibility="collapsed", key="sl_view")
        with f2:
            only_photos = st.checkbox("Only reports with photos", key="sl_only_photos")

        shown = [r for r in reports if resolve_image_path(r.get("image_path"))] if only_photos else reports

        if sl_view.startswith("📊"):
            df = pd.DataFrame(shown)
            if not df.empty:
                df["photo"] = df["image_path"].apply(lambda p: "📷 Yes" if resolve_image_path(p) else "—")
                cols = [c for c in ["id", "status", "location", "severity", "description", "photo", "timestamp"]
                        if c in df.columns]
                st.dataframe(df[cols], use_container_width=True, hide_index=True)
            st.caption("Switch to **Cards with photos** to see the pictures.")
        else:
            sev_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
            per_row = 3
            for i in range(0, len(shown), per_row):
                cols = st.columns(per_row)
                for col, r in zip(cols, shown[i:i + per_row]):
                    with col:
                        with st.container(border=True):
                            img = resolve_image_path(r.get("image_path"))
                            if img:
                                st.image(img, use_container_width=True)
                            else:
                                st.markdown("<div style='height:120px;display:flex;align-items:center;"
                                            "justify-content:center;background:#0d1f3c;border-radius:8px;"
                                            "color:#6ec8e4;'>📷 No photo</div>", unsafe_allow_html=True)
                            st.markdown(f"**{sev_icon.get(r.get('severity'), '⚪')} {r.get('status', '')}**")
                            st.caption(f"📍 {r.get('location', '')}")
                            if r.get("description"):
                                st.caption(f"📝 {r['description']}")
                            st.caption(f"🕐 {str(r.get('timestamp', ''))[:16].replace('T', ' ')}"
                                       f" • {r.get('severity', '')}")
                            if r.get("latitude") and r.get("longitude"):
                                st.link_button("🗺️ Open in Google Maps",
                                               f"https://www.google.com/maps?q={r['latitude']},{r['longitude']}",
                                               use_container_width=True)
            if not shown:
                st.info("No reports with photos yet.")
    else:
        st.info("No streetlight issues reported yet. Use the form above to submit the first report!")


# ─────────────────────────────────────────────────────────────
# PAGE: HAZARD MAP
# ─────────────────────────────────────────────────────────────

elif page == "🗺️ Hazard Map":
    st.markdown("## 🗺️ Interactive Safety Map")
    st.caption("Explore reported road hazards, potholes, cracks, and streetlight issues on the map.")

    # Get all hazard locations
    locations = db.get_all_hazard_locations()

    active_city = st.session_state.get("active_city", "Multan")
    c_lat = float(st.session_state.get("city_lat", 30.1984))
    c_lng = float(st.session_state.get("city_lng", 71.4687))

    # Map controls
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        st.markdown(f"**📍 Showing {len(locations)} reported hazard(s)** — Centered on {active_city}, Pakistan")
    with col_ctrl2:
        if st.button("🔄 Refresh Map"):
            st.rerun()

    # Create and display map with click detection
    try:
        from streamlit_folium import st_folium

        hazard_map = create_hazard_map(locations, center_lat=c_lat, center_lng=c_lng)
        st_folium(hazard_map, width=None, height=550, returned_objects=[])
    except ImportError:
        st.error("❌ `streamlit-folium` package not installed. Run: `pip install streamlit-folium`")
    except Exception as e:
        st.error(f"❌ Map error: {str(e)}")

    # Quick-add hazard — location picked by search / map tap, never typed coordinates
    st.divider()
    st.markdown("### ➕ Quick Report a Hazard")
    st.markdown("**📍 Step 1 — Where is it?**")
    q_loc = location_picker("quick_hazard", city=active_city, height=320)

    with st.form("quick_hazard_form", clear_on_submit=True):
        st.markdown("**📝 Step 2 — What is it?**")
        qcol1, qcol2, qcol3 = st.columns(3)
        with qcol1:
            q_type = st.selectbox("Hazard Type", ["Pothole", "Road Crack", "Broken Streetlight"])
        with qcol2:
            q_severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=1)
        with qcol3:
            q_desc = st.text_input("Brief Description", placeholder="Large pothole near intersection")

        if st.form_submit_button("📍 Add to Map", use_container_width=True):
            if not q_loc:
                st.error("❌ Please choose the location first: search a place or tap the map above.")
            else:
                q_name = q_loc["name"] or "Pinned location"
                if q_type == "Broken Streetlight":
                    db.insert_streetlight_report(
                        status="Broken / Not Working", location=q_name,
                        latitude=q_loc["lat"], longitude=q_loc["lng"],
                        description=q_desc, severity=q_severity)
                else:
                    db.insert_hazard_report(
                        hazard_type=q_type, location=q_name,
                        latitude=q_loc["lat"], longitude=q_loc["lng"],
                        description=q_desc, severity=q_severity, source="Map Report")
                reset_location("quick_hazard")
                st.success(f"✅ {q_type} reported at {q_name}!")
                st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE: SAFE ROUTE
# ─────────────────────────────────────────────────────────────

elif page == "🧭 Safe Route":
    active_city = st.session_state.get("active_city", "Multan")
    st.markdown("## 🧭 Safe Route Recommendation")
    st.caption("Find routes between locations and see which ones avoid known road hazards.")

    # Disclaimer
    st.markdown("""
    > **⚠️ Disclaimer:** Route recommendations are based on *available hazard reports* 
    > and the OSRM routing service. They do not guarantee safety. Always exercise caution 
    > while driving and follow local traffic rules.
    """)

    # Check if GPS coordinates were sent via URL parameters from device browser
    params = st.query_params
    if "gps_lat" in params and "gps_lng" in params:
        try:
            g_lat = float(params["gps_lat"])
            g_lng = float(params["gps_lng"])
            real_name = routing.reverse_geocode(g_lat, g_lng)
            st.session_state.start_input = real_name or f"{g_lat:.5f}, {g_lng:.5f}"
            st.toast(f"📍 Live Location Acquired: {st.session_state.start_input[:45]}", icon="📍")
        except Exception:
            pass

    # Quick demo route buttons & Live GPS button
    col_gps, col_txt = st.columns([1, 2])
    with col_gps:
        import streamlit.components.v1 as components
        components.html("""
        <button onclick="detectGPS()" style="background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%); color: #0a1628; border: none; padding: 9px 16px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; width: 100%;">
            📍 Use My Live GPS Location
        </button>
        <span id="gps_msg" style="color: #6ec8e4; font-size: 12px; display: block; margin-top: 4px;"></span>
        <script>
        function detectGPS() {
            var msg = document.getElementById('gps_msg');
            if (!navigator.geolocation) {
                msg.textContent = 'GPS not supported on this browser';
                return;
            }
            msg.textContent = 'Fetching current position...';
            navigator.geolocation.getCurrentPosition(
                function(pos) {
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    msg.textContent = 'Found: ' + lat.toFixed(4) + ', ' + lng.toFixed(4);
                    var url = new URL(window.parent.location.href);
                    url.searchParams.set('gps_lat', lat);
                    url.searchParams.set('gps_lng', lng);
                    window.parent.location.href = url.href;
                },
                function(err) {
                    msg.textContent = '⚠️ GPS permission not granted or device has no GPS. Simply type your area name below!';
                },
                { enableHighAccuracy: true, timeout: 8000 }
            );
        }
        </script>
        """, height=70)
    with col_txt:
        st.caption("Click **'Use My Live GPS Location'** to automatically detect your real physical location from your phone/laptop, or type any custom address or paste Google Maps coordinates.")

    st.markdown(f"##### 🚀 Quick Demo Routes ({active_city})")
    qcol1, qcol2, qcol3 = st.columns(3)

    if "start_input" not in st.session_state or not st.session_state.start_input:
        if active_city == "Multan":
            st.session_state.start_input = "Chowk Kutchery, Multan"
            st.session_state.end_input = "Bahauddin Zakariya University, Multan"
        else:
            st.session_state.start_input = "Liberty Market, Lahore"
            st.session_state.end_input = "Lahore Museum, Mall Road, Lahore"

    if active_city == "Multan":
        with qcol1:
            if st.button("📍 Kutchery -> BZU"):
                st.session_state.start_input = "Chowk Kutchery, Multan"
                st.session_state.end_input = "Bahauddin Zakariya University, Multan"
                st.session_state.route_input_mode = "⌨️ Type an address"
        with qcol2:
            if st.button("📍 Gulgasht -> Nishtar"):
                st.session_state.start_input = "Gulgasht Colony, Multan"
                st.session_state.end_input = "Nishtar Hospital, Multan"
                st.session_state.route_input_mode = "⌨️ Type an address"
        with qcol3:
            if st.button("📍 Nawan Shehr -> Mall of Multan"):
                st.session_state.start_input = "Nawan Shehr, Multan"
                st.session_state.end_input = "Mall of Multan, Bosan Road"
                st.session_state.route_input_mode = "⌨️ Type an address"
    else:
        with qcol1:
            if st.button("📍 Liberty -> Museum"):
                st.session_state.start_input = "Liberty Market, Lahore"
                st.session_state.end_input = "Lahore Museum, Mall Road, Lahore"
                st.session_state.route_input_mode = "⌨️ Type an address"
        with qcol2:
            if st.button("📍 Kalma -> Railway"):
                st.session_state.start_input = "Kalma Chowk, Lahore"
                st.session_state.end_input = "Lahore Railway Station"
                st.session_state.route_input_mode = "⌨️ Type an address"
        with qcol3:
            if st.button("📍 Johar Town -> DHA"):
                st.session_state.start_input = "Johar Town, Lahore"
                st.session_state.end_input = "DHA Phase 3, Lahore"
                st.session_state.route_input_mode = "⌨️ Type an address"

    # ── Choose start & destination ─────────────────────────────
    st.markdown("##### 📌 Choose Start & Destination")
    input_mode = st.radio(
        "How do you want to choose locations?",
        ["🗺️ Click on map (most accurate)", "📋 Pick a landmark", "⌨️ Type an address"],
        horizontal=True,
        key="route_input_mode",
    )

    start_location, end_location = "", ""

    if input_mode.startswith("🗺️"):
        from streamlit_folium import st_folium
        import folium

        st.session_state.setdefault("pick_start", None)
        st.session_state.setdefault("pick_end", None)
        st.session_state.setdefault("pick_last_click", None)

        nxt = "START 🟢" if st.session_state.pick_start is None else (
              "DESTINATION 🔴" if st.session_state.pick_end is None else "— both set (click again to move destination)")
        st.caption(f"Click the map to set **{nxt}**. Zoom in for accuracy.")

        c_lat = float(st.session_state.get("city_lat", 30.1984))
        c_lng = float(st.session_state.get("city_lng", 71.4687))
        pick_map = folium.Map(location=[c_lat, c_lng], zoom_start=13, tiles="OpenStreetMap")
        if st.session_state.pick_start:
            folium.Marker(st.session_state.pick_start, tooltip="Start",
                          icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(pick_map)
        if st.session_state.pick_end:
            folium.Marker(st.session_state.pick_end, tooltip="Destination",
                          icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")).add_to(pick_map)

        click = st_folium(pick_map, height=420, width=None, key="pick_map",
                          returned_objects=["last_clicked"])
        lc = click.get("last_clicked") if click else None
        if lc:
            pt = (round(lc["lat"], 6), round(lc["lng"], 6))
            if pt != st.session_state.pick_last_click:
                st.session_state.pick_last_click = pt
                if st.session_state.pick_start is None:
                    st.session_state.pick_start = pt
                else:
                    st.session_state.pick_end = pt
                st.session_state.pop("route_result", None)
                st.rerun()

        pc1, pc2, pc3 = st.columns([2, 2, 1])
        with pc1:
            s = st.session_state.pick_start
            st.markdown(f"🟢 **Start:** `{s[0]:.5f}, {s[1]:.5f}`" if s else "🟢 **Start:** not set")
        with pc2:
            e = st.session_state.pick_end
            st.markdown(f"🔴 **Destination:** `{e[0]:.5f}, {e[1]:.5f}`" if e else "🔴 **Destination:** not set")
        with pc3:
            if st.button("↺ Reset pins"):
                st.session_state.pick_start = st.session_state.pick_end = None
                st.session_state.pop("route_result", None)
                st.rerun()

        if st.session_state.pick_start:
            start_location = f"{st.session_state.pick_start[0]}, {st.session_state.pick_start[1]}"
        if st.session_state.pick_end:
            end_location = f"{st.session_state.pick_end[0]}, {st.session_state.pick_end[1]}"

    elif input_mode.startswith("📋"):
        lm = routing.CITY_LANDMARKS.get(active_city.lower(), {})
        if not lm:
            st.info(f"No built-in landmarks for {active_city} yet — use the map or type an address.")
        else:
            names = {v["display_name"]: k for k, v in lm.items()}
            options = list(names.keys())
            lc1, lc2 = st.columns(2)
            with lc1:
                s_name = st.selectbox("🟢 Start landmark", options, index=0, key="lm_start")
            with lc2:
                e_name = st.selectbox("🔴 Destination landmark", options,
                                      index=min(1, len(options) - 1), key="lm_end")
            start_location = f"{names[s_name]}, {active_city}"
            end_location = f"{names[e_name]}, {active_city}"

    else:
        col1, col2 = st.columns(2)
        with col1:
            start_location = st.text_input(
                "🟢 Starting Location",
                value=st.session_state.get("start_input", ""),
                placeholder="e.g., Chowk Kutchery or 30.2091, 71.4646",
                help="Landmark, address, or coordinates copied from Google Maps (right-click → copy)."
            )
        with col2:
            end_location = st.text_input(
                "🔴 Destination",
                value=st.session_state.get("end_input", ""),
                placeholder="e.g., Bahauddin Zakariya University",
                help="Landmark, address, or coordinates copied from Google Maps (right-click → copy)."
            )

    hazard_radius = st.slider(
        "📏 Hazard Detection Radius (meters)",
        min_value=50,
        max_value=500,
        value=100,
        step=50,
        help="Routes passing within this distance of a known hazard will be flagged."
    )

    if st.button("🧭 Find Safe Route", use_container_width=True):
        if not start_location or not end_location:
            st.error("❌ Please enter both starting location and destination.")
        else:
            from routing import find_safest_route

            # Get known hazards for comparison
            hazard_locations = db.get_all_hazard_locations()

            with st.spinner("🔄 Calculating routes and analyzing hazard exposure..."):
                result = find_safest_route(
                    start_location,
                    end_location,
                    hazard_locations,
                    radius_m=hazard_radius,
                    city=active_city
                )

            st.session_state.route_result = result
            st.session_state.route_radius = hazard_radius
            st.session_state.route_hazards = hazard_locations

    result = st.session_state.get("route_result")
    if result:
        hazard_radius = st.session_state.get("route_radius", hazard_radius)
        hazard_locations = st.session_state.get("route_hazards", [])
        if result["success"]:
            routes = result["routes"]
            rec_idx = result["recommended_index"]

            st.success(f"✅ Found **{len(routes)}** route(s) between your locations!")

            # Show resolved geographical locations
            st.markdown(f"""
            <div style="background: rgba(0, 212, 255, 0.08); border: 1px solid #00d4ff55; border-radius: 8px; padding: 12px 16px; margin: 12px 0; font-size: 0.95rem;">
                <div>🟢 <b>Start Resolved:</b> {result['start']['display_name']} <code style="color:#00d4ff;">({result['start']['lat']:.4f}, {result['start']['lng']:.4f})</code></div>
                <div style="margin-top:6px;">🔴 <b>Destination Resolved:</b> {result['end']['display_name']} <code style="color:#00d4ff;">({result['end']['lat']:.4f}, {result['end']['lng']:.4f})</code></div>
            </div>
            """, unsafe_allow_html=True)

            for label, geo in (("Start", result["start"]), ("Destination", result["end"])):
                if geo.get("approximate"):
                    st.warning(f"⚠️ {label} location could not be found exactly, so the city centre was used. "
                               f"Try a well-known landmark, add the area name, or paste coordinates "
                               f"(right-click the place in Google Maps to copy them).")

            # Route comparison table
            st.markdown("### 📊 Route Comparison")

            for i, route in enumerate(routes):
                is_recommended = (i == rec_idx)
                prefix = "🏆 **RECOMMENDED** — " if is_recommended else ""
                border = "2px solid #00d4ff" if is_recommended else "1px solid #00d4ff33"

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0d1f3c, #132d4f);
                            border: {border}; border-radius: 12px;
                            padding: 20px; margin: 10px 0;
                            {'box-shadow: 0 4px 20px rgba(0,212,255,0.15);' if is_recommended else ''}">
                    <h4 style="color: #00d4ff; margin: 0 0 10px 0;">
                        {prefix}Route {i + 1}
                    </h4>
                    <div style="display: flex; gap: 30px; color: #b0c4de;">
                        <span>📏 <b>{route['distance_km']:.1f}</b> km</span>
                        <span>⏱️ <b>{route['duration_min']:.0f}</b> min</span>
                        <span>⚠️ <b>{route['hazard_count']}</b> nearby hazard(s)</span>
                        <span>📊 Risk Score: <b>{route['hazard_score']}</b></span>
                        <span>{'' if route.get('extra_km', 0) <= 0.05 else f"↪️ +{route['extra_km']:.1f} km vs shortest"}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Display map
            st.markdown("### 🗺️ Route Map")
            st.link_button("🔎 Compare this route in Google Maps",
                           routing.google_maps_url(routes[rec_idx]), use_container_width=True)
            try:
                from streamlit_folium import st_folium

                route_map = create_route_map(routes, hazard_locations, recommended_index=rec_idx)
                st_folium(route_map, width=None, height=500, returned_objects=[])
            except ImportError:
                st.error("❌ `streamlit-folium` not installed.")
            except Exception as e:
                st.error(f"❌ Map error: {str(e)}")

            # Info about the recommendation
            if routes:
                rec = routes[rec_idx]
                if rec["hazard_count"] == 0:
                    st.info("ℹ️ No known hazards were found near any of the routes. "
                            "This could mean the area is safe, or simply that no hazards "
                            "have been reported there yet.")
                else:
                    st.info(f"ℹ️ Route {rec_idx + 1} is recommended: it has the best balance of hazard exposure "
                            f"({rec['hazard_count']} hazard(s) within {hazard_radius}m) and distance "
                            f"({rec['distance_km']:.1f} km). Routes more than 30% longer than the shortest "
                            f"are never recommended. Always drive carefully and watch for unreported hazards.")

        else:
            st.error(f"❌ {result['error']}")
            st.info("💡 **Tips:** Try more specific addresses, add city/country name, "
                    "or check your internet connection.")

    # Show info about how it works
    with st.expander("ℹ️ How Safe Route Recommendation Works"):
        st.markdown("""
        1. **Geocoding**: Your start and end locations are converted to coordinates using OpenStreetMap Nominatim.
        2. **Route Calculation**: The OSRM (Open Source Routing Machine) service calculates driving routes including alternatives.
        3. **Hazard Analysis**: Each route is checked against known hazard reports in our database. 
           Hazards within the specified radius of the route are counted.
        4. **Recommendation**: The route with the lowest hazard exposure score is recommended. 
           The score considers both the number and severity of nearby hazards.

        **Limitations:**
        - Recommendations depend on hazards that have been reported. Unreported hazards won't be considered.
        - Route data comes from OSRM's public server and may not reflect real-time traffic or road closures.
        - This is a planning tool, not a navigation system. Always stay alert while driving.
        """)


# ─────────────────────────────────────────────────────────────
# PAGE: AI NEGOTIATOR
# ─────────────────────────────────────────────────────────────

elif page == "🤝 AI Negotiator":
    st.markdown("""
    <div class="hero-banner">
        <h1>🤝 AI Negotiator</h1>
        <p>Understand demands, discover common ground, and build a fair compromise.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("Enter both parties' demands in simple language. Each card analyzes the same demands.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🧑 Party A")
        party_a = st.text_area("Party A's demands", placeholder="Example: We need the road repaired before the new route opens.", height=150, key="neg_party_a")
    with col_b:
        st.markdown("### 🧑 Party B")
        party_b = st.text_area("Party B's demands", placeholder="Example: We need traffic access to remain open during repairs.", height=150, key="neg_party_b")

    st.divider()
    st.markdown("## Mystery Cards")
    card1, card2, card3 = st.columns(3)
    with card1:
        st.markdown("<div class='css-card'><h3>🧠 Card 1</h3><h4>Understand Demands</h4><p>Analyze both parties' demands.</p></div>", unsafe_allow_html=True)
        run_understand = st.button("Analyze Demands", key="btn_understand", use_container_width=True)
    with card2:
        st.markdown("<div class='css-card'><h3>🤝 Card 2</h3><h4>Find Common Grounds</h4><p>Find shared priorities and differences.</p></div>", unsafe_allow_html=True)
        run_common = st.button("Find Common Ground", key="btn_common", use_container_width=True)
    with card3:
        st.markdown("<div class='css-card'><h3>⚖️ Card 3</h3><h4>Suggest Balanced Solution</h4><p>Generate a practical compromise.</p></div>", unsafe_allow_html=True)
        run_solution = st.button("Generate Solution", key="btn_solution", use_container_width=True)

    if run_understand or run_common or run_solution:
        if not party_a.strip() or not party_b.strip():
            st.warning("Please enter demands for both Party A and Party B first.")
        else:
            try:
                if run_understand:
                    st.session_state.neg_understanding = negotiator.understand_demands(party_a, party_b)
                if run_common:
                    st.session_state.neg_common = negotiator.find_common_ground(party_a, party_b)
                if run_solution:
                    st.session_state.neg_solution = negotiator.suggest_balanced_solution(party_a, party_b)
            except ValueError as exc:
                st.error(str(exc))

    if st.session_state.get("neg_understanding"):
        result = st.session_state.neg_understanding
        st.divider()
        st.markdown("### 🧠 Card 1 Result — Understanding Demands")
        left, right = st.columns(2)
        with left:
            st.markdown("**Party A's demand**")
            st.write(result["party_a_summary"])
            st.caption("Key terms: " + (", ".join(result["party_a_terms"][:12]) or "No unique terms found"))
        with right:
            st.markdown("**Party B's demand**")
            st.write(result["party_b_summary"])
            st.caption("Key terms: " + (", ".join(result["party_b_terms"][:12]) or "No unique terms found"))
        if result["shared_terms"]:
            st.success("Shared terms: " + ", ".join(result["shared_terms"][:12]))

    if st.session_state.get("neg_common"):
        result = st.session_state.neg_common
        st.divider()
        st.markdown("### 🤝 Card 2 Result — Common Grounds")
        st.success(result["explanation"])
        left, right = st.columns(2)
        with left:
            st.markdown("**Party A's distinct points**")
            st.write(", ".join(result["party_a_unique"][:15]) or "No distinct keywords identified.")
        with right:
            st.markdown("**Party B's distinct points**")
            st.write(", ".join(result["party_b_unique"][:15]) or "No distinct keywords identified.")

    if st.session_state.get("neg_solution"):
        result = st.session_state.neg_solution
        st.divider()
        st.markdown("### ⚖️ Card 3 Result — Balanced Solution")
        for index, item in enumerate(result["proposal"], start=1):
            st.write(f"{index}. {item}")
        with st.expander("How each party is considered"):
            st.write(result["party_a_consideration"])
            st.write(result["party_b_consideration"])
        st.caption(result["note"])

    if st.button("🗑️ Clear Negotiation", key="clear_negotiation"):
        for key in ("neg_understanding", "neg_common", "neg_solution"):
            st.session_state.pop(key, None)
        st.session_state.neg_party_a = ""
        st.session_state.neg_party_b = ""
        st.rerun()
