from pathlib import Path

from mps.config import Settings
from mps.services.import_engine import run_import
from mps.services.import_planner import (
    create_import_decision,
    create_import_plan,
)


def test_complete_import_pipeline(tmp_path):
    raw = tmp_path / "raw"
    jpg = tmp_path / "jpg"

    raw.mkdir()
    jpg.mkdir()

    (raw / "DSC0001.ARW").write_bytes(b"raw-data")
    (jpg / "DSC0001.JPG").write_bytes(b"jpeg-data")

    settings = Settings(
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

    plan = create_import_plan(
        project="Adriatic_2026",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpg,
        settings=settings,
    )

    decision = create_import_decision(plan)

    result = run_import(decision, dry_run=False)

    destination = (
        tmp_path
        / "Photos_Master"
        / "Adriatic_2026"
        / "03_Slovenia"
    )

    assert result.success
    assert result.copied == 2

    assert (destination / "DSC0001.ARW").exists()
    assert (destination / "DSC0001.JPG").exists()

    assert (destination / "DSC0001.ARW").read_bytes() == b"raw-data"
    assert (destination / "DSC0001.JPG").read_bytes() == b"jpeg-data"
