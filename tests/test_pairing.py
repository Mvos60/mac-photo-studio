from pathlib import Path

from mps.config import Settings
from mps.services.pairing import pair_paths


def _settings() -> Settings:
    return Settings(
        {
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            }
        }
    )


def test_pair_paths_matches_files_by_stem(tmp_path: Path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg")

    result = pair_paths(raw, jpg, _settings())

    assert result.pair_count == 1
    assert result.pairs[0].stem == "DSC0001"
    assert not result.raw_only
    assert not result.jpeg_only


def test_pair_paths_reports_unmatched_files(tmp_path: Path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (raw / "DSC0002.ARW").write_bytes(b"raw")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg")
    (jpg / "DSC0003.JPG").write_bytes(b"jpg")

    result = pair_paths(raw, jpg, _settings())

    assert result.pair_count == 1
    assert [p.name for p in result.raw_only] == ["DSC0002.ARW"]
    assert [p.name for p in result.jpeg_only] == ["DSC0003.JPG"]


def test_pair_paths_is_case_insensitive_for_extensions(tmp_path: Path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.arw").write_bytes(b"raw")
    (jpg / "DSC0001.jpeg").write_bytes(b"jpg")

    result = pair_paths(raw, jpg, _settings())

    assert result.pair_count == 1
