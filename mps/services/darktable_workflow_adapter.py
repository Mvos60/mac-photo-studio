from __future__ import annotations

from pathlib import Path
from typing import Any

from mps.config import Settings
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)
from mps.services.photo_workflow_integration import (
    record_photo_workflow_action,
)
from mps.services.workflow_application_context import (
    resolve_darktable_context,
)


DARKTABLE_APPLICATION = "darktable"


def _darktable_version(
    *,
    settings: Settings,
    application_version: str | None,
) -> str | None:
    if application_version is not None:
        return application_version

    context = resolve_darktable_context(settings)

    return context.version


def record_darktable_edit(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
    application_version: str | None = None,
    description: str = "RAW development",
    metadata: dict[str, Any] | None = None,
) -> PhotoProvenanceRecording:
    resolved_version = _darktable_version(
        settings=settings,
        application_version=application_version,
    )

    return record_photo_workflow_action(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
        action="edit",
        application=DARKTABLE_APPLICATION,
        application_version=resolved_version,
        description=description,
        metadata=metadata,
    )


def record_darktable_export(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
    application_version: str | None = None,
    description: str = "Darktable export",
    metadata: dict[str, Any] | None = None,
) -> PhotoProvenanceRecording:
    resolved_version = _darktable_version(
        settings=settings,
        application_version=application_version,
    )

    return record_photo_workflow_action(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
        action="export",
        application=DARKTABLE_APPLICATION,
        application_version=resolved_version,
        description=description,
        metadata=metadata,
    )
