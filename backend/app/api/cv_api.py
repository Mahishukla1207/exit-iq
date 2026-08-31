import time
from fastapi import APIRouter, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.cv.cv_pipeline import CVPipeline

router = APIRouter(prefix="/cv", tags=["Computer Vision"])

cv_pipeline: Optional[CVPipeline] = None


def set_cv_pipeline(pipeline: CVPipeline):
    global cv_pipeline
    cv_pipeline = pipeline
    return cv_pipeline


class CVStartRequest(BaseModel):
    video_path: Optional[str] = None


@router.post("/start")
def start_cv_pipeline(req: Optional[CVStartRequest] = None):
    global cv_pipeline
    if cv_pipeline is None:
        raise HTTPException(status_code=500, detail="CV pipeline uninitialized")

    video_path = req.video_path if req else None
    if video_path:
        cv_pipeline.video_path = video_path
        cv_pipeline.stream_manager.video_path = video_path

    success = cv_pipeline.start()
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to start CV pipeline with video path: {cv_pipeline.video_path}",
        )
    return {"status": "started", "video_path": cv_pipeline.video_path}


@router.post("/stop")
def stop_cv_pipeline():
    global cv_pipeline
    if cv_pipeline is None:
        raise HTTPException(status_code=500, detail="CV pipeline uninitialized")
    cv_pipeline.stop()
    return {"status": "stopped"}


@router.get("/status")
def get_cv_status():
    if cv_pipeline is None:
        return {"is_running": False, "status": "uninitialized"}
    return cv_pipeline.get_status()


@router.get("/frame")
def get_cv_frame():
    if cv_pipeline is None:
        raise HTTPException(status_code=500, detail="CV pipeline uninitialized")

    jpeg_bytes = cv_pipeline.get_annotated_frame_jpeg()
    if jpeg_bytes is None:
        raise HTTPException(status_code=404, detail="No CV frame available")
    return Response(content=jpeg_bytes, media_type="image/jpeg")


def generate_mjpeg_stream():
    """Generates continuous MJPEG video stream frames for video player."""
    while True:
        if cv_pipeline and cv_pipeline.is_running:
            jpeg_bytes = cv_pipeline.get_annotated_frame_jpeg()
            if jpeg_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
                )
        time.sleep(0.04)  # ~25 FPS stream rate


@router.get("/stream")
def get_cv_stream():
    """Returns continuous MJPEG video stream."""
    if cv_pipeline is None:
        raise HTTPException(status_code=500, detail="CV pipeline uninitialized")

    if not cv_pipeline.is_running:
        cv_pipeline.start()

    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
