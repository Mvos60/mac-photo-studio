from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ImportFileResultStatus(str, Enum):
    VERIFIED = "verified"
    SKIPPED = "skipped"
    FAILED = "failed"


class ImportFileMediaType(str, Enum):
    RAW = "raw"
    JPEG = "jpeg"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ImportFileResult:
    """Observer-only result for one file considered by an import batch."""

    source: Path
    destination: Path | None
    media_type: ImportFileMediaType
    status: ImportFileResultStatus
    reason_code: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, Path):
            raise TypeError("Import file result source must be a Path")
        if not isinstance(self.media_type, ImportFileMediaType):
            raise TypeError("Invalid import file media type")
        if not isinstance(self.status, ImportFileResultStatus):
            raise TypeError("Invalid import file result status")
        if self.destination is not None and not isinstance(
            self.destination, Path
        ):
            raise TypeError("Import file result destination must be a Path")
        if (
            self.status is not ImportFileResultStatus.SKIPPED
            and self.destination is None
        ):
            raise ValueError("Verified and failed results require a destination")
        if self.reason_code is not None and not self.reason_code.strip():
            raise ValueError("Import file result reason code cannot be blank")
        if self.detail is not None and not self.detail.strip():
            raise ValueError("Import file result detail cannot be blank")
