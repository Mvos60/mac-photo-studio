from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection


@dataclass(slots=True)
class ImportMediaSession:
    """Photo media collected and processed during one import session."""

    sources: list[CardScanResult] = field(default_factory=list)
    source_fingerprints: set[str] = field(default_factory=set)
    processed_source_files: list[Path] = field(default_factory=list)

    @property
    def selection(self) -> ImportMediaSelection:
        return ImportMediaSelection(
            sources=self.sources.copy(),
        )

    def add_source(
        self,
        source: CardScanResult,
        fingerprint: str,
    ) -> bool:
        if fingerprint in self.source_fingerprints:
            return False

        self.sources.append(source)
        self.source_fingerprints.add(fingerprint)

        return True

    def add_processed_source_files(
        self,
        source_files: list[Path],
    ) -> int:
        known = set(self.processed_source_files)
        added = 0

        for source_file in source_files:
            if source_file in known:
                continue

            self.processed_source_files.append(source_file)
            known.add(source_file)
            added += 1

        return added
