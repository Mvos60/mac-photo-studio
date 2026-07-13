from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_validator import (
    validate_provenance_event_chain,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)
from mps.services.provenance_event_paths import event_path
from mps.services.provenance_event_writer import (
    write_event_for_import,
)


@dataclass(slots=True, frozen=True)
class ProvenanceEventRecordingResult:
    recorded: bool
    provenance_id: str
    event_id: str
    event_count: int
    event_path: Path | None = None
    errors: list[str] = field(default_factory=list)


def record_provenance_event(
    *,
    import_root: str | Path,
    event: ProvenanceEvent,
) -> ProvenanceEventRecordingResult:
    chain = load_event_chain(
        import_root,
        event.provenance_id,
    )

    existing_validation = validate_provenance_event_chain(
        chain
    )

    if not existing_validation.valid:
        return ProvenanceEventRecordingResult(
            recorded=False,
            provenance_id=event.provenance_id,
            event_id=event.event_id,
            event_count=chain.event_count,
            errors=[
                "Existing provenance event chain is invalid",
                *existing_validation.errors,
            ],
        )

    output_path = event_path(
        import_root,
        event.provenance_id,
        event.event_id,
    )

    if output_path.exists():
        return ProvenanceEventRecordingResult(
            recorded=False,
            provenance_id=event.provenance_id,
            event_id=event.event_id,
            event_count=chain.event_count,
            errors=[
                f"Event {event.event_id} already exists"
            ],
        )

    existing_events = chain.ordered_events

    if (
        not existing_events
        and event.event_type is not ProvenanceEventType.INGEST
    ):
        return ProvenanceEventRecordingResult(
            recorded=False,
            provenance_id=event.provenance_id,
            event_id=event.event_id,
            event_count=chain.event_count,
            errors=[
                "Provenance event history must begin with ingest"
            ],
        )

    if (
        existing_events
        and event.created_at < existing_events[-1].created_at
    ):
        return ProvenanceEventRecordingResult(
            recorded=False,
            provenance_id=event.provenance_id,
            event_id=event.event_id,
            event_count=chain.event_count,
            errors=[
                f"Event {event.event_id} predates existing history"
            ],
        )

    chain.add_event(event)

    updated_validation = validate_provenance_event_chain(
        chain
    )

    if not updated_validation.valid:
        return ProvenanceEventRecordingResult(
            recorded=False,
            provenance_id=event.provenance_id,
            event_id=event.event_id,
            event_count=chain.event_count,
            errors=list(updated_validation.errors),
        )

    written_path = write_event_for_import(
        event,
        import_root,
    )

    return ProvenanceEventRecordingResult(
        recorded=True,
        provenance_id=event.provenance_id,
        event_id=event.event_id,
        event_count=chain.event_count,
        event_path=written_path,
        errors=[],
    )
