from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mps.models.provenance_event import ProvenanceEvent


@dataclass(slots=True)
class ProvenanceEventChain:
    provenance_id: str
    events: list[ProvenanceEvent] = field(default_factory=list)

    def add_event(
        self,
        event: ProvenanceEvent,
    ) -> None:
        if event.provenance_id != self.provenance_id:
            raise ValueError(
                "event provenance_id does not match chain"
            )

        self.events.append(event)

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def ordered_events(self) -> list[ProvenanceEvent]:
        return sorted(
            self.events,
            key=lambda event: (
                event.created_at,
                event.event_id,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_id": self.provenance_id,
            "event_count": self.event_count,
            "events": [
                event.to_dict()
                for event in self.ordered_events
            ],
        }
