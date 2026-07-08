from pathlib import Path

from mps.models.import_progress import ImportProgress


def test_import_progress_percent():
    progress = ImportProgress(
        current=3,
        total=10,
        source=Path("/tmp/source"),
        destination=Path("/tmp/destination"),
    )

    assert progress.percent == 30


def test_import_progress_percent_with_zero_total():
    progress = ImportProgress(
        current=0,
        total=0,
        source=Path("/tmp/source"),
        destination=Path("/tmp/destination"),
    )

    assert progress.percent == 100
