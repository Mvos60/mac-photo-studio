import json

from mps.services.provenance_certificate import (
    build_certificate_id,
    create_photo_provenance_certificate,
)


def test_build_certificate_id_is_stable():
    certificate_id = build_certificate_id(
        "12345678-aaaa-bbbb-cccc-000000000000",
        "abcdef1234567890",
    )

    assert certificate_id == "MPS-12345678-ABCDEF123456"


def test_create_photo_provenance_certificate_hashes_destination(tmp_path):
    destination = tmp_path / "photo.ARW"
    destination.write_bytes(b"original raw data")

    certificate = create_photo_provenance_certificate(
        provenance_id="prov-001",
        session_id="12345678-aaaa-bbbb-cccc-000000000000",
        source_path="/media/card/photo.ARW",
        destination_path=destination,
        camera="Sony A7 III",
        source_media="SDCARD-001",
        mps_version="0.2.0-dev",
    )

    assert certificate.certificate_id.startswith("MPS-12345678-")
    assert certificate.provenance_id == "prov-001"
    assert certificate.session_id == "12345678-aaaa-bbbb-cccc-000000000000"
    assert certificate.camera == "Sony A7 III"
    assert certificate.source_media == "SDCARD-001"
    assert certificate.mps_version == "0.2.0-dev"
    assert certificate.verification_status == "verified"
    assert len(certificate.sha256) == 64


def test_certificate_serializes_to_dict(tmp_path):
    destination = tmp_path / "photo.ARW"
    destination.write_bytes(b"raw")

    certificate = create_photo_provenance_certificate(
        provenance_id="prov-002",
        session_id="87654321-aaaa-bbbb-cccc-000000000000",
        source_path="/media/card/photo.ARW",
        destination_path=destination,
    )

    data = certificate.to_dict()

    assert data["certificate_id"].startswith("MPS-87654321-")
    assert data["provenance_id"] == "prov-002"
    assert data["destination_path"] == str(destination)
    assert "created_at" in data


def test_certificate_writes_json_file(tmp_path):
    destination = tmp_path / "photo.ARW"
    destination.write_bytes(b"raw")
    output = tmp_path / "certificate.json"

    certificate = create_photo_provenance_certificate(
        provenance_id="prov-003",
        session_id="99999999-aaaa-bbbb-cccc-000000000000",
        source_path="/media/card/photo.ARW",
        destination_path=destination,
    )

    certificate.write_json(output)

    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["certificate_id"].startswith("MPS-99999999-")
    assert loaded["sha256"] == certificate.sha256
