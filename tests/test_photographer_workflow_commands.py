from pathlib import Path

import pytest

from mps.config import Settings
from mps.services.digikam_workflow_adapter import (
    DigiKamWorkflowResult,
)
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)
from mps.services.photographer_workflow_commands import (
    record_darktable_workflow_command,
    record_digikam_workflow_command,
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


def test_digikam_derivative_command_uses_adapter(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.services.photographer_workflow_commands."
        "record_digikam_derivative",
        lambda **kwargs: called.append(kwargs)
        or DigiKamWorkflowResult(
            action="derivative",
            provenance_relevant=True,
            recorded=True,
        ),
    )

    result = record_digikam_workflow_command(
        settings=_settings(tmp_path),
        action="derivative",
        source_path="source.jpg",
        output_path="copy.jpg",
    )

    assert result.recorded is True
    assert called[0]["source_path"] == "source.jpg"
    assert called[0]["output_path"] == "copy.jpg"


def test_digikam_export_command_uses_adapter(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.services.photographer_workflow_commands."
        "record_digikam_export",
        lambda **kwargs: called.append(kwargs)
        or DigiKamWorkflowResult(
            action="export",
            provenance_relevant=True,
            recorded=True,
        ),
    )

    result = record_digikam_workflow_command(
        settings=_settings(tmp_path),
        action="export",
        source_path="source.jpg",
        output_path="export.jpg",
    )

    assert result.recorded is True
    assert called[0]["source_path"] == "source.jpg"
    assert called[0]["output_path"] == "export.jpg"


def test_digikam_command_rejects_unknown_action(
    tmp_path,
):
    with pytest.raises(
        ValueError,
        match="Unsupported digiKam workflow command: edit",
    ):
        record_digikam_workflow_command(
            settings=_settings(tmp_path),
            action="edit",
            source_path="source.jpg",
            output_path="output.jpg",
        )


def test_darktable_edit_command_uses_adapter(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.services.photographer_workflow_commands."
        "record_darktable_edit",
        lambda **kwargs: called.append(kwargs)
        or PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=True,
        ),
    )

    result = record_darktable_workflow_command(
        settings=_settings(tmp_path),
        action="edit",
        source_path="source.arw",
        output_path="master.tif",
    )

    assert result.recorded is True
    assert called[0]["source_path"] == "source.arw"
    assert called[0]["output_path"] == "master.tif"


def test_darktable_export_command_uses_adapter(
    tmp_path,
    monkeypatch,
):
    called = []

    monkeypatch.setattr(
        "mps.services.photographer_workflow_commands."
        "record_darktable_export",
        lambda **kwargs: called.append(kwargs)
        or PhotoProvenanceRecording(
            source_path=Path(kwargs["source_path"]),
            output_path=Path(kwargs["output_path"]),
            recorded=True,
        ),
    )

    result = record_darktable_workflow_command(
        settings=_settings(tmp_path),
        action="export",
        source_path="master.tif",
        output_path="web.jpg",
    )

    assert result.recorded is True
    assert called[0]["source_path"] == "master.tif"
    assert called[0]["output_path"] == "web.jpg"


def test_darktable_command_rejects_unknown_action(
    tmp_path,
):
    with pytest.raises(
        ValueError,
        match="Unsupported darktable workflow command: derivative",
    ):
        record_darktable_workflow_command(
            settings=_settings(tmp_path),
            action="derivative",
            source_path="source.arw",
            output_path="output.tif",
        )
