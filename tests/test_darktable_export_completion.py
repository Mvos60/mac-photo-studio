from pathlib import Path

from mps.config import Settings
from mps.services.darktable_export_completion import (
    complete_darktable_export,
)
from mps.services.photo_provenance_recording import (
    PhotoProvenanceRecording,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
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


def test_complete_darktable_export_records_then_verifies(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "master.tif"
    output = tmp_path / "export.jpg"
    called = []

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "record_darktable_export",
        lambda **kwargs: called.append(
            ("record", kwargs)
        )
        or PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=True,
        ),
    )

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "verify_managed_photo",
        lambda **kwargs: called.append(
            ("verify", kwargs)
        )
        or PhotoProvenanceVerification(
            photo_path=output,
            trusted=True,
        ),
    )

    settings = _settings(tmp_path)

    result = complete_darktable_export(
        settings=settings,
        source_path=source,
        output_path=output,
    )

    assert result.completed is True
    assert [item[0] for item in called] == [
        "record",
        "verify",
    ]
    assert called[0][1]["settings"] is settings
    assert called[0][1]["source_path"] == source
    assert called[0][1]["output_path"] == output
    assert called[1][1]["settings"] is settings
    assert called[1][1]["photo_path"] == output


def test_complete_darktable_export_stops_on_recording_failure(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "master.tif"
    output = tmp_path / "export.jpg"
    verified = []

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "record_darktable_export",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=False,
            errors=[
                "Source file is not the current provenance chain tip"
            ],
        ),
    )

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "verify_managed_photo",
        lambda **kwargs: verified.append(kwargs),
    )

    result = complete_darktable_export(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
    )

    assert result.completed is False
    assert result.verification is None
    assert result.errors == (
        "Source file is not the current provenance chain tip",
    )
    assert verified == []


def test_complete_darktable_export_reports_verification_failure(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "master.tif"
    output = tmp_path / "export.jpg"

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "record_darktable_export",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=source,
            output_path=output,
            recorded=True,
        ),
    )

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "verify_managed_photo",
        lambda **kwargs: PhotoProvenanceVerification(
            photo_path=output,
            trusted=False,
            errors=[
                "Actual file SHA-256 does not match recorded identity"
            ],
        ),
    )

    result = complete_darktable_export(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
    )

    assert result.completed is False
    assert result.verification is not None
    assert result.errors == (
        "Actual file SHA-256 does not match recorded identity",
    )


def test_complete_darktable_export_expands_paths(
    tmp_path,
    monkeypatch,
):
    source = Path("~/Photos_Master/master.tif")
    output = Path("~/Photos_Master/export.jpg")

    expected_source = source.expanduser()
    expected_output = output.expanduser()

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "record_darktable_export",
        lambda **kwargs: PhotoProvenanceRecording(
            source_path=expected_source,
            output_path=expected_output,
            recorded=True,
        ),
    )

    monkeypatch.setattr(
        "mps.services.darktable_export_completion."
        "verify_managed_photo",
        lambda **kwargs: PhotoProvenanceVerification(
            photo_path=expected_output,
            trusted=True,
        ),
    )

    result = complete_darktable_export(
        settings=_settings(tmp_path),
        source_path=source,
        output_path=output,
    )

    assert result.source_path == expected_source
    assert result.output_path == expected_output
    assert result.completed is True
