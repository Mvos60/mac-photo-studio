from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_recorder import (
    ProvenanceEventRecordingResult,
)
from mps.services.provenance_event_service import (
    append_provenance_event,
)
from mps.services.provenance_identity_resolver import (
    ProvenanceIdentityResolution,
    resolve_provenance_identity,
)


@dataclass(slots=True, frozen=True)
class ProvenancePhotoEventAppendResult:
    recorded: bool
    identity: ProvenanceIdentityResolution
    event: ProvenanceEvent | None = None
    recording: ProvenanceEventRecordingResult | None = None
    errors: list[str] = field(default_factory=list)


def append_photo_provenance_event(
    *,
    import_root: str | Path,
    session_id: str,
    event_type: ProvenanceEventType | str,
    output_sha256: str,
    photo_path: str | Path | None = None,
    sha256: str | None = None,
    application: str | None = None,
    application_version: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProvenancePhotoEventAppendResult:
    identity = resolve_provenance_identity(
        import_root=import_root,
        photo_path=photo_path,
        sha256=sha256,
    )

    if not identity.resolved or identity.provenance_id is None:
        return ProvenancePhotoEventAppendResult(
            recorded=False,
            identity=identity,
            errors=list(identity.errors),
        )

    append_result = append_provenance_event(
        import_root=import_root,
        provenance_id=identity.provenance_id,
        session_id=session_id,
        event_type=event_type,
        output_sha256=output_sha256,
        application=application,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )

    return ProvenancePhotoEventAppendResult(
        recorded=append_result.recorded,
        identity=identity,
        event=append_result.event,
        recording=append_result.recording,
        errors=list(append_result.errors),
    )
