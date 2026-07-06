from pathlib import Path

from mps.config import Settings
from mps.services.import_planner import create_import_plan


def _settings(tmp_path: Path) -> Settings:
    return Settings(
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


def test_create_import_plan_does_not_create_destination(tmp_path: Path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg")

    plan = create_import_plan(
        project="Adriatic_2026",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpg,
        settings=_settings(tmp_path),
    )

    assert plan.destination == tmp_path / "Photos_Master" / "Adriatic_2026" / "03_Slovenia"
    assert plan.pairing.pair_count == 1
    assert plan.total_source_files == 2
    assert plan.estimated_size_bytes == 6
    assert not plan.destination.exists()


def test_create_import_plan_reports_unmatched_files(tmp_path: Path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"
    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw")
    (raw / "DSC0002.ARW").write_bytes(b"raw")
    (jpg / "DSC0001.JPG").write_bytes(b"jpg")

    plan = create_import_plan(
        project="Adriatic_2026",
        day="04_Croatia",
        raw_folder=raw,
        jpeg_folder=jpg,
        settings=_settings(tmp_path),
    )

    assert plan.pairing.pair_count == 1
    assert len(plan.pairing.raw_only) == 1
    assert len(plan.pairing.jpeg_only) == 0
    assert plan.total_source_files == 3
