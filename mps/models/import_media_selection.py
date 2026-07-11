from __future__ import annotations

from dataclasses import dataclass

from mps.models.card import CardScanResult


@dataclass(slots=True, frozen=True)
class ImportMediaSelection:
    """Photo media sources currently available to an import session."""

    sources: list[CardScanResult]

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def total_raw_files(self) -> int:
        return sum(source.raw_count for source in self.sources)

    @property
    def total_jpeg_files(self) -> int:
        return sum(source.jpeg_count for source in self.sources)

    @property
    def has_raw(self) -> bool:
        return self.total_raw_files > 0

    @property
    def has_jpeg(self) -> bool:
        return self.total_jpeg_files > 0

    @property
    def empty(self) -> bool:
        return self.source_count == 0
