from __future__ import annotations

import json
from pathlib import Path

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)


def write_index(
    index: ProvenanceCertificateIndex,
    output_path: str | Path,
) -> Path:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        index.to_json(),
        encoding="utf-8",
    )

    return output


def load_index(
    path: str | Path,
) -> ProvenanceCertificateIndex:
    data = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    entries = [
        ProvenanceCertificateIndexEntry(
            certificate_id=item["certificate_id"],
            provenance_id=item["provenance_id"],
            session_id=item["session_id"],
            destination_path=item["destination_path"],
            certificate_path=item["certificate_path"],
            sha256=item["sha256"],
            camera_model=item["camera_model"],
            created_at=item["created_at"],
        )
        for item in data.get("entries", [])
    ]

    return ProvenanceCertificateIndex(
        entries=entries,
    )


def load_or_create_index(
    path: str | Path,
) -> ProvenanceCertificateIndex:
    index_file = Path(path)

    if index_file.exists():
        return load_index(index_file)

    return ProvenanceCertificateIndex(
        entries=[],
    )
