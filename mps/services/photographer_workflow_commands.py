from __future__ import annotations

from pathlib import Path

from mps.config import Settings
from mps.services.darktable_workflow_adapter import (
    record_darktable_edit,
    record_darktable_export,
)
from mps.services.digikam_workflow_adapter import (
    DigiKamWorkflowResult,
    record_digikam_derivative,
    record_digikam_export,
)
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)


def record_digikam_workflow_command(
    *,
    settings: Settings,
    action: str,
    source_path: str | Path,
    output_path: str | Path,
) -> DigiKamWorkflowResult:
    if action == "derivative":
        return record_digikam_derivative(
            settings=settings,
            source_path=source_path,
            output_path=output_path,
        )

    if action == "export":
        return record_digikam_export(
            settings=settings,
            source_path=source_path,
            output_path=output_path,
        )

    raise ValueError(
        f"Unsupported digiKam workflow command: {action}"
    )


def record_darktable_workflow_command(
    *,
    settings: Settings,
    action: str,
    source_path: str | Path,
    output_path: str | Path,
) -> PhotoProvenanceRecording:
    if action == "edit":
        return record_darktable_edit(
            settings=settings,
            source_path=source_path,
            output_path=output_path,
        )

    if action == "export":
        return record_darktable_export(
            settings=settings,
            source_path=source_path,
            output_path=output_path,
        )

    raise ValueError(
        f"Unsupported darktable workflow command: {action}"
    )
