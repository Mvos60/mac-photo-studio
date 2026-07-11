from pathlib import Path

from mps.models.card import CardScanResult
from mps.services.media_source_identity import (
    media_source_fingerprint,
)


def _card(root: Path) -> CardScanResult:
    return CardScanResult(
        root=root,
        dcim_path=root / "DCIM",
        raw_count=0,
        jpeg_count=0,
        heif_count=0,
        video_count=0,
        pair_count=0,
        orphan_raw_count=0,
        orphan_jpeg_count=0,
        other_count=0,
        total_size_bytes=0,
    )


def test_same_media_contents_have_same_fingerprint(tmp_path: Path):
    first = tmp_path / "mount1"
    second = tmp_path / "mount2"

    first_dcim = first / "DCIM" / "100MSDCF"
    second_dcim = second / "DCIM" / "100MSDCF"

    first_dcim.mkdir(parents=True)
    second_dcim.mkdir(parents=True)

    (first_dcim / "DSC0001.ARW").write_bytes(b"raw-data")
    (second_dcim / "DSC0001.ARW").write_bytes(b"raw-data")

    assert media_source_fingerprint(
        _card(first)
    ) == media_source_fingerprint(
        _card(second)
    )


def test_raw_and_jpeg_cards_at_same_mount_path_get_different_identity(
    tmp_path: Path,
):
    root = tmp_path / "card"
    dcim = root / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True)

    raw_file = dcim / "DSC0001.ARW"
    raw_file.write_bytes(b"raw-data")

    raw_fingerprint = media_source_fingerprint(
        _card(root)
    )

    raw_file.unlink()

    jpeg_file = dcim / "DSC0001.JPG"
    jpeg_file.write_bytes(b"jpeg-data")

    jpeg_fingerprint = media_source_fingerprint(
        _card(root)
    )

    assert raw_fingerprint != jpeg_fingerprint


def test_changed_media_inventory_changes_fingerprint(tmp_path: Path):
    root = tmp_path / "card"
    dcim = root / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True)

    (dcim / "DSC0001.ARW").write_bytes(b"raw-data")

    first = media_source_fingerprint(
        _card(root)
    )

    (dcim / "DSC0002.ARW").write_bytes(b"more-raw-data")

    second = media_source_fingerprint(
        _card(root)
    )

    assert first != second


def test_file_size_change_changes_fingerprint(tmp_path: Path):
    root = tmp_path / "card"
    dcim = root / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True)

    photo = dcim / "DSC0001.ARW"
    photo.write_bytes(b"raw")

    first = media_source_fingerprint(
        _card(root)
    )

    photo.write_bytes(b"much-larger-raw-data")

    second = media_source_fingerprint(
        _card(root)
    )

    assert first != second
