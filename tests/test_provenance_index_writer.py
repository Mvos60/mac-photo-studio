import json

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.services.provenance_index_writer import (
    write_index,
)


def test_write_index(tmp_path):
    entry = ProvenanceCertificateIndexEntry(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        destination_path="/photos/test.ARW",
        certificate_path="/photos/provenance/CERT-1.json",
        sha256="abcdef",
        camera_model="Sony A7 III",
        created_at="2026-07-08T12:00:00+00:00",
    )

    index = ProvenanceCertificateIndex(
        entries=[entry],
    )

    output = tmp_path / "index.json"

    written = write_index(
        index,
        output,
    )

    assert written.exists()

    data = json.loads(
        written.read_text(
            encoding="utf-8",
        )
    )

    assert len(data["entries"]) == 1
    assert data["entries"][0]["certificate_id"] == "CERT-1"
