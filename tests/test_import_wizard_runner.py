from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_wizard_runner import run_interactive_import


def card(root: Path):
    return CardScanResult(
        root=root,
        dcim_path=root / "DCIM",
        raw_count=42,
        jpeg_count=42,
        heif_count=0,
        video_count=0,
        pair_count=42,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=0,
    )


def prepare(monkeypatch, raw: Path, jpeg: Path):
    monkeypatch.setattr(
        "mps.services.import_wizard_runner.discover_import_cards",
        lambda settings: ImportCardSelection(
            raw_card=card(raw),
            jpeg_card=card(jpeg),
            warnings=[],
        ),
    )

    monkeypatch.setattr(
        "mps.services.import_wizard_runner.prompt_year",
        lambda default: 2026,
    )

    monkeypatch.setattr(
        "mps.services.import_wizard_runner.prompt_project",
        lambda: "Adriatic",
    )

    monkeypatch.setattr(
        "mps.services.import_wizard_runner.prompt_day",
        lambda: "03_Slovenia",
    )


def test_run_interactive_import_accept(monkeypatch, capsys, tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpeg / "DSC0001.JPG").write_bytes(b"jpeg")

    prepare(monkeypatch, raw, jpeg)

    monkeypatch.setattr("builtins.input", lambda _: "")

    settings = Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )

    session = run_interactive_import(settings)
    output = capsys.readouterr().out

    assert session is not None
    assert session.project == "Adriatic"
    assert "Import Summary" in output
    assert "Import Plan Preview" in output
    assert "Pairs       : 1" in output
    assert "Total files : 2" in output


def test_run_interactive_import_cancel(monkeypatch, capsys, tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    prepare(monkeypatch, raw, jpeg)

    monkeypatch.setattr("builtins.input", lambda _: "n")

    session = run_interactive_import(Settings({}))
    output = capsys.readouterr().out

    assert session is None
    assert "Import cancelled." in output
    assert "Import Plan Preview" not in output
