from pathlib import Path

from mps.models.import_decision import CopyOperation, ImportDecision
from mps.services.import_engine import run_import


def test_import_engine_dry_run_copies_nothing():
    decision = ImportDecision(
        destination=Path("/tmp/photos"),
        total_files=1,
        estimated_size_bytes=3,
        copy_operations=[
            CopyOperation(
                source=Path("/tmp/source.ARW"),
                destination=Path("/tmp/photos/source.ARW"),
            )
        ],
        warnings=[],
    )

    result = run_import(decision, dry_run=True)

    assert result.dry_run
    assert result.copied == 0
    assert result.failed == 0
    assert result.skipped == 1
    assert result.success
