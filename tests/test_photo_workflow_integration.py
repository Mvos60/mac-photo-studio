from pathlib import Path

import pytest

from mps.config import Settings
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)
from mps.services.photo_workflow_integration import (
    record_photo_workflow_action,
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
) -> PhotoProvenanceRecording:
    return PhotoProvenanceRecording(
        source_path=Path(source_path),
        output_path=Path(output_path),
        recorded=True,
        session_id="MPS-SESSION-TEST",
        event=ProvenanceEvent(
            event_id="MPS-EVENT-TEST",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-TEST",
            event_type=event_type,
            created_at="2026-07-13T10:00:00Z",
            input_sha256="input-hash",
            output_sha256="output-hash",
        ),
    )


@pytest.mark.parametrize(
    ("action", "expected_event_type"),
    [
        ("edit", ProvenanceEventType.EDIT),
        ("derivative", ProvenanceEventType.DERIVATIVE),
        ("export", ProvenanceEventType.EXPORT),
    ],
)
def test_workflow_action_maps_to_provenance_event_type(
    tmp_path,
    monkeypatch,
    action,
    expected_event_type,
):
    source = tmp_path / "source.ARW"
    output = tmp_path / "output.tif"

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=kwargs["event_type"],
        )

    monkeypatch.setattr(
        "mps.services.photo_workflow_integration."
        "record_managed_photo_action",
        record_action,
    )

    result = record_photo_workflow_action(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        action=action,
    )

    assert result.recorded is True
    assert result.event is not None
    assert result.event.event_type is expected_event_type
    assert called[0]["event_type"] is expected_event_type


def test_workflow_action_preserves_application_context(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "source.ARW"
    output = tmp_path / "output.tif"

    called = []

    def record_action(**kwargs):
        called.append(kwargs)

        return _recording(
            source_path=kwargs["source_path"],
            output_path=kwargs["output_path"],
            event_type=kwargs["event_type"],
        )

    monkeypatch.setattr(
        "mps.services.photo_workflow_integration."
        "record_managed_photo_action",
        record_action,
    )

    result = record_photo_workflow_action(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
        action="edit",
        application="darktable",
        application_version="5.6.0",
        description="RAW development",
        metadata={
            "workflow": "RAW-first",
        },
    )

    assert result.recorded is True

    assert called[0]["application"] == "darktable"
    assert called[0]["application_version"] == "5.6.0"
    assert called[0]["description"] == "RAW development"
    assert called[0]["metadata"] == {
        "workflow": "RAW-first",
    }


def test_workflow_action_rejects_unknown_action(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.services.photo_workflow_integration."
        "record_managed_photo_action",
        lambda **kwargs: called.append(kwargs),
    )

    with pytest.raises(
        ValueError,
        match="Unsupported photo workflow action: retouch-magic",
    ):
        record_photo_workflow_action(
            settings=_settings(tmp_path),
            source_path=tmp_path / "source.ARW",
            output_path=tmp_path / "output.tif",
            action="retouch-magic",
        )

    assert called == []
