from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
    write_event_chain_for_import,
)
from mps.services.provenance_event_writer import (
    write_event_for_import,
)
from mps.services.provenance_file_event_service import (
    append_file_provenance_event,
)
from mps.services.provenance_file_verifier import (
    verify_provenance_file,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index
from mps.services.safe_copy import sha256_file


def _write_lineage(tmp_path):
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

    return raw, master, jpeg


def test_verify_original_file_is_trusted(tmp_path):
    raw, _, _ = _write_lineage(tmp_path)

    result = verify_provenance_file(
        import_root=tmp_path,
        photo_path=raw,
    )

    assert result.trusted is True
    assert result.actual_sha256 == sha256_file(raw)
    assert result.identity is not None
    assert result.identity.provenance_id == "MPS-PROV-001"
    assert result.chain is not None
    assert result.chain.valid is True
    assert result.chain.event_count == 3
    assert result.errors == []


def test_verify_derived_master_is_trusted(tmp_path):
    _, master, _ = _write_lineage(tmp_path)

    result = verify_provenance_file(
        import_root=tmp_path,
        photo_path=master,
    )

    assert result.trusted is True
    assert result.actual_sha256 == sha256_file(master)
    assert result.identity is not None
    assert result.identity.sha256 == sha256_file(master)
    assert result.chain is not None
    assert result.chain.valid is True


def test_verify_second_generation_derived_file_is_trusted(
    tmp_path,
):
    _, _, jpeg = _write_lineage(tmp_path)

    result = verify_provenance_file(
        import_root=tmp_path,
        photo_path=jpeg,
    )

    assert result.trusted is True
    assert result.actual_sha256 == sha256_file(jpeg)
    assert result.identity is not None
    assert result.identity.provenance_id == "MPS-PROV-001"
    assert result.chain is not None
    assert result.chain.event_count == 3


def test_verify_modified_recorded_file_is_not_trusted(tmp_path):
    _, master, _ = _write_lineage(tmp_path)

    master.write_bytes(b"tampered developed photograph")

    result = verify_provenance_file(
        import_root=tmp_path,
        photo_path=master,
    )

    assert result.trusted is False
    assert result.identity is not None
    assert result.chain is not None
    assert result.errors == [
        "Actual file SHA-256 does not match recorded identity"
    ]


def test_verify_unknown_file_is_not_trusted(tmp_path):
    _write_lineage(tmp_path)

    unknown = tmp_path / "UNKNOWN.JPG"
    unknown.write_bytes(b"unknown photograph")

    result = verify_provenance_file(
        import_root=tmp_path,
        photo_path=unknown,
    )

    assert result.trusted is False
    assert result.actual_sha256 == sha256_file(unknown)
    assert result.identity is not None
    assert result.identity.resolved is False
    assert result.chain is None
    assert result.errors == [
        "No matching provenance identity found"
    ]


def test_verify_file_rejects_broken_lineage(tmp_path):
    _, _, jpeg = _write_lineage(tmp_path)

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    events = chain.ordered_events

    broken_export = ProvenanceEvent(
        event_id=events[2].event_id,
        provenance_id=events[2].provenance_id,
        session_id=events[2].session_id,
        event_type=events[2].event_type,
        created_at=events[2].created_at,
        input_sha256="wrong-parent-hash",
        output_sha256=events[2].output_sha256,
        application=events[2].application,
        application_version=events[2].application_version,
        description=events[2].description,
        metadata=events[2].metadata,
    )

    chain.events = [
        events[0],
        events[1],
        broken_export,
    ]

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = verify_provenance_file(
        import_root=tmp_path,
        photo_path=jpeg,
    )

    assert result.trusted is False
    assert result.chain is not None
    assert result.chain.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].startswith(
        "Hash continuity mismatch between "
    )
