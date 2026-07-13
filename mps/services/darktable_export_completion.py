from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.config import Settings
from mps.services.darktable_workflow_adapter import (
    record_darktable_export,
)
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
    verify_managed_photo,
)


@dataclass(slots=True, frozen=True)
class DarktableExportCompletion:
    source_path: Path
    output_path: Path
    completed: bool
    recording: PhotoProvenanceRecording | None = None
    verification: PhotoProvenanceVerification | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)


def complete_darktable_export(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
) -> DarktableExportCompletion:
    source = Path(source_path).expanduser()
    output = Path(output_path).expanduser()

    recording = record_darktable_export(
        settings=settings,
        source_path=source,
        output_path=output,
    )

    if not recording.recorded:
        return DarktableExportCompletion(
            source_path=source,
            output_path=output,
            completed=False,
            recording=recording,
            errors=tuple(recording.errors),
        )

    verification = verify_managed_photo(
        settings=settings,
        photo_path=output,
    )

    if not verification.trusted:
        return DarktableExportCompletion(
            source_path=source,
            output_path=output,
            completed=False,
            recording=recording,
            verification=verification,
            errors=tuple(verification.errors),
        )

    return DarktableExportCompletion(
        source_path=source,
        output_path=output,
        completed=True,
        recording=recording,
        verification=verification,
    )
