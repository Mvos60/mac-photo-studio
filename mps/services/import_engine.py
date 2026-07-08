from __future__ import annotations

from pathlib import Path

from mps.models.import_decision import ImportDecision
from mps.models.import_result import ImportResult


def run_import(decision: ImportDecision, dry_run: bool = True) -> ImportResult:
    """Run an import.

    Current capabilities:
      - dry-run preview
      - create destination folder
      - no file copies yet
    """

    if dry_run:
        return ImportResult(
            copied=0,
            failed=0,
            skipped=len(decision.copy_operations),
            dry_run=True,
        )

    destination: Path = decision.destination
    destination.mkdir(parents=True, exist_ok=True)

    return ImportResult(
        copied=0,
        failed=0,
        skipped=len(decision.copy_operations),
        dry_run=False,
    )
