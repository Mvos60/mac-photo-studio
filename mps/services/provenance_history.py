from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.models.provenance_event import ProvenanceEvent
from mps.services.provenance_event_chain_verifier import (
    verify_stored_event_chain,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)


@dataclass(slots=True, frozen=True)
class ProvenanceHistory:
    provenance_id: str
    valid: bool
    events: tuple[ProvenanceEvent, ...] = ()
    errors: list[str] = field(default_factory=list)


def read_provenance_history(
    *,
    import_root: str | Path,
    provenance_id: str,
) -> ProvenanceHistory:
    verification = verify_stored_event_chain(
        import_root,
        provenance_id,
    )

    chain = load_event_chain(
        import_root,
        provenance_id,
    )

    events = tuple(chain.ordered_events)
    errors = list(verification.errors)

    if not events:
        errors.append(
            "Provenance event chain is empty"
        )

    return ProvenanceHistory(
        provenance_id=provenance_id,
        valid=verification.valid and bool(events),
        events=events,
        errors=errors,
    )
