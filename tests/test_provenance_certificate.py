import json

from mps.models.provenance_certificate import ProvenanceCertificate
from mps.services.provenance_certificate import create_certificate


def test_create_certificate():
    cert = create_certificate(
        session_id="session-001",
        source_path="/card/DCIM/DSC0001.ARW",
        destination_path="/photos/DSC0001.ARW",
        sha256="abcdef123456",
        camera_model="Sony A7 III",
        manifest_path="/photos/import_manifest.json",
    )

    assert cert.certificate_id.startswith("MPS-CERT-")
    assert cert.provenance_id.startswith("MPS-PROV-")
    assert cert.session_id == "session-001"
    assert cert.sha256 == "abcdef123456"
    assert cert.camera_model == "Sony A7 III"


def test_certificate_to_dict():
    cert = ProvenanceCertificate(
        certificate_id="CERT-1",
        provenance_id="PROV-1",
        session_id="SESSION-1",
        source_path="/src",
        destination_path="/dst",
        sha256="123",
        camera_model="Sony",
        manifest_path="/manifest.json",
        created_at="2026-07-08T12:00:00+00:00",
    )

    data = cert.to_dict()

    assert data["certificate_id"] == "CERT-1"
    assert data["provenance_id"] == "PROV-1"
    assert data["session_id"] == "SESSION-1"


def test_certificate_to_json():
    cert = ProvenanceCertificate(
        certificate_id="CERT-2",
        provenance_id="PROV-2",
        session_id="SESSION-2",
        source_path="/src",
        destination_path="/dst",
        sha256="456",
        camera_model="Sony",
        manifest_path="/manifest.json",
        created_at="2026-07-08T12:00:00+00:00",
    )

    payload = json.loads(cert.to_json())

    assert payload["certificate_id"] == "CERT-2"
    assert payload["provenance_id"] == "PROV-2"
    assert payload["sha256"] == "456"
def test_json_ends_with_newline():
    cert = ProvenanceCertificate(
        certificate_id="CERT",
        provenance_id="PROV",
        session_id="SESSION",
        source_path="/src",
        destination_path="/dst",
        sha256="123",
        camera_model="Sony",
        manifest_path="/manifest.json",
        created_at="2026-07-08T12:00:00+00:00",
    )

    assert cert.to_json().endswith("\n")
