from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mps.models.provenance_event_type import ProvenanceEventType


def _utc_now_iso() -> str:
    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(slots=True, frozen=True)
class ProvenanceEvent:
    event_id: str
    provenance_id: str
    session_id: str
    event_type: ProvenanceEventType
    created_at: str
    input_sha256: str
    output_sha256: str | None = None
    application: str | None = None
    application_version: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        provenance_id: str,
        session_id: str,
        event_type: ProvenanceEventType | str,
        input_sha256: str,
        output_sha256: str | None = None,
        application: str | None = None,
        application_version: str | None = None,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ProvenanceEvent":
        if not provenance_id:
            raise ValueError("provenance_id is required")

        if not session_id:
            raise ValueError("session_id is required")

        if not event_type:
            raise ValueError("event_type is required")

        if not input_sha256:
            raise ValueError("input_sha256 is required")

        resolved_event_type = ProvenanceEventType(event_type)

        return cls(
            event_id=f"MPS-EVENT-{uuid4()}",
            provenance_id=provenance_id,
            session_id=session_id,
            event_type=resolved_event_type,
            created_at=_utc_now_iso(),
            input_sha256=input_sha256,
            output_sha256=output_sha256,
            application=application,
            application_version=application_version,
            description=description,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ProvenanceEvent":
        return cls(
            event_id=data["event_id"],
            provenance_id=data["provenance_id"],
            session_id=data["session_id"],
            event_type=ProvenanceEventType(
                data["event_type"]
            ),
            created_at=data["created_at"],
            input_sha256=data["input_sha256"],
            output_sha256=data.get("output_sha256"),
            application=data.get("application"),
            application_version=data.get(
                "application_version"
            ),
            description=data.get("description"),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        return data
