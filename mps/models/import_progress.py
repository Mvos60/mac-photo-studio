from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportProgress:
    """Progress information for one import workflow phase."""

    current: int
    total: int
    source: Path
    destination: Path
    phase: str = "copying"

    @property
    def percent(self) -> int:
        if self.total <= 0:
            return 100

        value = int(
            (self.current / self.total) * 100
        )
        return max(0, min(value, 100))
