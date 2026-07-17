from __future__ import annotations

from pathlib import Path

from mps.config import load_settings


def get_photo_library() -> Path:
    """
    Return the configured photo library.

    This is the canonical entry point for every component that
    needs access to the user's photo archive.
    """
    settings = load_settings()

    return Path(
        settings.get(
            "paths.photos_root",
            "~/Pictures",
        )
    ).expanduser()
