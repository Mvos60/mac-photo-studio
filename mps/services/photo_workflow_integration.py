from __future__ import annotations

from pathlib import Path
from typing import Any

from mps.config import Settings
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
    record_managed_photo_action,
)


_WORKFLOW_EVENT_TYPES = {
    "edit": ProvenanceEventType.EDIT,
    "derivative": ProvenanceEventType.DERIVATIVE,
    "export": ProvenanceEventType.EXPORT,
}


def record_photo_workflow_action(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
    action: str,
    application: str | None = None,
    application_version: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> PhotoProvenanceRecording:
    try:
        event_type = _WORKFLOW_EVENT_TYPES[action]
    except KeyError as error:
        raise ValueError(
            f"Unsupported photo workflow action: {action}"
        ) from error

    return record_managed_photo_action(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
        event_type=event_type,
        application=application,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )
