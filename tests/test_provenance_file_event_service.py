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
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index
from mps.services.safe_copy import sha256_file


def _write_photo_identity(tmp_path):
    photo = tmp_path / "DSC0001.ARW"
    photo.write_bytes(b"original raw photograph")

    raw_sha256 = sha256_file(photo)

    entry = ProvenanceCertificateIndexEntry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        destination_path=str(photo),
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

    return photo, raw_sha256


def test_append_file_event_hashes_actual_output_file(tmp_path):
    photo, raw_sha256 = _write_photo_identity(tmp_path)

    output = tmp_path / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=photo,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    expected_sha256 = sha256_file(output)

    assert result.recorded is True
    assert result.output_sha256 == expected_sha256
    assert result.event is not None
    assert result.event.input_sha256 == raw_sha256
    assert result.event.output_sha256 == expected_sha256


def test_append_file_event_extends_photo_chain(tmp_path):
    photo, _ = _write_photo_identity(tmp_path)

    output = tmp_path / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=photo,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is True

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert chain.event_count == 2

    ingest, edit = chain.ordered_events

    assert ingest.output_sha256 == edit.input_sha256
    assert edit.output_sha256 == sha256_file(output)


def test_append_file_event_resolves_source_by_sha256(tmp_path):
    _, raw_sha256 = _write_photo_identity(tmp_path)

    output = tmp_path / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    result = append_file_provenance_event(
        import_root=tmp_path,
        sha256=raw_sha256,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is True
    assert result.identity is not None
    assert result.identity.provenance_id == "MPS-PROV-001"


def test_append_file_event_preserves_application_context(tmp_path):
    photo, _ = _write_photo_identity(tmp_path)

    output = tmp_path / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=photo,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
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


def test_append_file_event_rejects_missing_output(tmp_path):
    photo, _ = _write_photo_identity(tmp_path)

    output = tmp_path / "missing.tif"

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=photo,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is False
    assert result.output_sha256 is None
    assert result.identity is None
    assert result.event is None
    assert result.errors == [
        "File does not exist"
    ]


def test_append_file_event_rejects_output_directory(tmp_path):
    photo, _ = _write_photo_identity(tmp_path)

    output = tmp_path / "output"
    output.mkdir()

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=photo,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is False
    assert result.output_sha256 is None
    assert result.errors == [
        "Path is not a file"
    ]


def test_append_file_event_refuses_unstable_output(
    tmp_path,
    monkeypatch,
):
    photo, _ = _write_photo_identity(tmp_path)

    output = tmp_path / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    from mps.services import provenance_file_event_service
    from mps.services.stable_file_hash import (
        StableFileHashResult,
    )

    monkeypatch.setattr(
        provenance_file_event_service,
        "stable_file_sha256",
        lambda path: StableFileHashResult(
            stable=False,
            path=output,
            errors=(
                "File changed while SHA-256 was being calculated",
            ),
        ),
    )

    result = append_file_provenance_event(
        import_root=tmp_path,
        photo_path=photo,
        output_path=output,
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is False
    assert result.output_sha256 is None
    assert result.event is None
    assert result.errors == [
        "File changed while SHA-256 was being calculated"
    ]

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert chain.event_count == 1
