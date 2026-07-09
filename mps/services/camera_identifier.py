from __future__ import annotations

import subprocess
from pathlib import Path


UNKNOWN_CAMERA = "Unknown camera"


def identify_camera_model(photo_path: str | Path) -> str:
    """Identify the camera model used for a photo.

    Uses exiftool when available. Returns a safe fallback instead of raising
    when the file cannot be read, exiftool is missing, or no model is present.
    """

    path = Path(photo_path).expanduser()

    if not path.exists() or not path.is_file():
        return UNKNOWN_CAMERA

    try:
        completed = subprocess.run(
            [
                "exiftool",
                "-s3",
                "-Model",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return UNKNOWN_CAMERA

    if completed.returncode != 0:
        return UNKNOWN_CAMERA

    model = completed.stdout.strip()

    return model or UNKNOWN_CAMERA
