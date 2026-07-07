from pathlib import Path

from mps.config import Settings
from mps.services.card_scanner import format_bytes, scan_path


def test_format_bytes_gb():
    assert format_bytes(2 * 1024**3) == "2.00 GB"


def test_scan_path_counts_raw_and_jpeg(tmp_path: Path):
    dcim = tmp_path / "DCIM" / "100MSDCF"
    dcim.mkdir(parents=True)

    (dcim / "DSC0001.ARW").write_bytes(b"raw")
    (dcim / "DSC0001.JPG").write_bytes(b"jpg")
    (dcim / "DSC0002.HEIF").write_bytes(b"heif")
    (dcim / "C0003.MP4").write_bytes(b"video")
    (dcim / "README.TXT").write_text("note", encoding="utf-8")

    settings = Settings(
        {
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
                "heif_extensions": ["HEIF", "HIF", "HEIC"],
                    "video_extensions": ["MP4", "MOV"],
                    "video_extensions": ["MP4", "MOV"],
            }
        }
    )

    result = scan_path(tmp_path, settings)

    assert result.dcim_path == tmp_path / "DCIM"
    assert result.raw_count == 1
    assert result.jpeg_count == 1
    assert result.heif_count == 1
    assert result.video_count == 1
    assert result.pair_count == 1
    assert result.other_count == 1
    assert result.has_photos


def test_scan_path_without_dcim_still_counts_files(tmp_path: Path):
    (tmp_path / "DSC0002.ARW").write_bytes(b"raw")

    settings = Settings(
        {
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
                "heif_extensions": ["HEIF", "HIF", "HEIC"],
                    "video_extensions": ["MP4", "MOV"],
                    "video_extensions": ["MP4", "MOV"],
            }
        }
    )

    assert scan_path(tmp_path, settings).raw_count == 1
