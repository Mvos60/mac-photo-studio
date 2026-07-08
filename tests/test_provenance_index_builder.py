from mps.models.provenance_certificate import ProvenanceCertificate
from mps.services.provenance_index_builder import (
    index_entry_from_certificate,
)


def test_index_entry_from_certificate():
    certificate = ProvenanceCertificate(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        source_path="/src",
        destination_path="/dst",
        sha256="abc123",
        camera_model="Sony A7 III",
        manifest_path="/manifest.json",
        created_at="2026-07-08T12:00:00+00:00",
    )

    entry = index_entry_from_certificate(
        certificate,
        "/photos/provenance/CERT-1.json",
    )

    assert entry.certificate_id == "CERT-1"
    assert entry.provenance_id == "PROV-1"
    assert entry.destination_path == "/dst"
    assert entry.certificate_path == "/photos/provenance/CERT-1.json"
