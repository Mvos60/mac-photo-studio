from dataclasses import dataclass, asdict
from typing import Any
import json


@dataclass(slots=True)
class ProvenanceCertificateIndexEntry:
    certificate_id: str
    provenance_id: str
    session_id: str
    destination_path: str
    certificate_path: str
    sha256: str
    camera_model: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProvenanceCertificateIndex:
    entries: list[ProvenanceCertificateIndexEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                entry.to_dict()
                for entry in self.entries
            ]
        }

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
