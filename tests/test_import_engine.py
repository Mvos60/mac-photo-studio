from pathlib import Path

from mps.models.import_decision import CopyOperation, ImportDecision
from mps.services.import_engine import run_import


def _decision(tmp_path: Path) -> ImportDecision:
    destination = tmp_path / "Photos"

    return ImportDecision(
        destination=destination,
        total_files=1,
        estimated_size_bytes=3,
        copy_operations=[
            CopyOperation(
                source=tmp_path / "source.ARW",
                destination=destination / "source.ARW",
            )
        ],
        warnings=[],
    )


def test_import_engine_dry_run_copies_nothing(tmp_path):
    decision = _decision(tmp_path)

    result = run_import(decision, dry_run=True)

    assert result.dry_run
    assert result.copied == 0
    assert result.failed == 0
    assert result.skipped == 1
    assert not decision.destination.exists()


def test_import_engine_creates_destination(tmp_path):
    decision = _decision(tmp_path)

    assert not decision.destination.exists()

    result = run_import(decision, dry_run=False)

    assert decision.destination.exists()
    assert decision.destination.is_dir()

    assert result.success
    assert not result.dry_run
