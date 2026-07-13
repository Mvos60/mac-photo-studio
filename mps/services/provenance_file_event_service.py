from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_recorder import (
    ProvenanceEventRecordingResult,
)
from mps.services.provenance_identity_resolver import (
    ProvenanceIdentityResolution,
)
from mps.services.provenance_photo_event_service import (
    append_photo_provenance_event,
)
from mps.services.stable_file_hash import stable_file_sha256


@dataclass(slots=True, frozen=True)
class ProvenanceFileEventAppendResult:
    recorded: bool
    output_path: Path
    output_sha256: str | None = None
    identity: ProvenanceIdentityResolution | None = None
    event: ProvenanceEvent | None = None
    recording: ProvenanceEventRecordingResult | None = None
    errors: list[str] = field(default_factory=list)


def append_file_provenance_event(
    *,
    import_root: str | Path,
    output_path: str | Path,
    session_id: str,
    event_type: ProvenanceEventType | str,
    photo_path: str | Path | None = None,
    sha256: str | None = None,
    application: str | None = None,
    application_version: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProvenanceFileEventAppendResult:
    output = Path(output_path).expanduser()

    stable_hash = stable_file_sha256(output)

    if not stable_hash.stable:
        return ProvenanceFileEventAppendResult(
            recorded=False,
            output_path=output,
            errors=list(stable_hash.errors),
        )

    output_sha256 = stable_hash.sha256

    if output_sha256 is None:
        return ProvenanceFileEventAppendResult(
            recorded=False,
            output_path=output,
            errors=[
                "Stable output SHA-256 was not produced"
            ],
        )

    photo_result = append_photo_provenance_event(
        import_root=import_root,
        photo_path=photo_path,
        sha256=sha256,
        session_id=session_id,
        event_type=event_type,
        output_sha256=output_sha256,
        application=application,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )

    return ProvenanceFileEventAppendResult(
        recorded=photo_result.recorded,
        output_path=output,
        output_sha256=output_sha256,
        identity=photo_result.identity,
        event=photo_result.event,
        recording=photo_result.recording,
        errors=list(photo_result.errors),
    )
