"""Historical chain-of-custody prototype.

This module predates Extended Photo Provenance and the production
ProvenanceCertificate ingest evidence path.

It remains temporarily for historical behaviour and test coverage.

New provenance development must use the Extended Photo Provenance architecture.
"""

import json
from pathlib import Path

from mps.models.provenance_record import ProvenanceRecord


def create_provenance_record(
    *,
    session_id: str,
    source_path: str | Path,
    destination_path: str | Path,
    sha256: str,
    camera: str | None = None,
    source_media: str | None = None,
    status: str = "created",
) -> ProvenanceRecord:
    if not session_id:
        raise ValueError("session_id is required")
    if not sha256:
        raise ValueError("sha256 is required")

    return ProvenanceRecord.create(
        session_id=session_id,
        source_path=source_path,
        destination_path=destination_path,
        sha256=sha256,
        camera=camera,
        source_media=source_media,
        status=status,
    )


def write_provenance_record(
    record: ProvenanceRecord,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            record.to_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def read_provenance_record(
    input_path: str | Path,
) -> ProvenanceRecord:
    data = json.loads(
        Path(input_path).read_text(encoding="utf-8")
    )
    return ProvenanceRecord(**data)


def provenance_filename(
    record: ProvenanceRecord,
) -> str:
    safe_id = (
        record.provenance_id
        .replace(":", "_")
        .replace("/", "_")
    )
    return f"{safe_id}.json"
