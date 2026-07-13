from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mps.config import Settings
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)
from mps.services.photo_workflow_integration import (
    record_photo_workflow_action,
)


DIGIKAM_APPLICATION = "digiKam"

_CATALOGUE_ACTIONS = {
    "album",
    "face",
    "rating",
    "search",
    "tag",
}


@dataclass(slots=True, frozen=True)
class DigiKamWorkflowResult:
    action: str
    provenance_relevant: bool
    recorded: bool
    recording: PhotoProvenanceRecording | None = None
    errors: list[str] = field(default_factory=list)


def handle_digikam_catalogue_action(
    *,
    action: str,
) -> DigiKamWorkflowResult:
    if action not in _CATALOGUE_ACTIONS:
        raise ValueError(
            f"Unsupported digiKam catalogue action: {action}"
        )

    return DigiKamWorkflowResult(
        action=action,
        provenance_relevant=False,
        recorded=False,
    )


def record_digikam_derivative(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
    application_version: str | None = None,
    description: str = "digiKam derived file",
    metadata: dict[str, Any] | None = None,
) -> DigiKamWorkflowResult:
    recording = record_photo_workflow_action(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
        action="derivative",
        application=DIGIKAM_APPLICATION,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )

    return DigiKamWorkflowResult(
        action="derivative",
        provenance_relevant=True,
        recorded=recording.recorded,
        recording=recording,
        errors=list(recording.errors),
    )


def record_digikam_export(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
    application_version: str | None = None,
    description: str = "digiKam export",
    metadata: dict[str, Any] | None = None,
) -> DigiKamWorkflowResult:
    recording = record_photo_workflow_action(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
        action="export",
        application=DIGIKAM_APPLICATION,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )

    return DigiKamWorkflowResult(
        action="export",
        provenance_relevant=True,
        recorded=recording.recorded,
        recording=recording,
        errors=list(recording.errors),
    )
