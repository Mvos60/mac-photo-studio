from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from mps.services.provenance_event_chain_validator import (
    validate_provenance_event_chain,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)


@dataclass(slots=True, frozen=True)
class StoredProvenanceEventChainVerification:
    provenance_id: str
    valid: bool
    event_count: int
    errors: list[str] = field(default_factory=list)


def verify_stored_event_chain(
    import_root: str | Path,
    provenance_id: str,
) -> StoredProvenanceEventChainVerification:
    chain = load_event_chain(
        import_root,
        provenance_id,
    )

    validation = validate_provenance_event_chain(
        chain
    )

    return StoredProvenanceEventChainVerification(
        provenance_id=provenance_id,
        valid=validation.valid,
        event_count=validation.event_count,
        errors=list(validation.errors),
    )
