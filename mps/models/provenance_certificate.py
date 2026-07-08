from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import json


@dataclass(slots=True)
class ProvenanceCertificate:
    certificate_id: str
    provenance_id: str
    session_id: str
    source_path: str
    destination_path: str
    sha256: str
    camera_model: str
    manifest_path: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return (
            json.dumps(
                self.to_dict(),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
