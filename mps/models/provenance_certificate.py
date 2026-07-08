from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


@dataclass(slots=True)
class PhotoProvenanceCertificate:
    certificate_id: str
    provenance_id: str
    session_id: str
    source_path: str
    destination_path: str
    sha256: str
    verification_status: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    camera: str | None = None
    source_media: str | None = None
    mps_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "provenance_id": self.provenance_id,
            "session_id": self.session_id,
            "source_path": self.source_path,
            "destination_path": self.destination_path,
            "sha256": self.sha256,
            "verification_status": self.verification_status,
            "created_at": self.created_at,
            "camera": self.camera,
            "source_media": self.source_media,
            "mps_version": self.mps_version,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output
