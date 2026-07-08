from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImportResult:
    """Result of an import engine run."""

    copied: int
    failed: int
    skipped: int
    dry_run: bool

    @property
    def success(self) -> bool:
        return self.failed == 0
