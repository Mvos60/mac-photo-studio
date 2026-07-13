from mps.config import Settings
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.photo_provenance_recording import (
    record_managed_photo_action,
)
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)
from mps.services.provenance_event_writer import (
    write_event_for_import,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index
from mps.services.safe_copy import sha256_file


def _settings(tmp_path):
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
        }
    )


def _write_managed_photo(tmp_path):
    import_root = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )
    import_root.mkdir(parents=True)

    photo = import_root / "DSC0001.ARW"
    photo.write_bytes(b"original raw photograph")
    sha256 = sha256_file(photo)

    entry = ProvenanceCertificateIndexEntry(
        certificate_id="MPS-CERT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        destination_path=str(photo),
        certificate_path=str(
            import_root
            / "provenance"
            / "MPS-CERT-001.json"
        ),
        sha256=sha256,
        camera_model="ILCE-7M3",
        created_at="2020-01-01T10:00:00+00:00",
    )

    write_index(
        ProvenanceCertificateIndex(entries=[entry]),
        index_path(import_root),
    )

    write_event_for_import(
        ProvenanceEvent(
            event_id="MPS-EVENT-001",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-001",
            event_type=ProvenanceEventType.INGEST,
            created_at="2020-01-01T10:00:00Z",
            input_sha256=sha256,
            output_sha256=sha256,
        ),
        import_root,
    )

    return import_root, photo


def test_record_managed_photo_edit(tmp_path):
    import_root, photo = _write_managed_photo(tmp_path)

    output = import_root / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    result = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=photo,
        output_path=output,
        event_type=ProvenanceEventType.EDIT,
        application="darktable",
        application_version="5.6.0",
        description="RAW development",
    )

    assert result.recorded is True
    assert result.session_id is not None
    assert result.session_id.startswith("MPS-SESSION-")
    assert result.event is not None
    assert result.event.event_type == ProvenanceEventType.EDIT
    assert result.event.application == "darktable"

    chain = load_event_chain(
        import_root,
        "MPS-PROV-001",
    )

    assert chain.event_count == 2


def test_record_managed_photo_export_from_derived_file(
    tmp_path,
):
    import_root, photo = _write_managed_photo(tmp_path)

    master = import_root / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    edit = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=photo,
        output_path=master,
        event_type=ProvenanceEventType.EDIT,
    )

    assert edit.recorded is True

    output = import_root / "DSC0001_web.jpg"
    output.write_bytes(b"web export")

    export = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=master,
        output_path=output,
        event_type=ProvenanceEventType.EXPORT,
    )

    assert export.recorded is True
    assert export.event is not None
    assert (
        export.event.event_type
        == ProvenanceEventType.EXPORT
    )

    chain = load_event_chain(
        import_root,
        "MPS-PROV-001",
    )

    assert chain.event_count == 3


def test_record_managed_photo_rejects_unmanaged_source(
    tmp_path,
):
    source = tmp_path / "outside.ARW"
    source.write_bytes(b"outside")

    output = tmp_path / "output.tif"
    output.write_bytes(b"output")

    result = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is False
    assert result.session_id is None
    assert result.errors == [
        "Photo is not inside a managed provenance import"
    ]


def test_record_managed_photo_rejects_stale_source(
    tmp_path,
):
    import_root, photo = _write_managed_photo(tmp_path)

    master = import_root / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    edit = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=photo,
        output_path=master,
        event_type=ProvenanceEventType.EDIT,
    )

    assert edit.recorded is True

    second = import_root / "DSC0001_second.tif"
    second.write_bytes(b"second edit")

    result = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=photo,
        output_path=second,
        event_type=ProvenanceEventType.EDIT,
    )

    assert result.recorded is False
    assert result.session_id is None
    assert result.errors == [
        "Source file is not the current provenance chain tip"
    ]

    chain = load_event_chain(
        import_root,
        "MPS-PROV-001",
    )

    assert chain.event_count == 2


def test_record_managed_photo_preserves_context(tmp_path):
    _, photo = _write_managed_photo(tmp_path)

    output = photo.parent / "DSC0001_master.tif"
    output.write_bytes(b"developed photograph")

    result = record_managed_photo_action(
        settings=_settings(tmp_path),
        source_path=photo,
        output_path=output,
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
        "output_path": str(output),
    }
