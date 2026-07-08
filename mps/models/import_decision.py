from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportDecision:
    """The planner's final read-only decision."""

    destination: Path
    total_files: int
    estimated_size_bytes: int
    warnings: list[str]
