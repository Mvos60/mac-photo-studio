import json

from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)


def test_certificate_index_serializes_entries():
    entry = ProvenanceCertificateIndexEntry(
        certificate_id="MPS-CERT-1",
        provenance_id="MPS-PROV-1",
        session_id="SESSION-1",
        destination_path="/photos/image.ARW",
        certificate_path="/photos/provenance/MPS-CERT-1.json",
        sha256="abc123",
        camera_model="Sony A7 III",
        created_at="2026-07-08T12:00:00+00:00",
    )

    index = ProvenanceCertificateIndex(entries=[entry])

    data = json.loads(index.to_json())

    assert len(data["entries"]) == 1
    assert data["entries"][0]["certificate_id"] == "MPS-CERT-1"
    assert data["entries"][0]["sha256"] == "abc123"
