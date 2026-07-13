from __future__ import annotations

from dataclasses import dataclass, field

from mps.models.provenance_event_chain import ProvenanceEventChain


@dataclass(slots=True, frozen=True)
class ProvenanceEventChainValidation:
    valid: bool
    event_count: int
    errors: list[str] = field(default_factory=list)


def validate_provenance_event_chain(
    chain: ProvenanceEventChain,
) -> ProvenanceEventChainValidation:
    events = chain.ordered_events
    errors: list[str] = []

    for previous, current in zip(
        events,
        events[1:],
    ):
        if previous.output_sha256 is None:
            errors.append(
                f"Event {previous.event_id} has no output SHA-256"
            )
            continue

        if previous.output_sha256 != current.input_sha256:
            errors.append(
                f"Hash continuity mismatch between "
                f"{previous.event_id} and {current.event_id}"
            )

    return ProvenanceEventChainValidation(
        valid=not errors,
        event_count=len(events),
        errors=errors,
    )
