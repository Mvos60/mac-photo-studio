from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportProgress:
    """Progress information for one import operation."""

    current: int
    total: int
    source: Path
    destination: Path

    @property
    def percent(self) -> int:
        if self.total == 0:
            return 100
        return int((self.current / self.total) * 100)
