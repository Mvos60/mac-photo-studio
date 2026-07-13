from mps.models.provenance_certificate import ProvenanceCertificate
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_ingest_event import (
    ingest_event_from_certificate,
)


def _certificate() -> ProvenanceCertificate:
    return ProvenanceCertificate(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        source_path="/media/card/DCIM/DSC0001.ARW",
        destination_path=(
            "/photos/2026/Adriatic/03_Slovenia/DSC0001.ARW"
        ),
        sha256="verified-hash",
        camera_model="ILCE-7M3",
        manifest_path="/photos/import_manifest.json",
        created_at="2026-07-13T10:00:00+00:00",
    )


def test_ingest_event_uses_certificate_identity():
    event = ingest_event_from_certificate(
        _certificate(),
        application_version="0.2.0-dev",
    )

    assert event.provenance_id == "MPS-PROV-001"
    assert event.session_id == "MPS-SESSION-001"
    assert event.event_type is ProvenanceEventType.INGEST


def test_ingest_event_preserves_verified_hash():
    event = ingest_event_from_certificate(
        _certificate(),
        application_version="0.2.0-dev",
    )

    assert event.input_sha256 == "verified-hash"
    assert event.output_sha256 == "verified-hash"


def test_ingest_event_records_mac_photo_studio_context():
    event = ingest_event_from_certificate(
        _certificate(),
        application_version="0.2.0-dev",
    )

    assert event.application == "Mac Photo Studio"
    assert event.application_version == "0.2.0-dev"
    assert event.description == "Verified camera media ingest"


def test_ingest_event_links_certificate_evidence():
    event = ingest_event_from_certificate(
        _certificate(),
        application_version="0.2.0-dev",
    )

    assert event.metadata == {
        "certificate_id": "MPS-CERT-001",
        "source_path": "/media/card/DCIM/DSC0001.ARW",
        "destination_path": (
            "/photos/2026/Adriatic/03_Slovenia/DSC0001.ARW"
        ),
        "camera_model": "ILCE-7M3",
        "manifest_path": "/photos/import_manifest.json",
    }
