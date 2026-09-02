import os
import time
import threading
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any


class VideoStreamManager:
    """
    OpenCV Video Stream Manager for UCF Crowd Footage and Video Input.
    Handles continuous frame decoding, looping, non-blocking frame buffers,
    and graceful handling of missing or corrupted files.
    """

    def __init__(self, video_path: Optional[str] = None):
        self.explicit_path = video_path is not None
        # Default to environment variable or fallback UCF crowd video file
        self.video_path = video_path or os.getenv(
            "UCF_CROWD_VIDEO_PATH", "CrowdDataset/9-19_l.mov"
        )
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active = False
        self.fps = 30.0
        self.width = 1280
        self.height = 720
        self.total_frames = 0
        self.current_frame_idx = 0
        self.last_frame: Optional[np.ndarray] = None
        self.lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Initializes VideoCapture and starts background capture thread."""
        with self.lock:
            if self.is_active:
                return True

            if not os.path.exists(self.video_path):
                if not self.explicit_path:
                    # Search CrowdDataset for fallback video file only if no explicit path was forced
                    search_dirs = [
                        "CrowdDataset",
                        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "CrowdDataset")),
                        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "CrowdDataset")),
                    ]
                    for dataset_dir in search_dirs:
                        if os.path.exists(dataset_dir):
                            candidates = [
                                os.path.join(dataset_dir, f)
                                for f in os.listdir(dataset_dir)
                                if f.lower().endswith((".mov", ".mp4", ".avi", ".mkv"))
                            ]
                            if candidates:
                                self.video_path = candidates[0]
                                break

            if not os.path.exists(self.video_path):
                print(f"[VideoStreamManager] Video file not found at: {self.video_path}")
                return False

            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print(f"[VideoStreamManager] Failed to open video file: {self.video_path}")
                return False

            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            self.is_active = True
            self.current_frame_idx = 0

            # Read initial frame
            ret, frame = self.cap.read()
            if ret:
                self.last_frame = frame
            else:
                self.is_active = False
                return False

            return True

    def stop(self):
        """Stops capture and releases video resources."""
        with self.lock:
            self.is_active = False
            if self.cap is not None:
                self.cap.release()
                self.cap = None

    def read_next_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Reads next frame from video source. Loops seamlessly when EOF is reached.
        """
        with self.lock:
            if not self.is_active or self.cap is None:
                return False, None

            ret, frame = self.cap.read()
            if not ret:
                # Loop video to beginning for continuous demo
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                self.current_frame_idx = 0

            if ret and frame is not None:
                self.last_frame = frame
                self.current_frame_idx += 1
                return True, frame.copy()
            elif self.last_frame is not None:
                return True, self.last_frame.copy()
            else:
                return False, None

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Returns the most recently decoded frame (non-blocking)."""
        with self.lock:
            if self.last_frame is not None:
                return True, self.last_frame.copy()
            return False, None

    def get_fps(self) -> float:
        return self.fps

    def get_resolution(self) -> Tuple[int, int]:
        return self.width, self.height

    def is_running(self) -> bool:
        with self.lock:
            return self.is_active and self.cap is not None and self.cap.isOpened()

    def get_info(self) -> Dict[str, Any]:
        return {
            "video_path": self.video_path,
            "is_running": self.is_running(),
            "fps": round(self.fps, 2),
            "resolution": [self.width, self.height],
            "total_frames": self.total_frames,
            "current_frame": self.current_frame_idx,
        }
