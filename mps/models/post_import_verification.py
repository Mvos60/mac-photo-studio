from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, frozen=True)
class PostImportVerification:
    import_root: Path
    manifest_path: Path
    expected_files: int
    verified_files: int
    missing_files: list[Path] = field(default_factory=list)
    checksum_mismatches: list[Path] = field(default_factory=list)
    incomplete_entries: int = 0
    expected_certificates: int = 0
    verified_certificates: int = 0
    provenance_errors: list[str] = field(default_factory=list)

    @property
    def safe_to_release(self) -> bool:
        return (
            self.expected_files == self.verified_files
            and not self.missing_files
            and not self.checksum_mismatches
            and self.incomplete_entries == 0
            and self.expected_certificates == self.verified_certificates
            and not self.provenance_errors
        )

    @property
    def card_status(self) -> str:
        if self.safe_to_release:
            return "SAFE TO RELEASE"

        return "DO NOT RELEASE"
