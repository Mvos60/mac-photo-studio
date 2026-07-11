from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.import_media_wizard_runner import (
    run_import_media_session,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )


def _write_photo(
    root: Path,
    name: str,
    content: bytes,
) -> None:
    dcim = root / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True, exist_ok=True)
    (dcim / name).write_bytes(content)


def _card(
    root: Path,
    *,
    raw: int = 0,
    jpeg: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=root,
        dcim_path=root / "DCIM",
        raw_count=raw,
        jpeg_count=jpeg,
        heif_count=0,
        video_count=0,
        pair_count=min(raw, jpeg),
        orphan_raw_count=max(raw - jpeg, 0),
        orphan_jpeg_count=max(jpeg - raw, 0),
        other_count=0,
        total_size_bytes=0,
    )


def test_single_raw_card_can_finish_session(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    selections = iter(
        [
            ImportMediaSelection(
                sources=[
                    _card(root, raw=1),
                ]
            ),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: next(selections),
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-TEST",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.reconciliation is not None
    assert result.reconciliation.reconciled is True
    assert result.batches_processed == 1
    assert result.copied == 1
    assert len(result.session.sources) == 1
    assert "Eject or unmount the media before physical removal." in output


def test_raw_then_jpeg_same_reader_are_processed_sequentially(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    root = tmp_path / "reader"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    raw_selection = ImportMediaSelection(
        sources=[
            _card(root, raw=1),
        ]
    )

    jpeg_selection = ImportMediaSelection(
        sources=[
            _card(root, jpeg=1),
        ]
    )

    discovery_count = 0

    def discover(settings):
        nonlocal discovery_count
        discovery_count += 1

        if discovery_count == 1:
            return raw_selection

        raw_file = (
            root
            / "DCIM"
            / "100MSDCF"
            / "DSC0001.ARW"
        )

        if raw_file.exists():
            raw_file.unlink()

        jpeg_file = (
            root
            / "DCIM"
            / "100MSDCF"
            / "DSC0001.JPG"
        )

        if not jpeg_file.exists():
            jpeg_file.write_bytes(b"jpeg-data")

        return jpeg_selection

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        discover,
    )

    answers = iter(["y", ""])

    monkeypatch.setattr(
        "builtins.input",
        lambda _: next(answers),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-SEQUENTIAL",
    )

    output = capsys.readouterr().out

    assert result.success
    assert result.reconciliation is not None
    assert result.reconciliation.reconciled is True
    assert result.batches_processed == 2
    assert result.copied == 2
    assert len(result.session.sources) == 2

    assert {
        path.name
        for path in result.session.processed_source_files
    } == {
        "DSC0001.ARW",
        "DSC0001.JPG",
    }

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    assert (destination / "DSC0001.ARW").exists()
    assert (destination / "DSC0001.JPG").exists()

    assert output.count(
        "Eject or unmount the media before physical removal."
    ) == 2
    assert "Final Import Session Reconciliation" in output
    assert "FINAL STATUS       : IMPORT SESSION RECONCILED" in output


def test_two_simultaneous_cards_are_one_batch(
    monkeypatch,
    tmp_path: Path,
):
    raw_root = tmp_path / "raw"
    jpeg_root = tmp_path / "jpeg"

    _write_photo(raw_root, "DSC0001.ARW", b"raw-data")
    _write_photo(jpeg_root, "DSC0001.JPG", b"jpeg-data")

    selection = ImportMediaSelection(
        sources=[
            _card(raw_root, raw=1),
            _card(jpeg_root, jpeg=1),
        ]
    )

    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: selection,
    )

    monkeypatch.setattr(
        "builtins.input",
        lambda _: "",
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-TWO-READERS",
    )

    assert result.success
    assert result.reconciliation is not None
    assert result.reconciliation.reconciled is True
    assert result.batches_processed == 1
    assert result.copied == 2
    assert len(result.session.sources) == 2


def test_no_media_does_not_complete_session(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    monkeypatch.setattr(
        "mps.services.import_media_wizard_runner."
        "discover_import_media",
        lambda settings: ImportMediaSelection(
            sources=[]
        ),
    )

    result = run_import_media_session(
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-EMPTY",
    )

    output = capsys.readouterr().out

    assert result.success is False
    assert result.completed is False
    assert result.batches_processed == 0
    assert "No new photo media available." in output
