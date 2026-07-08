from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportResult:
    """Result of an import engine run."""

    copied: int
    failed: int
    skipped: int
    dry_run: bool
    log_path: Path | None = None

    @property
    def success(self) -> bool:
        return self.failed == 0
