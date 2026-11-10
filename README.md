# SafeRoute AI 🛡️

**Smarter Roads. Safer Journeys.**

AI-Powered Road Hazards & Streetlight Safety Mapping

---

## 🚀 Features

- **🤖 AI Road Damage Detection** — Upload road images and detect potholes, cracks, and pavement damage using YOLOv8 computer vision (trained on RDD2022 dataset)
- **💡 Streetlight Safety Reporting** — Report broken, dim, or missing streetlights to improve nighttime road safety
- **🗺️ Interactive Hazard Map** — Visualize all reported hazards on an interactive map with color-coded markers
- **🧭 Safe Route Recommendation** — Find routes between locations that minimize exposure to known road hazards
- **📊 Professional Dashboard** — Track hazard statistics, recent reports, and safety trends

## 📋 Requirements

- Python 3.9+
- Internet connection (for routing and geocoding services)

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up AI Model (Optional but recommended)

Download the pretrained YOLOv8 road damage detection model:

```bash
# Option A: Using huggingface-cli
huggingface-cli download ozair23/yolov8-road-damage-detector best.pt --local-dir weights

# Option B: Using Python
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('ozair23/yolov8-road-damage-detector', 'best.pt', local_dir='weights')"

# Option C: Manual download
# Visit: https://huggingface.co/ozair23/yolov8-road-damage-detector
# Download best.pt and place it in the weights/ folder
```

Then rename the weights file:

```bash
# Rename to the expected filename
mv weights/best.pt weights/rdd_yolov8.pt
# On Windows:
# ren weights\best.pt rdd_yolov8.pt
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## 🏗️ Project Structure

```
SafeRouteAI/
├── app.py              # Main Streamlit application
├── database.py         # SQLite database operations
├── detection.py        # YOLOv8 road damage detection
├── routing.py          # Route calculation & hazard analysis
├── map_utils.py        # Folium map utilities
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
├── data/               # Database & uploaded images
└── weights/            # AI model weights (download separately)
```

## 🤖 AI Model

This project uses a YOLOv8 model trained on the **RDD2022 (Road Damage Detection 2022)** dataset.

**Detected Classes:**
| Code | Type | Description |
|------|------|-------------|
| D00 | Longitudinal Crack | Cracks parallel to traffic direction |
| D10 | Transverse Crack | Cracks perpendicular to traffic |
| D20 | Alligator Crack | Interconnected fatigue cracking pattern |
| D40 | Pothole | Bowl-shaped depressions in pavement |

**Model Source:** [ozair23/yolov8-road-damage-detector](https://huggingface.co/ozair23/yolov8-road-damage-detector)

> ⚠️ The AI model does **not** detect streetlight faults. Streetlight issues are reported manually through the dedicated reporting form.

## 🗺️ Services Used

- **OSRM** (Open Source Routing Machine) — Route calculation
- **OpenStreetMap Nominatim** — Geocoding
- **Folium** — Interactive maps
- **OpenStreetMap / CartoDB** — Map tiles

## ⚠️ Disclaimers

- Route safety recommendations are based on **available hazard reports only**. Unreported hazards will not be considered.
- This is a **prototype tool**, not a certified navigation system. Always follow local traffic rules and stay alert.
- AI detection accuracy depends on image quality and the model's training data.

## 📝 License

Hackathon Project — 2026
