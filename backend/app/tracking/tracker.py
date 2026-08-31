import time
import math
from typing import List, Dict, Any, Optional, Tuple


class CentroidTracker:
    """
    Lightweight Multi-Object Centroid Tracker with trajectory & bottom-center tracking.
    Assigns persistent IDs to detected persons across video frames to compute
    pixels/second velocity, displacement, direction vectors, and zone transitions.
    """

    def __init__(self, max_disappeared: int = 20, max_distance: float = 120.0):
        self.next_object_id = 1
        self.objects: Dict[int, List[float]] = {}  # object_id -> center [x, y]
        self.bottom_centers: Dict[int, List[float]] = {}  # object_id -> bottom_center [x, y]
        self.prev_bottom_centers: Dict[int, List[float]] = {}  # object_id -> prev bottom_center [x, y]
        self.bboxes: Dict[int, List[float]] = {}  # object_id -> [x1, y1, x2, y2]
        self.confidences: Dict[int, float] = {}
        self.disappeared: Dict[int, int] = {}
        self.velocities: Dict[int, float] = {}  # object_id -> speed (px/sec)
        self.directions: Dict[int, Dict[str, float]] = {}  # object_id -> {dx, dy, angle_deg}
        self.displacements: Dict[int, float] = {}
        self.last_seen_frames: Dict[int, int] = {}
        self.frame_count = 0
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(
        self, detections: List[Dict[str, Any]], fps: float = 30.0
    ) -> Dict[int, Dict[str, Any]]:
        """
        Updates tracked objects with new bounding box centroids and bottom-centers.
        Returns tracked objects dictionary keyed by persistent object_id.
        """
        self.frame_count += 1
        dt = 1.0 / max(1.0, fps)

        if len(detections) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return self._get_tracked_dict()

        input_centroids = [
            d.get("center", [(d["bbox"][0] + d["bbox"][2]) / 2.0, (d["bbox"][1] + d["bbox"][3]) / 2.0])
            for d in detections
        ]
        input_bottom_centers = [
            d.get("bottom_center", [(d["bbox"][0] + d["bbox"][2]) / 2.0, d["bbox"][3]])
            for d in detections
        ]

        if len(self.objects) == 0:
            for i, center in enumerate(input_centroids):
                self._register(
                    center=center,
                    bottom_center=input_bottom_centers[i],
                    bbox=detections[i].get("bbox", [0, 0, 0, 0]),
                    confidence=detections[i].get("confidence", 0.0),
                )
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Distance matrix calculation using centroids
            distances = []
            for obj_center in object_centroids:
                row = [math.hypot(obj_center[0] - c[0], obj_center[1] - c[1]) for c in input_centroids]
                distances.append(row)

            # Greedy Hungarian-like distance assignment
            used_rows = set()
            used_cols = set()

            for _ in range(len(object_ids)):
                min_dist = float("inf")
                min_r, min_c = -1, -1
                for r in range(len(object_ids)):
                    if r in used_rows:
                        continue
                    for c in range(len(input_centroids)):
                        if c in used_cols:
                            continue
                        if distances[r][c] < min_dist:
                            min_dist = distances[r][c]
                            min_r, min_c = r, c

                if min_r != -1 and min_c != -1 and min_dist < self.max_distance:
                    obj_id = object_ids[min_r]
                    prev_bc = self.bottom_centers[obj_id]
                    new_bc = input_bottom_centers[min_c]
                    new_center = input_centroids[min_c]

                    dx = new_bc[0] - prev_bc[0]
                    dy = new_bc[1] - prev_bc[1]
                    disp = math.hypot(dx, dy)
                    speed_px_sec = disp / dt
                    angle = math.degrees(math.atan2(dy, dx)) if disp > 0.1 else 0.0

                    self.prev_bottom_centers[obj_id] = prev_bc
                    self.objects[obj_id] = new_center
                    self.bottom_centers[obj_id] = new_bc
                    self.bboxes[obj_id] = detections[min_c].get("bbox", [0, 0, 0, 0])
                    self.confidences[obj_id] = detections[min_c].get("confidence", 0.0)
                    self.velocities[obj_id] = round(speed_px_sec, 2)
                    self.displacements[obj_id] = round(disp, 2)
                    self.directions[obj_id] = {
                        "dx": round(dx / disp, 2) if disp > 0.1 else 0.0,
                        "dy": round(dy / disp, 2) if disp > 0.1 else 0.0,
                        "angle_deg": round(angle, 1),
                    }
                    self.disappeared[obj_id] = 0
                    self.last_seen_frames[obj_id] = self.frame_count

                    used_rows.add(min_r)
                    used_cols.add(min_c)

            # Deregister missing objects
            for r in range(len(object_ids)):
                if r not in used_rows:
                    obj_id = object_ids[r]
                    self.disappeared[obj_id] += 1
                    if self.disappeared[obj_id] > self.max_disappeared:
                        self._deregister(obj_id)

            # Register new objects
            for c in range(len(input_centroids)):
                if c not in used_cols:
                    self._register(
                        center=input_centroids[c],
                        bottom_center=input_bottom_centers[c],
                        bbox=detections[c].get("bbox", [0, 0, 0, 0]),
                        confidence=detections[c].get("confidence", 0.0),
                    )

        return self._get_tracked_dict()

    def _register(
        self,
        center: List[float],
        bottom_center: List[float],
        bbox: List[float],
        confidence: float,
    ):
        obj_id = self.next_object_id
        self.objects[obj_id] = center
        self.bottom_centers[obj_id] = bottom_center
        self.prev_bottom_centers[obj_id] = bottom_center
        self.bboxes[obj_id] = bbox
        self.confidences[obj_id] = confidence
        self.disappeared[obj_id] = 0
        self.velocities[obj_id] = 0.0
        self.displacements[obj_id] = 0.0
        self.directions[obj_id] = {"dx": 0.0, "dy": 0.0, "angle_deg": 0.0}
        self.last_seen_frames[obj_id] = self.frame_count
        self.next_object_id += 1

    def _deregister(self, object_id: int):
        for d in (
            self.objects,
            self.bottom_centers,
            self.prev_bottom_centers,
            self.bboxes,
            self.confidences,
            self.disappeared,
            self.velocities,
            self.displacements,
            self.directions,
            self.last_seen_frames,
        ):
            if object_id in d:
                del d[object_id]

    def _get_tracked_dict(self) -> Dict[int, Dict[str, Any]]:
        result = {}
        for obj_id, center in self.objects.items():
            result[obj_id] = {
                "id": obj_id,
                "tracking_id": obj_id,
                "center": center,
                "bottom_center": self.bottom_centers.get(obj_id, center),
                "prev_bottom_center": self.prev_bottom_centers.get(obj_id, center),
                "bbox": self.bboxes.get(obj_id, [0, 0, 0, 0]),
                "confidence": self.confidences.get(obj_id, 0.0),
                "speed": self.velocities.get(obj_id, 0.0),  # px/sec
                "velocity_px_sec": self.velocities.get(obj_id, 0.0),
                "displacement": self.displacements.get(obj_id, 0.0),
                "direction": self.directions.get(obj_id, {"dx": 0.0, "dy": 0.0, "angle_deg": 0.0}),
                "frame_num": self.last_seen_frames.get(obj_id, self.frame_count),
            }
        return result
