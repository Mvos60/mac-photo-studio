import json

from mps.models.provenance_certificate import ProvenanceCertificate
from mps.services.provenance_writer import write_certificate


def test_write_certificate(tmp_path):
    certificate = ProvenanceCertificate(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        source_path="/src",
        destination_path="/dst",
        sha256="123456",
        camera_model="Sony A7 III",
        manifest_path="/manifest.json",
        created_at="2026-07-08T12:00:00+00:00",
    )

    output = tmp_path / "certificate.json"

    result = write_certificate(certificate, output)

    assert result.exists()

    data = json.loads(result.read_text())

    assert data["certificate_id"] == "CERT-1"
    assert data["provenance_id"] == "PROV-1"
    assert data["camera_model"] == "Sony A7 III"


def test_write_certificate_for_import(tmp_path):
    from mps.services.provenance_writer import write_certificate_for_import

    certificate = ProvenanceCertificate(
        certificate_id="MPS-CERT-1234",
        provenance_id="MPS-PROV-1234",
        session_id="SESSION-1",
        source_path="/src",
        destination_path="/dst",
        sha256="123456",
        camera_model="Sony A7 III",
        manifest_path="/manifest.json",
        created_at="2026-07-08T12:00:00+00:00",
    )

    result = write_certificate_for_import(certificate, tmp_path)

    assert result.name == "MPS-CERT-1234.json"
    assert result.parent.name == "provenance"
    assert result.exists()
