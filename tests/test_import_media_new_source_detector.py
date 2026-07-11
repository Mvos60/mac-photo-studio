from pathlib import Path

from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_new_source_detector import (
    detect_new_media_sources,
)
from mps.services.import_media_session import add_media_to_session


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


def test_new_card_is_detected(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw")

    card = _card(root, raw=1)
    session = ImportMediaSession()

    result = detect_new_media_sources(
        session,
        ImportMediaSelection(sources=[card]),
    )

    assert result.sources == [card]


def test_seen_card_is_not_detected_again(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw")

    card = _card(root, raw=1)
    selection = ImportMediaSelection(sources=[card])
    session = ImportMediaSession()

    add_media_to_session(
        session,
        selection,
    )

    result = detect_new_media_sources(
        session,
        selection,
    )

    assert result.empty is True


def test_second_card_at_same_mount_path_is_new(tmp_path: Path):
    root = tmp_path / "card"
    _write_photo(root, "DSC0001.ARW", b"raw")

    raw_card = _card(root, raw=1)
    session = ImportMediaSession()

    add_media_to_session(
        session,
        ImportMediaSelection(sources=[raw_card]),
    )

    raw_file = root / "DCIM" / "100MSDCF" / "DSC0001.ARW"
    raw_file.unlink()

    _write_photo(root, "DSC0001.JPG", b"jpeg")
    jpeg_card = _card(root, jpeg=1)

    result = detect_new_media_sources(
        session,
        ImportMediaSelection(sources=[jpeg_card]),
    )

    assert result.sources == [jpeg_card]


def test_only_unseen_media_is_returned(tmp_path: Path):
    raw_root = tmp_path / "raw"
    jpeg_root = tmp_path / "jpeg"

    _write_photo(raw_root, "DSC0001.ARW", b"raw")
    _write_photo(jpeg_root, "DSC0001.JPG", b"jpeg")

    raw_card = _card(raw_root, raw=1)
    jpeg_card = _card(jpeg_root, jpeg=1)

    session = ImportMediaSession()

    add_media_to_session(
        session,
        ImportMediaSelection(sources=[raw_card]),
    )

    result = detect_new_media_sources(
        session,
        ImportMediaSelection(
            sources=[
                raw_card,
                jpeg_card,
            ]
        ),
    )

    assert result.sources == [jpeg_card]
