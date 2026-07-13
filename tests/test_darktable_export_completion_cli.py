from pathlib import Path

from mps.main import main
from mps.services.darktable_export_completion import (
    DarktableExportCompletion,
)


def test_cli_darktable_complete_export_reports_verified(
    tmp_path,
    monkeypatch,
    capsys,
):
    source = tmp_path / "master.tif"
    output = tmp_path / "export.jpg"

    monkeypatch.setattr(
        "mps.main.complete_darktable_export",
        lambda **kwargs: DarktableExportCompletion(
            source_path=source,
            output_path=output,
            completed=True,
        ),
    )

    result = main(
        [
            "darktable-complete-export",
            str(source),
            str(output),
        ]
    )

    text = capsys.readouterr().out

    assert result == 0
    assert "Status:        VERIFIED" in text
    assert str(source) in text
    assert str(output) in text


def test_cli_darktable_complete_export_reports_failure(
    tmp_path,
    monkeypatch,
    capsys,
):
    source = tmp_path / "master.tif"
    output = tmp_path / "export.jpg"

    monkeypatch.setattr(
        "mps.main.complete_darktable_export",
        lambda **kwargs: DarktableExportCompletion(
            source_path=source,
            output_path=output,
            completed=False,
            errors=(
                "Source file is not the current provenance chain tip",
            ),
        ),
    )

    result = main(
        [
            "darktable-complete-export",
            str(source),
            str(output),
        ]
    )

    text = capsys.readouterr().out

    assert result == 1
    assert "Status:        NOT VERIFIED" in text
    assert (
        "Source file is not the current provenance chain tip"
        in text
    )


def test_cli_darktable_complete_export_requires_paths():
    try:
        main(["darktable-complete-export"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected argparse SystemExit")
