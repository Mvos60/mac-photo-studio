from pathlib import Path

import pytest

from mps.config import Settings
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.digikam_workflow_adapter import (
    DIGIKAM_APPLICATION,
    handle_digikam_catalogue_action,
    record_digikam_derivative,
    record_digikam_export,
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


@pytest.mark.parametrize(
    "action",
    [
        "album",
        "face",
        "rating",
        "search",
        "tag",
    ],
)
def test_digikam_catalogue_actions_do_not_record_provenance(
    action,
):
    result = handle_digikam_catalogue_action(
        action=action,
    )

    assert result.action == action
    assert result.provenance_relevant is False
    assert result.recorded is False
    assert result.recording is None
    assert result.errors == []


def test_digikam_catalogue_action_rejects_unknown_action():
    with pytest.raises(
        ValueError,
        match=(
            "Unsupported digiKam catalogue action: "
            "pixel-edit"
        ),
    ):
        handle_digikam_catalogue_action(
            action="pixel-edit",
        )


def test_digikam_derivative_uses_workflow_boundary(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "DSC0001.JPG"
    output = tmp_path / "DSC0001_copy.JPG"

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.DERIVATIVE,
        )

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_digikam_derivative(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        application_version="9.1.0",
    )

    assert result.provenance_relevant is True
    assert result.recorded is True
    assert called[0]["action"] == "derivative"
    assert called[0]["application"] == DIGIKAM_APPLICATION
    assert called[0]["application_version"] == "9.1.0"
    assert called[0]["description"] == "digiKam derived file"


def test_digikam_export_uses_workflow_boundary(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "DSC0001.JPG"
    output = tmp_path / "DSC0001_export.JPG"

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.EXPORT,
        )

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_digikam_export(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        application_version="9.1.0",
    )

    assert result.provenance_relevant is True
    assert result.recorded is True
    assert called[0]["action"] == "export"
    assert called[0]["application"] == DIGIKAM_APPLICATION
    assert called[0]["application_version"] == "9.1.0"
    assert called[0]["description"] == "digiKam export"


def test_digikam_recording_failure_is_preserved(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "DSC0001.JPG"
    output = tmp_path / "DSC0001_export.JPG"

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
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

    result = record_digikam_export(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
    )

    assert result.provenance_relevant is True
    assert result.recorded is False
    assert result.errors == [
        "Source file is not the current provenance chain tip"
    ]


def test_digikam_derivative_detects_application_version(
    tmp_path,
    monkeypatch,
):
    from mps.services.workflow_application_context import (
        WorkflowApplicationContext,
    )

    called = []

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
        "resolve_digikam_context",
        lambda settings: WorkflowApplicationContext(
            key="digikam",
            application="digiKam",
            available=True,
            version="digiKam 9.1.0",
        ),
    )

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.DERIVATIVE,
        )

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_digikam_derivative(
        settings=_settings(tmp_path),
        source_path=tmp_path / "DSC0001.JPG",
        output_path=tmp_path / "DSC0001_copy.JPG",
    )

    assert result.recorded is True
    assert (
        called[0]["application_version"]
        == "digiKam 9.1.0"
    )


def test_digikam_explicit_version_skips_detection(
    tmp_path,
    monkeypatch,
):
    detection_called = []

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
        "resolve_digikam_context",
        lambda settings: detection_called.append(settings),
    )

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=ProvenanceEventType.EXPORT,
        )

    monkeypatch.setattr(
        "mps.services.digikam_workflow_adapter."
        "record_photo_workflow_action",
        record_action,
    )

    result = record_digikam_export(
        settings=_settings(tmp_path),
        source_path=tmp_path / "DSC0001.JPG",
        output_path=tmp_path / "DSC0001_export.JPG",
        application_version="9.1.0",
    )

    assert result.recorded is True
    assert detection_called == []
    assert called[0]["application_version"] == "9.1.0"
