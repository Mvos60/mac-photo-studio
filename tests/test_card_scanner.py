from pathlib import Path

from mps.config import Settings
from mps.services.card_scanner import (
    format_bytes,
    scan_path,
)


def _settings() -> Settings:
    return Settings(
        {
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
                "heif_extensions": [
                    "HEIF",
                    "HIF",
                    "HEIC",
                ],
                "video_extensions": [
                    "MP4",
                    "MOV",
                ],
            }
        }
    )


def test_format_bytes_gb():
    assert format_bytes(
        2 * 1024**3
    ) == "2.00 GB"


def test_scan_path_counts_raw_and_jpeg(
    tmp_path: Path,
):
    dcim = (
        tmp_path
        / "DCIM"
        / "100MSDCF"
    )
    dcim.mkdir(parents=True)

    (
        dcim / "DSC0001.ARW"
    ).write_bytes(b"raw")
    (
        dcim / "DSC0001.JPG"
    ).write_bytes(b"jpg")
    (
        dcim / "DSC0002.HEIF"
    ).write_bytes(b"heif")
    (
        dcim / "DSC0003.ARW"
    ).write_bytes(b"raw orphan")
    (
        dcim / "DSC0004.JPG"
    ).write_bytes(b"jpg orphan")
    (
        dcim / "C0003.MP4"
    ).write_bytes(b"video")
    (
        dcim / "README.TXT"
    ).write_text(
        "note",
        encoding="utf-8",
    )

    result = scan_path(
        tmp_path,
        _settings(),
    )

    assert result.dcim_path == (
        tmp_path / "DCIM"
    )
    assert result.raw_count == 2
    assert result.jpeg_count == 2
    assert result.heif_count == 1
    assert result.video_count == 1
    assert result.pair_count == 1
    assert result.orphan_raw_count == 1
    assert result.orphan_jpeg_count == 1
    assert result.other_count == 1
    assert result.has_photos


def test_scan_path_without_dcim_still_counts_files(
    tmp_path: Path,
):
    (
        tmp_path / "DSC0002.ARW"
    ).write_bytes(b"raw")

    assert scan_path(
        tmp_path,
        _settings(),
    ).raw_count == 1


def test_scan_path_ignores_trash_photo_files(
    tmp_path: Path,
):
    normal = (
        tmp_path
        / "DCIM"
        / "100MSDCF"
    )
    trash = (
        tmp_path
        / "DCIM"
        / ".Trash-1000"
        / "files"
    )

    normal.mkdir(parents=True)
    trash.mkdir(parents=True)

    (
        normal / "DSC0001.ARW"
    ).write_bytes(b"real raw")
    (
        normal / "DSC0001.JPG"
    ).write_bytes(b"real jpg")

    (
        trash / "DSC0002.ARW"
    ).write_bytes(b"trash raw")
    (
        trash / "DSC0002.JPG"
    ).write_bytes(b"trash jpg")

    result = scan_path(
        tmp_path,
        _settings(),
    )

    assert result.raw_count == 1
    assert result.jpeg_count == 1
    assert result.pair_count == 1
    assert result.orphan_raw_count == 0
    assert result.orphan_jpeg_count == 0


def test_scan_path_ignores_trash_file_sizes(
    tmp_path: Path,
):
    normal = (
        tmp_path
        / "DCIM"
        / "100MSDCF"
    )
    trash = (
        tmp_path
        / "DCIM"
        / ".Trash-1000"
        / "files"
    )

    normal.mkdir(parents=True)
    trash.mkdir(parents=True)

    (
        normal / "DSC0001.ARW"
    ).write_bytes(b"12345")

    (
        trash / "DSC0002.ARW"
    ).write_bytes(b"1234567890")

    result = scan_path(
        tmp_path,
        _settings(),
    )

    assert result.total_size_bytes == 5
