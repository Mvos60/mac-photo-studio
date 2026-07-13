from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_validator import (
    validate_provenance_event_chain,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)
from mps.services.provenance_event_recorder import (
    ProvenanceEventRecordingResult,
    record_provenance_event,
)


@dataclass(slots=True, frozen=True)
class ProvenanceEventAppendResult:
    recorded: bool
    provenance_id: str
    event: ProvenanceEvent | None = None
    recording: ProvenanceEventRecordingResult | None = None
    errors: list[str] = field(default_factory=list)


def append_provenance_event(
    *,
    import_root: str | Path,
    provenance_id: str,
    session_id: str,
    event_type: ProvenanceEventType | str,
    output_sha256: str,
    application: str | None = None,
    application_version: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProvenanceEventAppendResult:
    chain = load_event_chain(
        import_root,
        provenance_id,
    )

    events = chain.ordered_events

    if not events:
        return ProvenanceEventAppendResult(
            recorded=False,
            provenance_id=provenance_id,
            errors=[
                "Existing provenance event history is required"
            ],
        )

    validation = validate_provenance_event_chain(
        chain
    )

    if not validation.valid:
        return ProvenanceEventAppendResult(
            recorded=False,
            provenance_id=provenance_id,
            errors=[
                "Existing provenance event chain is invalid",
                *validation.errors,
            ],
        )

    previous = events[-1]

    if previous.output_sha256 is None:
        return ProvenanceEventAppendResult(
            recorded=False,
            provenance_id=provenance_id,
            errors=[
                f"Event {previous.event_id} has no output SHA-256"
            ],
        )

    event = ProvenanceEvent.create(
        provenance_id=provenance_id,
        session_id=session_id,
        event_type=event_type,
        input_sha256=previous.output_sha256,
        output_sha256=output_sha256,
        application=application,
        application_version=application_version,
        description=description,
        metadata=metadata,
    )

    recording = record_provenance_event(
        import_root=import_root,
        event=event,
    )

    return ProvenanceEventAppendResult(
        recorded=recording.recorded,
        provenance_id=provenance_id,
        event=event,
        recording=recording,
        errors=list(recording.errors),
    )
