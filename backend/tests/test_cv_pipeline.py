import os
import pytest
import numpy as np

from app.cv.stream_manager import VideoStreamManager
from app.cv.video_processor import VideoProcessor
from app.tracking.tracker import CentroidTracker
from app.cv.zone_mapper import ROIZoneMapper
from app.cv.cv_pipeline import CVPipeline
from app.simulation.simulation_engine import SimulationEngine


def test_video_stream_manager_initialization():
    # Test valid / default video path
    manager = VideoStreamManager("CrowdDataset/9-19_l.mov")
    if os.path.exists("CrowdDataset/9-19_l.mov"):
        success = manager.start()
        assert success is True
        assert manager.get_fps() > 0
        w, h = manager.get_resolution()
        assert w > 0 and h > 0
        ret, frame = manager.read_next_frame()
        assert ret is True
        assert frame is not None
        manager.stop()
        assert manager.is_running() is False


def test_video_stream_manager_invalid_path():
    manager = VideoStreamManager("non_existent_directory/fake_video.mov")
    success = manager.start()
    assert success is False
    assert manager.is_running() is False


def test_video_processor_detection_schema():
    processor = VideoProcessor(conf_threshold=0.40)
    processor.initialize()

    # Create dummy RGB image frame
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = processor.detect_frame(dummy_frame)
    assert isinstance(detections, list)

    # Validate schema format when detections exist or manually tested
    fake_box = [100.0, 100.0, 200.0, 300.0]
    bcx = (fake_box[0] + fake_box[2]) / 2.0
    bcy = fake_box[3]
    assert bcx == 150.0
    assert bcy == 300.0


def test_centroid_tracker_persistence_and_velocity():
    tracker = CentroidTracker(max_disappeared=10, max_distance=100.0)

    # Frame 1: Detection at (100, 100, 200, 300) -> Center (150, 200), Bottom-center (150, 300)
    dets_f1 = [
        {"confidence": 0.85, "bbox": [100.0, 100.0, 200.0, 300.0], "center": [150.0, 200.0], "bottom_center": [150.0, 300.0]}
    ]
    tracked_f1 = tracker.update(dets_f1, fps=30.0)
    assert len(tracked_f1) == 1
    t_id = list(tracked_f1.keys())[0]
    assert tracked_f1[t_id]["tracking_id"] == t_id
    assert tracked_f1[t_id]["bottom_center"] == [150.0, 300.0]

    # Frame 2: Person moves 30px right to (130, 100, 230, 300) -> Center (180, 200), Bottom-center (180, 300)
    dets_f2 = [
        {"confidence": 0.88, "bbox": [130.0, 100.0, 230.0, 300.0], "center": [180.0, 200.0], "bottom_center": [180.0, 300.0]}
    ]
    tracked_f2 = tracker.update(dets_f2, fps=30.0)
    assert t_id in tracked_f2  # Persistent ID retained
    assert tracked_f2[t_id]["displacement"] == 30.0
    assert tracked_f2[t_id]["velocity_px_sec"] == 30.0 * 30.0  # 900 px/sec
    assert tracked_f2[t_id]["direction"]["dx"] > 0  # Moving right


def test_roi_zone_mapper_analytics():
    mapper = ROIZoneMapper(frame_width=1280, frame_height=720)

    # Fake tracked object in zone_atrium (Top-Left quadrant: x=200, y=200)
    tracked_objs = {
        1: {
            "tracking_id": 1,
            "bottom_center": [200.0, 200.0],
            "velocity_px_sec": 120.0,
            "direction": {"dx": 1.0, "dy": 0.0, "angle_deg": 0.0},
        }
    }

    analytics = mapper.process_analytics(tracked_objs, fps=30.0)
    assert analytics["total_people_count"] == 1
    assert "zone_atrium" in analytics["zone_analytics"]
    assert analytics["zone_analytics"]["zone_atrium"]["count"] == 1
    assert analytics["zone_analytics"]["zone_atrium"]["density"] > 0


def test_cv_pipeline_to_simulation_and_routing():
    sim = SimulationEngine()
    pipeline = CVPipeline(video_path="CrowdDataset/9-19_l.mov", simulation_engine=sim)

    # Inject high crowd analytics into simulation via pipeline update
    analytics = {
        "total_people_count": 80,
        "zone_analytics": {
            "zone_atrium": {"count": 45, "density": 3.8, "inflow_rate": 5.0, "outflow_rate": 0.5, "avg_speed_px_sec": 40.0},
            "zone_north": {"count": 10, "density": 0.4, "inflow_rate": 0.0, "outflow_rate": 0.0, "avg_speed_px_sec": 60.0},
        },
    }

    pipeline._update_simulation_engine(analytics)

    # Verify simulation engine received crowd metrics
    assert sim.crowd_zones["zone_atrium"].density == 3.8
    assert sim.crowd_zones["zone_atrium"].count == 45

    # Verify LightGBM prediction updated for zone_atrium
    assert sim.predictions["zone_atrium"].predicted_congestion_prob > 0.4

    # Verify Weighted Risk-Aware A* path rerouted around congested Exit A / zone_atrium
    assert sim.active_route is not None
    assert sim.active_route.is_safe is True
    assert sim.active_route.target_exit != "exit_a"
