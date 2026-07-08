from __future__ import annotations

from mps.models.import_decision import ImportDecision
from mps.models.import_result import ImportResult


def run_import(decision: ImportDecision, dry_run: bool = True) -> ImportResult:
    """Run an import decision.

    First version is intentionally safe:
    - no folders are created
    - no files are copied
    - no source files are modified
    """

    if dry_run:
        return ImportResult(
            copied=0,
            failed=0,
            skipped=len(decision.copy_operations),
            dry_run=True,
        )

    return ImportResult(
        copied=0,
        failed=0,
        skipped=len(decision.copy_operations),
        dry_run=False,
    )
