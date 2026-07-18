"""Sample video frames for vision models that accept images but not video input."""

import base64
import os
import tempfile
from pathlib import Path

import numpy as np

class VideoProcessingError(RuntimeError):
    """Raised for unreadable or frame-less video uploads."""


def extract_sampled_frames(data: bytes, filename: str, sample_count: int = 6) -> list[str]:
    try:
        import cv2
    except ImportError as error:
        raise VideoProcessingError("OpenCV no está instalado. Ejecuta `pip install -r requirements.txt`.") from error

    suffix = Path(filename).suffix or ".mp4"
    temp_path = None
    capture = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(data)
            temp_path = temp_file.name
        capture = cv2.VideoCapture(temp_path)
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames < 1:
            raise VideoProcessingError("No se pudieron leer fotogramas del video.")
        frame_indexes = sorted({int(index) for index in np.linspace(0, total_frames - 1, sample_count)})
        frames = []
        for index in frame_indexes:
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            success, frame = capture.read()
            if not success:
                continue
            encoded, jpeg = cv2.imencode(".jpg", frame)
            if encoded:
                frames.append(f"data:image/jpeg;base64,{base64.b64encode(jpeg.tobytes()).decode('utf-8')}")
        if not frames:
            raise VideoProcessingError("No se pudieron extraer fotogramas utilizables del video.")
        return frames
    finally:
        if capture is not None:
            capture.release()
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
