from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from mps.config import Settings
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.extended_photo_provenance import (
    append_file_provenance_event,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
    verify_managed_photo,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)


@dataclass(slots=True, frozen=True)
class PhotoProvenanceRecording:
    source_path: Path
    output_path: Path
    recorded: bool
    session_id: str | None = None
    event: ProvenanceEvent | None = None
    verification: PhotoProvenanceVerification | None = None
    errors: list[str] = field(default_factory=list)


def _photographer_action_session_id() -> str:
    return f"MPS-SESSION-{uuid4()}"


def record_managed_photo_action(
    *,
    settings: Settings,
    source_path: str | Path,
    output_path: str | Path,
    event_type: ProvenanceEventType | str,
    application: str | None = None,
    application_version: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> PhotoProvenanceRecording:
    source = Path(source_path).expanduser()
    output = Path(output_path).expanduser()

    verification = verify_managed_photo(
        settings=settings,
        photo_path=source,
    )

    if (
        not verification.trusted
        or verification.import_root is None
        or verification.verification is None
        or verification.verification.identity is None
    ):
        return PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=False,
            verification=verification,
            errors=list(verification.errors),
        )

    identity = verification.verification.identity

    if identity.provenance_id is None:
        return PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=False,
            verification=verification,
            errors=[
                "Source provenance identity is unavailable"
            ],
        )

    chain = load_event_chain(
        verification.import_root,
        identity.provenance_id,
    )
    events = chain.ordered_events

    if not events:
        return PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=False,
            verification=verification,
            errors=[
                "Source provenance event chain is empty"
            ],
        )

    chain_tip_sha256 = events[-1].output_sha256

    if (
        verification.verification.actual_sha256
        != chain_tip_sha256
    ):
        return PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=False,
            verification=verification,
            errors=[
                "Source file is not the current provenance chain tip"
            ],
        )

    session_id = _photographer_action_session_id()

    result = append_file_provenance_event(
        import_root=verification.import_root,
        photo_path=source,
        output_path=output,
        session_id=session_id,
        event_type=event_type,
        application=application,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )

    return PhotoProvenanceRecording(
        source_path=source,
        output_path=output,
        recorded=result.recorded,
        session_id=session_id,
        event=result.event,
        verification=verification,
        errors=list(result.errors),
    )
