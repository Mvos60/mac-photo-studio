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
from mps.services.provenance_file_event_service import (
    append_file_provenance_event,
)
from mps.services.provenance_identity_resolver import (
    resolve_provenance_identity,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index
from mps.services.safe_copy import sha256_file


def _write_original_identity(tmp_path):
    raw = tmp_path / "DSC0001.ARW"
    raw.write_bytes(b"original raw photograph")

    raw_sha256 = sha256_file(raw)

    entry = ProvenanceCertificateIndexEntry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        destination_path=str(raw),
        certificate_path=str(
            tmp_path
            / "provenance"
            / "MPS-CERT-001.json"
        ),
        sha256=raw_sha256,
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
        input_sha256=raw_sha256,
        output_sha256=raw_sha256,
    )

    write_event_for_import(
        ingest,
        tmp_path,
    )

    return raw


def test_file_event_records_derived_output_path(tmp_path):
    raw = _write_original_identity(tmp_path)

    master = tmp_path / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=raw,
        output_path=master,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is True
    assert result.event is not None
    assert result.event.metadata["output_path"] == str(master)


def test_resolve_derived_file_by_path(tmp_path):
    raw = _write_original_identity(tmp_path)

    master = tmp_path / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    append_file_provenance_event(
        import_root=tmp_path,
        photo_path=raw,
        output_path=master,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    identity = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path=master,
    )

    assert identity.resolved is True
    assert identity.provenance_id == "MPS-PROV-001"
    assert identity.destination_path == str(master)
    assert identity.sha256 == sha256_file(master)


def test_resolve_derived_file_by_sha256(tmp_path):
    raw = _write_original_identity(tmp_path)

    master = tmp_path / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    append_file_provenance_event(
        import_root=tmp_path,
        photo_path=raw,
        output_path=master,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    identity = resolve_provenance_identity(
        import_root=tmp_path,
        sha256=sha256_file(master),
    )

    assert identity.resolved is True
    assert identity.provenance_id == "MPS-PROV-001"
    assert identity.destination_path == str(master)


def test_derived_file_can_continue_same_lineage(tmp_path):
    raw = _write_original_identity(tmp_path)

    master = tmp_path / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    edit = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=raw,
        output_path=master,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        application="darktable",
    )

    assert edit.recorded is True

    jpeg = tmp_path / "DSC0001_export.jpg"
    jpeg.write_bytes(b"exported photograph")

    export = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=master,
        output_path=jpeg,
        session_id="MPS-SESSION-003",
        event_type=ProvenanceEventType.EXPORT,
        application="darktable",
    )

    assert export.recorded is True
    assert export.identity is not None
    assert export.identity.provenance_id == "MPS-PROV-001"
    assert export.event is not None
    assert export.event.input_sha256 == sha256_file(master)
    assert export.event.output_sha256 == sha256_file(jpeg)

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert [
        event.event_type
        for event in chain.ordered_events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
        ProvenanceEventType.EXPORT,
    ]


def test_second_generation_derived_file_is_resolvable(tmp_path):
    raw = _write_original_identity(tmp_path)

    master = tmp_path / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    append_file_provenance_event(
        import_root=tmp_path,
        photo_path=raw,
        output_path=master,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    jpeg = tmp_path / "DSC0001_export.jpg"
    jpeg.write_bytes(b"exported photograph")

    append_file_provenance_event(
        import_root=tmp_path,
        photo_path=master,
        output_path=jpeg,
        session_id="MPS-SESSION-003",
        event_type=ProvenanceEventType.EXPORT,
    )

    identity = resolve_provenance_identity(
        import_root=tmp_path,
        photo_path=jpeg,
        sha256=sha256_file(jpeg),
    )

    assert identity.resolved is True
    assert identity.provenance_id == "MPS-PROV-001"
    assert identity.destination_path == str(jpeg)
