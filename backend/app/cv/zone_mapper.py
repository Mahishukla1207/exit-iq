import time
import math
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Building zones updated by the live CCTV ROI mapper (4 camera quadrants).
CV_MAPPED_ZONE_IDS = frozenset({"zone_atrium", "zone_north", "zone_south", "zone_east"})


class ROIZoneMapper:
    """
    Maps camera coordinates (person bottom-center points) into logical floor plan zones
    using polygon Region of Interest (ROI) mapping and cv2.pointPolygonTest.
    Computes real crowd analytics: density, velocity (px/sec), inflow, outflow, and density change rate.
    """

    def __init__(self, frame_width: int = 1280, frame_height: int = 720, custom_rois: Optional[Dict[str, Any]] = None):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.rois: Dict[str, Dict[str, Any]] = {}
        self.person_zone_history: Dict[int, str] = {}  # tracking_id -> last_known_zone_id
        self.zone_densities_history: Dict[str, List[Tuple[float, float]]] = {}  # zone_id -> [(timestamp, density)]

        # Cumulative inflow / outflow counters per zone
        self.zone_inflow_counts: Dict[str, float] = {}
        self.zone_outflow_counts: Dict[str, float] = {}

        self.last_update_time = time.time()
        self.setup_default_rois(custom_rois)

    def setup_default_rois(self, custom_rois: Optional[Dict[str, Any]] = None):
        """Initializes 4 quadrant / corridor ROIs over camera field of view."""
        w, h = self.frame_width, self.frame_height

        if custom_rois:
            for zid, cfg in custom_rois.items():
                poly = np.array(cfg["polygon"], dtype=np.int32)
                area = cfg.get("area", cv2.polygonArea(poly))
                self.rois[zid] = {
                    "name": cfg.get("name", zid),
                    "polygon": poly,
                    "area": max(1.0, area),
                }
        else:
            # Split camera frame into 4 representative floor plan zones:
            # 1. zone_atrium (West Atrium / Top-Left)
            # 2. zone_north (North Corridor / Top-Right)
            # 3. zone_south (South Corridor / Bottom-Left)
            # 4. zone_east (East Corridor / Bottom-Right)
            rois_config = {
                "zone_atrium": {
                    "name": "West Wing Atrium",
                    "polygon": [[0, 0], [int(w * 0.5), 0], [int(w * 0.5), int(h * 0.5)], [0, int(h * 0.5)]],
                    "area": (w * 0.5 * h * 0.5) / 1000.0,
                },
                "zone_north": {
                    "name": "North Wing Hallway",
                    "polygon": [[int(w * 0.5), 0], [w, 0], [w, int(h * 0.5)], [int(w * 0.5), int(h * 0.5)]],
                    "area": (w * 0.5 * h * 0.5) / 1000.0,
                },
                "zone_south": {
                    "name": "South Wing Hallway",
                    "polygon": [[0, int(h * 0.5)], [int(w * 0.5), int(h * 0.5)], [int(w * 0.5), h], [0, h]],
                    "area": (w * 0.5 * h * 0.5) / 1000.0,
                },
                "zone_east": {
                    "name": "East Corridor",
                    "polygon": [[int(w * 0.5), int(h * 0.5)], [w, int(h * 0.5)], [w, h], [int(w * 0.5), h]],
                    "area": (w * 0.5 * h * 0.5) / 1000.0,
                },
            }

            for zid, cfg in rois_config.items():
                poly = np.array(cfg["polygon"], dtype=np.int32)
                self.rois[zid] = {
                    "name": cfg["name"],
                    "polygon": poly,
                    "area": cfg["area"],
                }

        for zid in self.rois:
            self.zone_inflow_counts[zid] = 0.0
            self.zone_outflow_counts[zid] = 0.0
            self.zone_densities_history[zid] = []

    def get_zone_for_point(self, point: Tuple[float, float]) -> Optional[str]:
        """
        Determines which zone ROI polygon contains the bottom-center point (x, y).
        Uses cv2.pointPolygonTest for exact point-in-polygon mapping.
        """
        pt = (float(point[0]), float(point[1]))
        for zid, roi_info in self.rois.items():
            dist = cv2.pointPolygonTest(roi_info["polygon"], pt, measureDist=False)
            if dist >= 0:  # Inside or on boundary
                return zid
        return None

    def process_analytics(
        self, tracked_objects: Dict[int, Dict[str, Any]], fps: float = 30.0
    ) -> Dict[str, Any]:
        """
        Processes tracked persons, maps bottom-centers to ROIs, calculates inflow/outflow,
        zone densities, average speeds (px/sec), and density change rates.
        """
        now = time.time()
        dt = max(0.1, now - self.last_update_time)
        self.last_update_time = now

        zone_counts: Dict[str, int] = {zid: 0 for zid in self.rois}
        zone_speeds: Dict[str, List[float]] = {zid: [] for zid in self.rois}
        zone_angles: Dict[str, List[float]] = {zid: [] for zid in self.rois}
        current_tracked_zones: Dict[int, str] = {}

        # 1. Map each tracked person to a zone and check transitions for inflow/outflow
        for track_id, info in tracked_objects.items():
            bc = info.get("bottom_center", info.get("center"))
            speed = info.get("velocity_px_sec", info.get("speed", 0.0))
            direction = info.get("direction", {})
            angle = direction.get("angle_deg", 0.0)

            zid = self.get_zone_for_point(bc)
            if zid:
                zone_counts[zid] += 1
                zone_speeds[zid].append(speed)
                zone_angles[zid].append(angle)
                current_tracked_zones[track_id] = zid

                prev_zid = self.person_zone_history.get(track_id)
                if prev_zid and prev_zid != zid:
                    # Transition detected: prev_zid -> zid
                    self.zone_outflow_counts[prev_zid] += 1.0
                    self.zone_inflow_counts[zid] += 1.0

        # Update person zone history
        self.person_zone_history = current_tracked_zones

        # 2. Compute zone analytics
        zone_analytics: Dict[str, Dict[str, Any]] = {}
        total_people = sum(zone_counts.values())

        for zid, roi_info in self.rois.items():
            count = zone_counts[zid]
            # Normalized density = people / zone_area (calibrated area factor)
            density = round(count / max(0.1, roi_info["area"] / 100.0), 2)
            avg_speed = round(float(np.mean(zone_speeds[zid])), 2) if zone_speeds[zid] else 0.0

            # Calculate density change rate: (current_density - prev_density) / dt
            hist = self.zone_densities_history[zid]
            hist.append((now, density))
            # Keep history to last 10 seconds
            self.zone_densities_history[zid] = [(t, d) for t, d in hist if now - t <= 10.0]

            prev_density = hist[0][1] if len(hist) > 1 else density
            density_change_rate = round((density - prev_density) / max(0.5, now - hist[0][0]), 3)

            # Inflow and outflow rates per second
            inflow_rate = round(self.zone_inflow_counts[zid] / max(1.0, dt), 2)
            outflow_rate = round(self.zone_outflow_counts[zid] / max(1.0, dt), 2)
            # Decay cumulative counters slowly
            self.zone_inflow_counts[zid] *= 0.8
            self.zone_outflow_counts[zid] *= 0.8

            zone_analytics[zid] = {
                "zone_id": zid,
                "name": roi_info["name"],
                "count": count,
                "density": density,
                "avg_speed_px_sec": avg_speed,
                "inflow_rate": inflow_rate,
                "outflow_rate": outflow_rate,
                "density_change_rate": density_change_rate,
                "polygon": roi_info["polygon"].tolist(),
            }

        return {
            "total_people_count": total_people,
            "tracked_count": len(tracked_objects),
            "zone_analytics": zone_analytics,
            "timestamp": now,
        }
