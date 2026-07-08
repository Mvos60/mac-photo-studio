from pathlib import Path

from mps.models.import_decision import CopyOperation, ImportDecision
from mps.services.import_engine import run_import


def _decision(tmp_path: Path) -> ImportDecision:
    source = tmp_path / "source.ARW"
    source.write_bytes(b"photo-data")

    destination = tmp_path / "Photos"

    return ImportDecision(
        destination=destination,
        total_files=1,
        estimated_size_bytes=source.stat().st_size,
        copy_operations=[
            CopyOperation(
                source=source,
                destination=destination / source.name,
            )
        ],
        warnings=[],
    )


def test_import_engine_dry_run(tmp_path):
    decision = _decision(tmp_path)

    result = run_import(decision, dry_run=True)

    assert result.dry_run
    assert result.copied == 0
    assert result.failed == 0
    assert result.skipped == 1
    assert not decision.destination.exists()


def test_import_engine_copies_first_file(tmp_path):
    decision = _decision(tmp_path)

    result = run_import(decision, dry_run=False)

    copied_file = decision.destination / "source.ARW"

    assert copied_file.exists()
    assert copied_file.read_bytes() == b"photo-data"

    assert result.copied == 1
    assert result.failed == 0
    assert result.skipped == 0
    assert result.success
