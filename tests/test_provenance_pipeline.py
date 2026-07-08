import json

from mps.services.provenance_pipeline import create_and_write_certificate


def test_create_and_write_certificate(tmp_path):
    certificate, written_path = create_and_write_certificate(
        import_root=tmp_path,
        session_id="SESSION-001",
        source_path="/card/DCIM/DSC0001.ARW",
        destination_path="/photos/DSC0001.ARW",
        sha256="abc123",
        camera_model="Sony A7 III",
        manifest_path="/photos/import_manifest.json",
    )

    assert certificate.certificate_id.startswith("MPS-CERT-")
    assert certificate.provenance_id.startswith("MPS-PROV-")

    assert written_path.exists()
    assert written_path.parent.name == "provenance"
    assert written_path.name == f"{certificate.certificate_id}.json"

    data = json.loads(written_path.read_text(encoding="utf-8"))

    assert data["certificate_id"] == certificate.certificate_id
    assert data["provenance_id"] == certificate.provenance_id
    assert data["session_id"] == "SESSION-001"
    assert data["sha256"] == "abc123"
    assert data["camera_model"] == "Sony A7 III"
