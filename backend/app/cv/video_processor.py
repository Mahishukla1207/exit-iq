import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

# Canonical YOLO model path under backend/models/yolov8n.pt
CANONICAL_YOLO_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models", "yolov8n.pt")
)


class VideoProcessor:
    """
    OpenCV + YOLO Video Processing Engine.
    Processes CCTV video streams or prerecorded footage for Person & Hazard detection.
    """

    def __init__(self, model_name: Optional[str] = None, conf_threshold: float = 0.40):
        self.model_name = model_name or (CANONICAL_YOLO_PATH if os.path.exists(CANONICAL_YOLO_PATH) else "yolov8n.pt")
        self.conf_threshold = conf_threshold
        self.model = None
        self.is_initialized = False

    def initialize(self):
        if HAS_YOLO and not self.is_initialized:
            try:
                # Load lightweight nano model for detection
                self.model = YOLO(self.model_name)
                self.is_initialized = True
            except Exception as e:
                print(f"[YOLO] Could not load model: {e}. CV processor will operate in fallback mode.")

    def detect_frame(
        self, frame: np.ndarray, conf_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        Detects people (COCO class 0) in video frame.
        Returns list of detection dicts:
        [{
            class_id: 0,
            class_name: 'person',
            confidence: float,
            bbox: [x1, y1, x2, y2],
            center: [cx, cy],
            bottom_center: [bcx, bcy]
        }]
        """
        threshold = conf_threshold if conf_threshold is not None else self.conf_threshold
        detections = []
        if not self.is_initialized:
            self.initialize()

        if self.is_initialized and self.model is not None:
            try:
                results = self.model(frame, verbose=False)
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        if conf >= threshold and cls_id == 0:  # Person class
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            bcx = (x1 + x2) / 2.0
                            bcy = y2  # Ground position at feet level
                            cx = (x1 + x2) / 2.0
                            cy = (y1 + y2) / 2.0

                            detections.append({
                                "class_id": cls_id,
                                "class_name": "person",
                                "confidence": round(conf, 2),
                                "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                                "center": [round(cx, 1), round(cy, 1)],
                                "bottom_center": [round(bcx, 1), round(bcy, 1)],
                            })
            except Exception as e:
                print(f"[YOLO] Inference error: {e}")
        return detections
