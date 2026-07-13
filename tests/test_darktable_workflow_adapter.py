from pathlib import Path

from mps.config import Settings
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.darktable_workflow_adapter import (
    DARKTABLE_APPLICATION,
    record_darktable_edit,
    record_darktable_export,
)
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
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


def _recording(
    *,
    source_path: str | Path,
    output_path: str | Path,
    event_type: ProvenanceEventType,
    recorded: bool = True,
) -> PhotoProvenanceRecording:
    event = None

    if recorded:
        event = ProvenanceEvent(
            event_id="MPS-EVENT-TEST",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-TEST",
            event_type=event_type,
            created_at="2026-07-13T10:00:00Z",
            input_sha256="input-hash",
            output_sha256="output-hash",
        )

    return PhotoProvenanceRecording(
        source_path=Path(source_path),
        output_path=Path(output_path),
        recorded=recorded,
        session_id=(
            "MPS-SESSION-TEST"
            if recorded
            else None
        ),
        event=event,
    )


def test_darktable_edit_maps_to_edit_workflow(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "DSC0001.ARW"
    output = tmp_path / "DSC0001_master.tif"

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.EDIT,
        )

    monkeypatch.setattr(
        "mps.services.darktable_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_darktable_edit(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        application_version="5.6.0",
    )

    assert result.recorded is True
    assert called[0]["action"] == "edit"
    assert called[0]["application"] == DARKTABLE_APPLICATION
    assert called[0]["application_version"] == "5.6.0"
    assert called[0]["description"] == "RAW development"


def test_darktable_export_maps_to_export_workflow(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "DSC0001_master.tif"
    output = tmp_path / "DSC0001_web.jpg"

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.EXPORT,
        )

    monkeypatch.setattr(
        "mps.services.darktable_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_darktable_export(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        application_version="5.6.0",
    )

    assert result.recorded is True
    assert called[0]["action"] == "export"
    assert called[0]["application"] == DARKTABLE_APPLICATION
    assert called[0]["application_version"] == "5.6.0"
    assert called[0]["description"] == "Darktable export"


def test_darktable_edit_preserves_custom_context(
    tmp_path,
    monkeypatch,
):
    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.EDIT,
        )

    monkeypatch.setattr(
        "mps.services.darktable_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_darktable_edit(
        settings=_settings(tmp_path),
        source_path=tmp_path / "DSC0001.ARW",
        output_path=tmp_path / "DSC0001_master.tif",
        application_version="5.6.0",
        description="Creative RAW development",
        metadata={
            "workflow": "RAW-first",
            "profile": "Adriatic colour",
        },
    )

    assert result.recorded is True
    assert (
        called[0]["description"]
        == "Creative RAW development"
    )
    assert called[0]["metadata"] == {
        "workflow": "RAW-first",
        "profile": "Adriatic colour",
    }


def test_darktable_export_preserves_custom_context(
    tmp_path,
    monkeypatch,
):
    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.EXPORT,
        )

    monkeypatch.setattr(
        "mps.services.darktable_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_darktable_export(
        settings=_settings(tmp_path),
        source_path=tmp_path / "DSC0001_master.tif",
        output_path=tmp_path / "DSC0001_print.jpg",
        application_version="5.6.0",
        description="Lab print export",
        metadata={
            "purpose": "print",
        },
    )

    assert result.recorded is True
    assert called[0]["description"] == "Lab print export"
    assert called[0]["metadata"] == {
        "purpose": "print",
    }


def test_darktable_recording_failure_is_preserved(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "DSC0001.ARW"
    output = tmp_path / "DSC0001_master.tif"

    monkeypatch.setattr(
        "mps.services.darktable_workflow_adapter."
        "record_photo_workflow_action",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=False,
            errors=[
                "Source file is not the current provenance chain tip"
            ],
        ),
    )

    result = record_darktable_edit(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
    )

    assert result.recorded is False
    assert result.errors == [
        "Source file is not the current provenance chain tip"
    ]
