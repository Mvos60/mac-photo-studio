from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.models.import_file_result import (
    ImportFileMediaType,
    ImportFileResultStatus,
)
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


def test_batch_reports_verified_file_once(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw-data")
    results = []

    result = process_import_media_batch(
        ImportMediaSelection(sources=[_card(root, raw=1)]),
        ImportMediaSession(),
        _settings(tmp_path),
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id="MPS-SESSION-RESULT",
        file_result_callback=results.append,
    )

    assert result.success
    assert len(results) == 1
    assert results[0].status is ImportFileResultStatus.VERIFIED
    assert results[0].media_type is ImportFileMediaType.RAW
    assert results[0].destination is not None


def test_batch_reports_failed_copy_without_verified_result(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw-data")
    destination = (
        tmp_path / "Photos_Master" / "2026" / "Adriatic" / "03_Slovenia"
    )
    destination.mkdir(parents=True)
    (destination / "DSC0001.ARW").write_bytes(b"existing")
    results = []

    batch = process_import_media_batch(
        ImportMediaSelection(sources=[_card(root, raw=1)]),
        ImportMediaSession(), _settings(tmp_path),
        year=2026, project="Adriatic", day="03_Slovenia",
        session_id="MPS-SESSION-FAILED",
        file_result_callback=results.append,
    )

    assert not batch.success
    assert len(results) == 1
    assert results[0].status is ImportFileResultStatus.FAILED
    assert results[0].reason_code == "copy_failed"
    assert "refusing to overwrite" in results[0].detail


def test_duplicate_batch_reports_skip_without_copy(tmp_path: Path):
    root = tmp_path / "card"
    settings = _settings(tmp_path)
    selection = ImportMediaSelection(sources=[_card(root, jpeg=1)])
    _write_photo(root, "DSC0001.JPG", b"jpeg-photo")
    first = process_import_media_batch(
        selection, ImportMediaSession(), settings,
        year=2026, project="First", day="Session",
        session_id="MPS-FIRST",
    )
    results = []
    second = process_import_media_batch(
        selection, ImportMediaSession(), settings,
        year=2026, project="Second", day="Session",
        session_id="MPS-SECOND", file_result_callback=results.append,
    )

    assert first.success
    assert second.nothing_to_import
    assert len(results) == 1
    assert results[0].status is ImportFileResultStatus.SKIPPED
    assert results[0].reason_code == "already_imported"


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


def test_reused_cards_import_only_new_files_into_new_library(
    tmp_path: Path,
):
    settings = _settings(tmp_path)

    raw_card = tmp_path / "raw-card"
    jpeg_card = tmp_path / "jpeg-card"

    _write_photo(
        raw_card,
        "DSC0001.ARW",
        b"raw-photo-1",
    )
    _write_photo(
        raw_card,
        "DSC0002.ARW",
        b"raw-photo-2",
    )
    _write_photo(
        raw_card,
        "DSC0003.ARW",
        b"raw-photo-3",
    )

    _write_photo(
        jpeg_card,
        "DSC0001.JPG",
        b"jpeg-photo-1",
    )
    _write_photo(
        jpeg_card,
        "DSC0002.JPG",
        b"jpeg-photo-2",
    )
    _write_photo(
        jpeg_card,
        "DSC0003.JPG",
        b"jpeg-photo-3",
    )

    first_session = ImportMediaSession()

    first = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(raw_card, raw=3),
                _card(jpeg_card, jpeg=3),
            ]
        ),
        first_session,
        settings,
        year=2026,
        project="FirstLibrary",
        day="FirstSession",
        session_id="MPS-SESSION-FIRST",
    )

    assert first.success
    assert first.copied == 6

    _write_photo(
        raw_card,
        "DSC0004.ARW",
        b"raw-photo-4",
    )
    _write_photo(
        jpeg_card,
        "DSC0004.JPG",
        b"jpeg-photo-4",
    )

    second_session = ImportMediaSession()

    second = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(raw_card, raw=4),
                _card(jpeg_card, jpeg=4),
            ]
        ),
        second_session,
        settings,
        year=2026,
        project="SecondLibrary",
        day="SecondSession",
        session_id="MPS-SESSION-SECOND",
    )

    assert second.success
    assert second.copied == 2
    assert second.failed == 0
    assert second.media_registered is True

    second_destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "SecondLibrary"
        / "SecondSession"
    )

    assert {
        path.name
        for path in second_destination.iterdir()
        if path.suffix in {".ARW", ".JPG"}
    } == {
        "DSC0004.ARW",
        "DSC0004.JPG",
    }

    assert not (
        second_destination / "DSC0001.ARW"
    ).exists()
    assert not (
        second_destination / "DSC0001.JPG"
    ).exists()
    assert not (
        second_destination / "DSC0002.ARW"
    ).exists()
    assert not (
        second_destination / "DSC0002.JPG"
    ).exists()
    assert not (
        second_destination / "DSC0003.ARW"
    ).exists()
    assert not (
        second_destination / "DSC0003.JPG"
    ).exists()

def test_duplicate_only_batch_is_successful_noop(
    tmp_path: Path,
):
    root = tmp_path / "card"
    settings = _settings(tmp_path)
    selection = ImportMediaSelection(
        sources=[
            _card(root, jpeg=1),
        ]
    )

    _write_photo(
        root,
        "DSC0001.JPG",
        b"jpeg-photo",
    )

    first = process_import_media_batch(
        selection,
        ImportMediaSession(),
        settings,
        year=2026,
        project="First",
        day="Session",
        session_id="MPS-SESSION-FIRST",
    )

    second = process_import_media_batch(
        selection,
        ImportMediaSession(),
        settings,
        year=2026,
        project="Second",
        day="Session",
        session_id="MPS-SESSION-SECOND",
    )

    assert first.success
    assert second.success
    assert second.nothing_to_import is True
    assert second.copied == 0
    assert second.failed == 0
    assert second.media_registered is False
    assert second.verification is None
    assert second.plan.destination.exists() is False

def test_destination_selection_controls_manifest_metadata(
    tmp_path: Path,
):
    import json

    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw-data")
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )

    result = process_import_media_batch(
        ImportMediaSelection(
            sources=[_card(root, raw=1)]
        ),
        ImportMediaSession(),
        _settings(tmp_path),
        year=1999,
        project="Legacy Project",
        day="Legacy Day",
        session_id="MPS-SESSION-CALENDAR",
        destination_selection=destination_selection,
    )

    destination = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "08"
        / "01_Ljubljana"
        / "Adriatic"
    )
    manifest = json.loads(
        (destination / "import_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert result.success
    assert result.plan.destination == destination
    assert manifest["project"] == "Adriatic"
    assert manifest["day_session"] == "08-01_Ljubljana"
