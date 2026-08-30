import math
from typing import List, Dict, Any


class CentroidTracker:
    """
    Lightweight Multi-Object Centroid Tracker.
    Assigns persistent IDs to detected persons across video frames to compute velocity & zone transitions.
    """

    def __init__(self, max_disappeared: int = 15, max_distance: float = 80.0):
        self.next_object_id = 1
        self.objects: Dict[int, List[float]] = {}  # object_id -> center [x, y]
        self.disappeared: Dict[int, int] = {}
        self.velocities: Dict[int, float] = {}  # object_id -> speed (px/frame)
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, detections: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Updates tracked objects with new bounding box centroids.
        Returns tracked objects dictionary: {id: {center, speed}}
        """
        if len(detections) == 0:
            for obj_id in list(self.disappeared.keys()):
                self.disappeared[obj_id] += 1
                if self.disappeared[obj_id] > self.max_disappeared:
                    self._deregister(obj_id)
            return self._get_tracked_dict()

        input_centroids = [d["center"] for d in detections]

        if len(self.objects) == 0:
            for center in input_centroids:
                self._register(center)
        else:
            object_ids = list(self.objects.keys())
            object_centroids = list(self.objects.values())

            # Distance matrix calculation
            distances = []
            for obj_center in object_centroids:
                row = [math.hypot(obj_center[0] - c[0], obj_center[1] - c[1]) for c in input_centroids]
                distances.append(row)

            # Greedy assignment
            used_rows = set()
            used_cols = set()

            for i in range(len(object_ids)):
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
                    prev_center = self.objects[obj_id]
                    new_center = input_centroids[min_c]
                    speed = math.hypot(new_center[0] - prev_center[0], new_center[1] - prev_center[1])

                    self.objects[obj_id] = new_center
                    self.velocities[obj_id] = round(speed, 2)
                    self.disappeared[obj_id] = 0

                    used_rows.add(min_r)
                    used_cols.add(min_c)

            # Register new objects
            for c in range(len(input_centroids)):
                if c not in used_cols:
                    self._register(input_centroids[c])

        return self._get_tracked_dict()

    def _register(self, center: List[float]):
        self.objects[self.next_object_id] = center
        self.disappeared[self.next_object_id] = 0
        self.velocities[self.next_object_id] = 0.0
        self.next_object_id += 1

    def _deregister(self, object_id: int):
        del self.objects[object_id]
        del self.disappeared[object_id]
        if object_id in self.velocities:
            del self.velocities[object_id]

    def _get_tracked_dict(self) -> Dict[int, Dict[str, Any]]:
        result = {}
        for obj_id, center in self.objects.items():
            result[obj_id] = {
                "id": obj_id,
                "center": center,
                "speed": self.velocities.get(obj_id, 0.0),
            }
        return result
