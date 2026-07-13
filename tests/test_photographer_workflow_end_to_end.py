from pathlib import Path

from mps.config import Settings
from mps.models.provenance_certificate_index import (
    ProvenanceCertificateIndex,
    ProvenanceCertificateIndexEntry,
)
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.darktable_export_completion import (
    complete_darktable_export,
)
from mps.services.darktable_workflow_adapter import (
    record_darktable_edit,
)
from mps.services.digikam_darktable_handoff import (
    handoff_digikam_photo_to_darktable,
)
from mps.services.photo_provenance_history import (
    read_managed_photo_history,
)
from mps.services.photo_provenance_verification import (
    verify_managed_photo,
)
from mps.services.provenance_event_writer import (
    write_event_for_import,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import write_index
from mps.services.safe_copy import sha256_file
from mps.services.workflow_application_context import (
    WorkflowApplicationContext,
)
from mps.services.workflow_application_launcher import (
    WorkflowApplicationLaunch,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
        }
    )


def test_complete_photographer_workflow_preserves_trusted_lineage(
    tmp_path,
    monkeypatch,
):
    settings = _settings(tmp_path)

    import_root = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )
    import_root.mkdir(parents=True)

    raw = import_root / "DSC0001.ARW"
    raw.write_bytes(b"original raw photograph")
    raw_sha256 = sha256_file(raw)

    write_index(
        ProvenanceCertificateIndex(
            entries=[
                ProvenanceCertificateIndexEntry(
                    certificate_id="MPS-CERT-001",
                    provenance_id="MPS-PROV-001",
                    session_id="MPS-SESSION-001",
                    destination_path=str(raw),
                    certificate_path=str(
                        import_root
                        / "provenance"
                        / "MPS-CERT-001.json"
                    ),
                    sha256=raw_sha256,
                    camera_model="ILCE-7M3",
                    created_at="2020-01-01T10:00:00+00:00",
                ),
            ],
        ),
        index_path(import_root),
    )

    write_event_for_import(
        ProvenanceEvent(
            event_id="MPS-EVENT-001",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-001",
            event_type=ProvenanceEventType.INGEST,
            created_at="2020-01-01T10:00:00Z",
            input_sha256=raw_sha256,
            output_sha256=raw_sha256,
            metadata={
                "camera_model": "ILCE-7M3",
            },
        ),
        import_root,
    )

    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "launch_darktable",
        lambda **kwargs: WorkflowApplicationLaunch(
            application="darktable",
            launched=True,
            target=Path(kwargs["photo_path"]),
        ),
    )

    handoff = handoff_digikam_photo_to_darktable(
        settings=settings,
        photo_path=raw,
    )

    assert handoff.handed_off is True

    monkeypatch.setattr(
        "mps.services.darktable_workflow_adapter."
        "resolve_darktable_context",
        lambda settings: WorkflowApplicationContext(
            key="darktable",
            application="darktable",
            available=True,
            version="this is darktable 5.6.0",
        ),
    )

    master = import_root / "DSC0001_master.tif"
    master.write_bytes(b"developed photograph")

    edit = record_darktable_edit(
        settings=settings,
        source_path=raw,
        output_path=master,
    )

    assert edit.recorded is True

    export = import_root / "DSC0001_export.jpg"
    export.write_bytes(b"exported photograph")

    completion = complete_darktable_export(
        settings=settings,
        source_path=master,
        output_path=export,
    )

    assert completion.completed is True

    verification = verify_managed_photo(
        settings=settings,
        photo_path=export,
    )

    assert verification.trusted is True

    history = read_managed_photo_history(
        settings=settings,
        photo_path=export,
    )

    assert history.trusted is True
    assert [
        event.event_type
        for event in history.events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
        ProvenanceEventType.EXPORT,
    ]

    assert history.events[0].metadata["camera_model"] == (
        "ILCE-7M3"
    )
    assert history.events[1].application == "darktable"
    assert history.events[1].application_version == (
        "this is darktable 5.6.0"
    )
    assert history.events[2].application == "darktable"
    assert history.events[2].application_version == (
        "this is darktable 5.6.0"
    )
