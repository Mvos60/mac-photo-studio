from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CopyOperation:
    """One planned file copy."""

    source: Path
    destination: Path


@dataclass(frozen=True)
class ImportDecision:
    """The planner's final read-only decision."""

    destination: Path
    total_files: int
    estimated_size_bytes: int
    copy_operations: list[CopyOperation]
    warnings: list[str]
