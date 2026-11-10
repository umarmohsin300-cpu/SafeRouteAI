"""
SafeRoute AI - Detection Module
Handles YOLOv8 road damage detection using a pretrained model.

Model: YOLOv8 trained on RDD2022 (Road Damage Detection 2022)
Classes: D00 (Longitudinal Crack), D10 (Transverse Crack),
         D20 (Alligator Crack), D40 (Pothole)
"""

import os
import cv2
import numpy as np
from PIL import Image

# Path for model weights
WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
MODEL_PATH = os.path.join(WEIGHTS_DIR, "rdd_yolov8.pt")

# Class name mapping
CLASS_NAMES = {
    0: "Alligator Crack",
    1: "Transverse Crack",
    2: "Longitudinal Crack",
    3: "Road Corruption",
    4: "Pothole"
}

# Map class names to hazard categories
CLASS_TO_HAZARD = {
    "Longitudinal Crack": "Road Crack",
    "Transverse Crack": "Road Crack",
    "Alligator Crack": "Road Crack",
    "Road Corruption": "Road Crack",
    "Pothole": "Pothole"
}

# Colors for drawing bounding boxes (BGR format for OpenCV)
CLASS_COLORS = {
    "Longitudinal Crack": (0, 165, 255),   # Orange
    "Transverse Crack": (0, 200, 255),     # Gold
    "Alligator Crack": (0, 100, 255),      # Deep Orange
    "Road Corruption": (0, 140, 255),      # Amber
    "Pothole": (0, 0, 255)                 # Red
}


def get_model_status():
    """Check if the YOLO model weights are available."""
    if os.path.exists(MODEL_PATH):
        return True, MODEL_PATH
    # Check for any .pt file in weights directory
    if os.path.exists(WEIGHTS_DIR):
        for f in os.listdir(WEIGHTS_DIR):
            if f.endswith(".pt"):
                return True, os.path.join(WEIGHTS_DIR, f)
    return False, None


def load_model():
    """Load the YOLOv8 model."""
    available, path = get_model_status()
    if not available:
        return None, "Model weights not found. See instructions to download."

    try:
        from ultralytics import YOLO
        model = YOLO(path)
        return model, "Model loaded successfully."
    except ImportError:
        return None, "ultralytics package not installed. Run: pip install ultralytics"
    except Exception as e:
        return None, f"Error loading model: {str(e)}"


def detect_road_damage(image_input, confidence_threshold=0.25):
    """
    Run road damage detection on an image.

    Args:
        image_input: PIL Image, numpy array, or file path
        confidence_threshold: Minimum confidence for detections

    Returns:
        dict with keys:
            - success (bool)
            - annotated_image (numpy array or None)
            - detections (list of dicts)
            - total_hazards (int)
            - error (str or None)
    """
    result = {
        "success": False,
        "annotated_image": None,
        "detections": [],
        "total_hazards": 0,
        "error": None
    }

    # Load model
    model, message = load_model()
    if model is None:
        result["error"] = message
        return result

    try:
        # Convert input to numpy array
        if isinstance(image_input, Image.Image):
            img_array = np.array(image_input.convert("RGB"))
        elif isinstance(image_input, np.ndarray):
            img_array = image_input
        elif isinstance(image_input, str) and os.path.exists(image_input):
            img_array = cv2.imread(image_input)
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        else:
            result["error"] = "Invalid image input."
            return result

        # Run inference
        results = model.predict(
            source=img_array,
            conf=confidence_threshold,
            verbose=False
        )

        # Process results
        detections = []
        annotated_img = img_array.copy()

        if results and len(results) > 0:
            r = results[0]

            # Get the model's class names
            model_class_names = r.names if hasattr(r, 'names') else CLASS_NAMES

            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())

                    # Get class name from model or our mapping
                    if cls_id in model_class_names:
                        class_name = model_class_names[cls_id]
                    elif cls_id in CLASS_NAMES:
                        class_name = CLASS_NAMES[cls_id]
                    else:
                        class_name = f"Damage_{cls_id}"

                    # Map RDD codes or format readable names
                    rdd_mapping = {
                        "D00": "Longitudinal Crack",
                        "D10": "Transverse Crack",
                        "D20": "Alligator Crack",
                        "D40": "Pothole",
                        "other corruption": "Road Corruption"
                    }
                    display_name = rdd_mapping.get(class_name, class_name).title()

                    # Determine severity based on confidence and box size
                    box_area = (x2 - x1) * (y2 - y1)
                    img_area = img_array.shape[0] * img_array.shape[1]
                    area_ratio = box_area / img_area if img_area > 0 else 0

                    if conf > 0.7 and area_ratio > 0.1:
                        severity = "Critical"
                    elif conf > 0.5:
                        severity = "High"
                    elif conf > 0.3:
                        severity = "Medium"
                    else:
                        severity = "Low"

                    detection = {
                        "class_name": display_name,
                        "class_id": cls_id,
                        "confidence": round(conf * 100, 1),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "severity": severity,
                        "hazard_category": CLASS_TO_HAZARD.get(display_name, "Road Damage")
                    }
                    detections.append(detection)

                    # Draw bounding box on image
                    color = CLASS_COLORS.get(display_name, (0, 255, 0))
                    # Convert to BGR for cv2
                    color_bgr = (color[2], color[1], color[0])
                    thickness = max(2, int(min(img_array.shape[:2]) / 200))
                    cv2.rectangle(annotated_img,
                                  (int(x1), int(y1)), (int(x2), int(y2)),
                                  color_bgr, thickness)

                    # Draw label
                    label = f"{display_name} {conf*100:.0f}%"
                    font_scale = max(0.5, min(img_array.shape[:2]) / 1000)
                    font_thickness = max(1, int(font_scale * 2))
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                                   font_scale, font_thickness)
                    cv2.rectangle(annotated_img,
                                  (int(x1), int(y1) - th - 10),
                                  (int(x1) + tw + 6, int(y1)),
                                  color_bgr, -1)
                    cv2.putText(annotated_img, label,
                                (int(x1) + 3, int(y1) - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                                (255, 255, 255), font_thickness)

        result["success"] = True
        result["annotated_image"] = annotated_img
        result["detections"] = detections
        result["total_hazards"] = len(detections)

    except Exception as e:
        result["error"] = f"Detection error: {str(e)}"

    return result


def get_download_instructions():
    """Return instructions for downloading the model weights."""
    return """
### 📥 Model Setup Instructions

To enable AI road damage detection, you need a YOLOv8 model trained on road damage data.

**Option 1: Download from Hugging Face**
1. Visit a YOLOv8 RDD2022 model repository on Hugging Face
2. Download the `.pt` weights file
3. Place it in the `weights/` folder
4. Rename it to `rdd_yolov8.pt`

**Option 2: Use the ultralytics CLI**
```bash
# If you have a trained model, place the .pt file in the weights/ folder
cp your_model.pt weights/rdd_yolov8.pt
```

**Option 3: Quick test with any YOLOv8 model**
```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Downloads automatically
# Note: Generic YOLOv8 won't detect road damage specifically
```

The model should detect: Longitudinal Cracks, Transverse Cracks, Alligator Cracks, and Potholes.
"""
