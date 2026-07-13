"""Historical chain-of-custody provenance model.

ProvenanceRecord predates the production ProvenanceCertificate ingest evidence
model.

It is retained during the 0.2 development cycle for historical test coverage.
New Extended Photo Provenance development must not extend this model.

Current verified-ingest evidence uses:

    mps.models.provenance_certificate.ProvenanceCertificate
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def _utc_now_iso() -> str:
    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass(slots=True)
class ProvenanceRecord:
    provenance_id: str
    session_id: str
    source_path: str
    destination_path: str
    sha256: str
    created_at: str = field(default_factory=_utc_now_iso)
    camera: str | None = None
    source_media: str | None = None
    status: str = "created"

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        source_path: str | Path,
        destination_path: str | Path,
        sha256: str,
        camera: str | None = None,
        source_media: str | None = None,
        status: str = "created",
    ) -> "ProvenanceRecord":
        return cls(
            provenance_id=f"MPS-PROV-{uuid4()}",
            session_id=session_id,
            source_path=str(source_path),
            destination_path=str(destination_path),
            sha256=sha256,
            camera=camera,
            source_media=source_media,
            status=status,
        )

    def to_dict(self) -> dict[str, str | None]:
        return {
            "provenance_id": self.provenance_id,
            "session_id": self.session_id,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "camera": self.camera,
            "source_media": self.source_media,
            "status": self.status,
        }
