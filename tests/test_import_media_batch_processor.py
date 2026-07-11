from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_batch_processor import (
    process_import_media_batch,
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
    directory = root / "DCIM" / "100MSDCF"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(content)


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


def test_successful_raw_batch_is_registered(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw-data")

    session = ImportMediaSession()

    result = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
        session,
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-1",
    )

    assert result.success
    assert result.copied == 1
    assert result.failed == 0
    assert result.media_registered is True
    assert len(session.sources) == 1

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    assert (destination / "DSC0001.ARW").exists()
    assert (destination / "import_manifest.json").exists()


def test_sequential_cards_share_one_import_session(tmp_path: Path):
    root = tmp_path / "reader"
    session = ImportMediaSession()
    settings = _settings(tmp_path)

    _write_photo(root, "DSC0001.ARW", b"raw-data")

    first = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(root, raw=1),
            ]
        ),
        session,
        settings,
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-SEQUENTIAL",
    )

    raw_file = (
        root
        / "DCIM"
        / "100MSDCF"
        / "DSC0001.ARW"
    )
    raw_file.unlink()

    _write_photo(root, "DSC0001.JPG", b"jpeg-data")

    second = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(root, jpeg=1),
            ]
        ),
        session,
        settings,
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-SEQUENTIAL",
    )

    assert first.success
    assert second.success
    assert len(session.sources) == 2
    assert len(session.source_fingerprints) == 2
    assert {
        source.name
        for source in session.processed_source_files
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

    import json

    manifest = json.loads(
        (destination / "import_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["session_id"] == "MPS-SESSION-SEQUENTIAL"
    assert manifest["file_count"] == 2


def test_collision_warning_prevents_batch_processing(
    tmp_path: Path,
):
    first_root = tmp_path / "card1"
    second_root = tmp_path / "card2"

    _write_photo(first_root, "DSC0001.ARW", b"first")
    _write_photo(second_root, "DSC0001.ARW", b"second")

    session = ImportMediaSession()

    result = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(first_root, raw=1),
                _card(second_root, raw=1),
            ]
        ),
        session,
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-1",
    )

    assert result.success is False
    assert result.copied == 0
    assert result.verification is None
    assert result.media_registered is False
    assert session.sources == []


def test_empty_batch_is_not_registered(tmp_path: Path):
    session = ImportMediaSession()

    result = process_import_media_batch(
        ImportMediaSelection(sources=[]),
        session,
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-1",
    )

    assert result.success is False
    assert result.copied == 0
    assert result.media_registered is False
    assert session.sources == []
