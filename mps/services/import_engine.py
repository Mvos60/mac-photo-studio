from __future__ import annotations

from mps.models.import_decision import ImportDecision
from mps.models.import_result import ImportResult
from mps.services.safe_copy import copy_one_file


def run_import(decision: ImportDecision, dry_run: bool = True) -> ImportResult:
    """Run an import.

    Current capabilities:

    - dry run
    - create destination folder
    - copy all files using the Safe Copy engine
    """

    if dry_run:
        return ImportResult(
            copied=0,
            failed=0,
            skipped=len(decision.copy_operations),
            dry_run=True,
        )

    decision.destination.mkdir(parents=True, exist_ok=True)

    copied = 0
    failed = 0

    for operation in decision.copy_operations:
        result = copy_one_file(
            operation.source,
            operation.destination,
        )

        if result.success:
            copied += 1
        else:
            failed += 1

    return ImportResult(
        copied=copied,
        failed=failed,
        skipped=0,
        dry_run=False,
    )
