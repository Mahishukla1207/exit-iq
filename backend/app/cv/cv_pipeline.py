import os
import time
import threading
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

from app.cv.stream_manager import VideoStreamManager
from app.cv.video_processor import VideoProcessor
from app.tracking.tracker import CentroidTracker
from app.cv.zone_mapper import ROIZoneMapper


class CVPipeline:
    """
    End-to-End Computer Vision Pipeline:
    UCF Video Stream -> YOLOv8 Person Detection -> Centroid Tracking ->
    ROI Zone Mapping -> Real Crowd Analytics -> LightGBM Prediction ->
    Risk Engine -> Risk-Aware A* Rerouting.
    """

    def __init__(self, video_path: Optional[str] = None, simulation_engine: Optional[Any] = None):
        self.video_path = video_path or os.getenv(
            "UCF_CROWD_VIDEO_PATH", "CrowdDataset/9-19_l.mov"
        )
        self.simulation_engine = simulation_engine

        self.stream_manager = VideoStreamManager(self.video_path)
        self.video_processor = VideoProcessor(conf_threshold=0.25)
        self.tracker = CentroidTracker(max_disappeared=20, max_distance=120.0)
        self.zone_mapper: Optional[ROIZoneMapper] = None

        self.is_running = False
        self.lock = threading.Lock()
        self.latest_annotated_frame: Optional[np.ndarray] = None
        self.latest_analytics: Dict[str, Any] = {}
        self.fps = 30.0
        self._thread: Optional[threading.Thread] = None

    def initialize(self) -> bool:
        """Initializes detector model and video stream."""
        self.video_processor.initialize()
        success = self.stream_manager.start()
        if success:
            w, h = self.stream_manager.get_resolution()
            self.fps = self.stream_manager.get_fps()
            self.zone_mapper = ROIZoneMapper(frame_width=w, frame_height=h)
        return success

    def start(self) -> bool:
        """Starts background frame processing loop."""
        if self.is_running:
            return True

        if not self.stream_manager.is_running():
            if not self.initialize():
                return False

        self.is_running = True
        self._thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        """Stops background frame processing loop."""
        self.is_running = False
        if self.stream_manager:
            self.stream_manager.stop()

    def _processing_loop(self):
        """Continuous background thread reading frames, detecting, tracking, and updating engine."""
        frame_interval = 1.0 / max(1.0, self.fps)

        while self.is_running:
            start_t = time.time()
            ret, frame = self.stream_manager.read_next_frame()
            if not ret or frame is None:
                time.sleep(0.05)
                continue

            # 1. YOLOv8 Person Detection
            detections = self.video_processor.detect_frame(frame)

            # 2. Centroid Tracking
            tracked_objects = self.tracker.update(detections, fps=self.fps)

            # 3. Zone ROI Mapping & Crowd Analytics
            if self.zone_mapper is not None:
                analytics = self.zone_mapper.process_analytics(tracked_objects, fps=self.fps)
            else:
                analytics = {"total_people_count": len(tracked_objects), "zone_analytics": {}}

            # 4. Generate Annotated Frame for UI Display
            annotated_frame = self._annotate_frame(frame, detections, tracked_objects, analytics)

            with self.lock:
                self.latest_annotated_frame = annotated_frame
                self.latest_analytics = analytics

            # 5. Feed metrics into Simulation Engine -> LightGBM -> Risk Engine -> Risk-Aware A*
            if self.simulation_engine is not None:
                self._update_simulation_engine(analytics, detections, tracked_objects)

            elapsed = time.time() - start_t
            sleep_time = max(0.01, frame_interval - elapsed)
            time.sleep(sleep_time)

    def _update_simulation_engine(self, analytics: Dict[str, Any], detections: List[Dict[str, Any]], tracked_objects: Dict[int, Dict[str, Any]]):
        """Injects CV analytics into SimulationEngine state."""
        try:
            zone_data = analytics.get("zone_analytics", {})
            for zid, metrics in zone_data.items():
                if zid in self.simulation_engine.crowd_zones:
                    crowd = self.simulation_engine.crowd_zones[zid]
                    crowd.count = metrics["count"]
                    crowd.density = max(0.1, metrics["density"])
                    crowd.inflow_rate = metrics["inflow_rate"]
                    crowd.outflow_rate = metrics["outflow_rate"]
                    crowd.avg_speed = max(0.5, metrics["avg_speed_px_sec"] / 50.0)  # Map px/sec to approx m/s

            # Populate CV metrics for dashboard telemetry
            self.simulation_engine.latest_cv_analytics = analytics
            self.simulation_engine.cv_active_tracking_ids = len(tracked_objects)
            self.simulation_engine.cv_detections_count = len(detections)

            # Trigger full system recalculation (LightGBM -> Risk Engine -> Risk-Aware A*)
            self.simulation_engine.recalculate_system()
        except Exception as e:
            print(f"[CVPipeline] Error updating simulation engine: {e}")

    def _annotate_frame(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        tracked_objects: Dict[int, Dict[str, Any]],
        analytics: Dict[str, Any],
    ) -> np.ndarray:
        """Annotates frame with bounding boxes, tracking vectors, ROI polygons, and OSD telemetry banner."""
        img = frame.copy()
        h, w = img.shape[:2]

        # 1. Draw Zone ROI Polygons
        zone_data = analytics.get("zone_analytics", {})
        colors = {
            "zone_atrium": (239, 68, 68),    # Red/Pink
            "zone_north": (245, 158, 11),   # Amber/Orange
            "zone_south": (59, 130, 246),   # Blue
            "zone_east": (16, 185, 129),    # Green
        }

        for zid, zinfo in zone_data.items():
            poly = np.array(zinfo["polygon"], dtype=np.int32)
            c = colors.get(zid, (100, 100, 100))
            cv2.polylines(img, [poly], isClosed=True, color=c, thickness=2)
            # Overlay zone header tag
            centroid_x = int(np.mean(poly[:, 0]))
            centroid_y = int(np.mean(poly[:, 1]))
            tag = f"{zinfo['name']}: {zinfo['count']} p (d={zinfo['density']})"
            cv2.putText(img, tag, (centroid_x - 70, centroid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, c, 2)

        # 2. Draw Bounding Boxes, Ground Bottom-Centers, and Tracking IDs
        for obj_id, track in tracked_objects.items():
            bx = track.get("bbox", [0, 0, 0, 0])
            x1, y1, x2, y2 = map(int, bx)
            conf = track.get("confidence", 0.0)
            bc = track.get("bottom_center", [(x1 + x2) // 2, y2])
            bc_pt = (int(bc[0]), int(bc[1]))
            speed = track.get("velocity_px_sec", 0.0)

            # Bounding Box
            cv2.rectangle(img, (x1, y1), (x2, y2), (16, 185, 129), 2)

            # Bounding Box Label
            lbl = f"P#{obj_id} ({int(conf*100)}%) {int(speed)}px/s"
            cv2.rectangle(img, (x1, max(0, y1 - 20)), (x1 + len(lbl) * 8, y1), (16, 185, 129), -1)
            cv2.putText(img, lbl, (x1 + 4, max(12, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (9, 13, 22), 1, cv2.LINE_AA)

            # Ground position circle at feet level
            cv2.circle(img, bc_pt, 4, (56, 189, 248), -1)

            # Trajectory / Velocity vector line
            direction = track.get("direction", {})
            dx = direction.get("dx", 0.0)
            dy = direction.get("dy", 0.0)
            if abs(dx) > 0.05 or abs(dy) > 0.05:
                arrow_end = (int(bc_pt[0] + dx * 25), int(bc_pt[1] + dy * 25))
                cv2.arrowedLine(img, bc_pt, arrow_end, (56, 189, 248), 2, tipLength=0.3)

        # 3. Telemetry OSD Header Banner
        cv2.rectangle(img, (0, 0), (w, 40), (9, 13, 22), -1)
        osd_txt = (
            f"LIVE CV FEED | YOLOv8 + Centroid Tracking | Total: {analytics.get('total_people_count', 0)} Persons | "
            f"Video: {os.path.basename(self.video_path)}"
        )
        cv2.putText(img, osd_txt, (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (52, 211, 153), 2, cv2.LINE_AA)

        return img

    def get_annotated_frame_jpeg(self) -> Optional[bytes]:
        """Encodes latest annotated frame to JPEG byte array for streaming/UI display."""
        with self.lock:
            if self.latest_annotated_frame is None:
                return None
            ret, buffer = cv2.imencode(".jpg", self.latest_annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                return buffer.tobytes()
            return None

    def get_status(self) -> Dict[str, Any]:
        """Returns pipeline status and current crowd analytics."""
        with self.lock:
            return {
                "is_running": self.is_running,
                "video_info": self.stream_manager.get_info(),
                "analytics": self.latest_analytics,
            }
