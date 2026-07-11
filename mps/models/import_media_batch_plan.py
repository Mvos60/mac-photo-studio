from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mps.models.import_decision import ImportDecision
from mps.models.import_media_selection import ImportMediaSelection


@dataclass(slots=True, frozen=True)
class ImportMediaBatchPlan:
    selection: ImportMediaSelection
    destination: Path
    decision: ImportDecision

    @property
    def total_files(self) -> int:
        return self.decision.total_files

    @property
    def estimated_size_bytes(self) -> int:
        return self.decision.estimated_size_bytes
