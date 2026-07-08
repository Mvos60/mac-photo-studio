from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class VerificationResult:
    expected_count: int
    verified_count: int
    missing_files: list[Path] = field(default_factory=list)
    checksum_mismatches: list[Path] = field(default_factory=list)
    incomplete_entries: int = 0

    @property
    def ok(self) -> bool:
        return (
            self.expected_count == self.verified_count
            and not self.missing_files
            and not self.checksum_mismatches
            and self.incomplete_entries == 0
        )

    @property
    def status(self) -> str:
        return "VERIFIED" if self.ok else "FAILED"
