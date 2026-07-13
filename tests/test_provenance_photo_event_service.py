from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)
from mps.services.provenance_event_writer import (
    write_event_for_import,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index
from mps.services.provenance_photo_event_service import (
    append_photo_provenance_event,
)


def _write_photo_identity(tmp_path) -> None:
    entry = ProvenanceCertificateIndexEntry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        destination_path="/photos/DSC0001.ARW",
        certificate_path=(
            "/photos/provenance/MPS-CERT-001.json"
        ),
        sha256="raw-hash",
        camera_model="ILCE-7M3",
        created_at="2020-01-01T10:00:00+00:00",
    )

    write_index(
        ProvenanceCertificateIndex(
            entries=[entry],
        ),
        index_path(tmp_path),
    )

    ingest = ProvenanceEvent(
        event_id="MPS-EVENT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=ProvenanceEventType.INGEST,
        created_at="2020-01-01T10:00:00Z",
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    write_event_for_import(
        ingest,
        tmp_path,
    )


def test_append_photo_event_resolves_by_path(tmp_path):
    _write_photo_identity(tmp_path)

    result = append_photo_provenance_event(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is True
    assert result.identity.resolved is True
    assert result.identity.provenance_id == "MPS-PROV-001"
    assert result.event is not None
    assert result.event.input_sha256 == "raw-hash"
    assert result.event.output_sha256 == "master-hash"


def test_append_photo_event_resolves_by_sha256(tmp_path):
    _write_photo_identity(tmp_path)

    result = append_photo_provenance_event(
        import_root=tmp_path,
        sha256="raw-hash",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is True
    assert result.identity.provenance_id == "MPS-PROV-001"


def test_append_photo_event_preserves_application_context(
    tmp_path,
):
    _write_photo_identity(tmp_path)

    result = append_photo_provenance_event(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
        application="darktable",
        application_version="5.6.0",
        description="RAW development",
        metadata={
            "workflow": "RAW-first",
        },
    )

    assert result.recorded is True
    assert result.event is not None
    assert result.event.application == "darktable"
    assert result.event.application_version == "5.6.0"
    assert result.event.description == "RAW development"
    assert result.event.metadata == {
        "workflow": "RAW-first",
    }


def test_append_photo_event_extends_correct_chain(tmp_path):
    _write_photo_identity(tmp_path)

    result = append_photo_provenance_event(
        import_root=tmp_path,
        photo_path="/photos/DSC0001.ARW",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is True

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert chain.event_count == 2

    assert [
        event.event_type
        for event in chain.ordered_events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
    ]


def test_append_photo_event_reports_unresolved_identity(
    tmp_path,
):
    result = append_photo_provenance_event(
        import_root=tmp_path,
        photo_path="/photos/UNKNOWN.ARW",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is False
    assert result.identity.resolved is False
    assert result.event is None
    assert result.recording is None
    assert result.errors == [
        "Provenance certificate index does not exist"
    ]


def test_append_photo_event_requires_identity_search_value(
    tmp_path,
):
    result = append_photo_provenance_event(
        import_root=tmp_path,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is False
    assert result.identity.resolved is False
    assert result.errors == [
        "photo_path or sha256 is required"
    ]
