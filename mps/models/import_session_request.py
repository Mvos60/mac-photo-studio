from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ImportSessionRequest:
    """Information collected before starting an import."""

    year: int
    project: str
    day: str

    raw_folder: Path
    jpeg_folder: Path
