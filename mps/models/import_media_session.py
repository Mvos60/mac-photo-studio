from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.models.import_media_selection import ImportMediaSelection


@dataclass(frozen=True, slots=True)
class ImportMediaSessionDestination:
    selection: ImportDestinationSelection
    import_root: Path

    def __post_init__(self) -> None:
        if not isinstance(
            self.selection,
            ImportDestinationSelection,
        ):
            raise ValueError(
                "Destination selection must be an "
                "ImportDestinationSelection"
            )

        if not isinstance(self.import_root, Path):
            raise ValueError(
                "Destination import_root must be a Path"
            )


@dataclass(slots=True)
class ImportMediaSession:
    """Photo media collected and processed during one import session."""

    session_id: str | None = None
    sources: list[CardScanResult] = field(default_factory=list)
    source_fingerprints: set[str] = field(default_factory=set)
    processed_source_files: list[Path] = field(default_factory=list)
    destination: ImportMediaSessionDestination | None = None

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
