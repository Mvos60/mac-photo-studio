from pathlib import Path

from mps.models.import_decision import CopyOperation, ImportDecision
from mps.services.import_engine import run_import


def _decision(tmp_path: Path) -> ImportDecision:
    source1 = tmp_path / "source1.ARW"
    source2 = tmp_path / "source1.JPG"

    source1.write_bytes(b"raw-photo-data")
    source2.write_bytes(b"jpeg-photo-data")

    destination = tmp_path / "Photos"

    return ImportDecision(
        destination=destination,
        total_files=2,
        estimated_size_bytes=source1.stat().st_size + source2.stat().st_size,
        copy_operations=[
            CopyOperation(
                source=source1,
                destination=destination / source1.name,
            ),
            CopyOperation(
                source=source2,
                destination=destination / source2.name,
            ),
        ],
        warnings=[],
    )


def test_import_engine_dry_run(tmp_path):
    decision = _decision(tmp_path)

    result = run_import(decision, dry_run=True)

    assert result.dry_run
    assert result.copied == 0
    assert result.failed == 0
    assert result.skipped == 2
    assert not decision.destination.exists()


def test_import_engine_copies_all_files(tmp_path):
    decision = _decision(tmp_path)

    result = run_import(decision, dry_run=False)

    copied_raw = decision.destination / "source1.ARW"
    copied_jpg = decision.destination / "source1.JPG"

    assert copied_raw.exists()
    assert copied_jpg.exists()

    assert copied_raw.read_bytes() == b"raw-photo-data"
    assert copied_jpg.read_bytes() == b"jpeg-photo-data"

    assert result.copied == 2
    assert result.failed == 0
    assert result.skipped == 0
    assert result.success
