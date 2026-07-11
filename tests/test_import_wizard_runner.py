from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_wizard_runner import run_interactive_import


def card():
    return CardScanResult(
        root=Path("/media/card"),
        dcim_path=Path("/media/card/DCIM"),
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


def prepare(monkeypatch):
    monkeypatch.setattr(
        "mps.services.import_wizard_runner.discover_import_cards",
        lambda settings: ImportCardSelection(
            raw_card=card(),
            jpeg_card=card(),
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


def test_run_interactive_import_accept(monkeypatch, capsys):
    prepare(monkeypatch)

    monkeypatch.setattr("builtins.input", lambda _: "")

    session = run_interactive_import(Settings({}))
    output = capsys.readouterr().out

    assert session is not None
    assert session.project == "Adriatic"
    assert "Import Summary" in output


def test_run_interactive_import_cancel(monkeypatch, capsys):
    prepare(monkeypatch)

    monkeypatch.setattr("builtins.input", lambda _: "n")

    session = run_interactive_import(Settings({}))
    output = capsys.readouterr().out

    assert session is None
    assert "Import cancelled." in output
