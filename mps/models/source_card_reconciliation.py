from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SourceCardReconciliation:
    expected_sources: int
    reconciled_sources: int
    missing_from_manifest: list[Path] = field(default_factory=list)
    unexpected_manifest_sources: list[Path] = field(default_factory=list)
    unverified_destinations: list[Path] = field(default_factory=list)
    provenance_failures: list[Path] = field(default_factory=list)

    @property
    def reconciled(self) -> bool:
        return (
            self.expected_sources == self.reconciled_sources
            and not self.missing_from_manifest
            and not self.unexpected_manifest_sources
            and not self.unverified_destinations
            and not self.provenance_failures
        )

    @property
    def card_status(self) -> str:
        if self.reconciled:
            return "SOURCE CARDS RECONCILED"

        return "SOURCE CARDS NOT RECONCILED"
