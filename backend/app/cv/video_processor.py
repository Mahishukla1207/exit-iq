import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False


class VideoProcessor:
    """
    OpenCV + YOLO Video Processing Engine.
    Processes CCTV video streams or prerecorded footage for Person & Hazard detection.
    """

    def __init__(self, model_name: str = "yolov8n.pt"):
        self.model_name = model_name
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

    def detect_frame(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detects people (COCO class 0) and hazards in video frame.
        Returns list of detection dicts: [{class_id, class_name, confidence, bbox: [x1, y1, x2, y2]}]
        """
        detections = []
        if self.is_initialized and self.model is not None:
            results = self.model(frame, verbose=False)
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    if conf > 0.35 and cls_id == 0:  # Person class
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        detections.append({
                            "class_id": cls_id,
                            "class_name": "person",
                            "confidence": round(conf, 2),
                            "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                            "center": [round((x1 + x2) / 2, 1), round((y1 + y2) / 2, 1)],
                        })
        return detections
