from __future__ import annotations

from pathlib import Path

from mps.models.import_decision import ImportDecision
from mps.models.import_result import ImportResult
from mps.services.safe_copy import copy_one_file


def run_import(decision: ImportDecision, dry_run: bool = True) -> ImportResult:
    """Run an import.

    Current capabilities:

    - dry run
    - create destination folder
    - copy the first file using the Safe Copy engine
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

    if decision.copy_operations:
        operation = decision.copy_operations[0]

        result = copy_one_file(
            operation.source,
            operation.destination,
        )

        if result.success:
            copied = 1
        else:
            failed = 1

    skipped = max(0, len(decision.copy_operations) - copied - failed)

    return ImportResult(
        copied=copied,
        failed=failed,
        skipped=skipped,
        dry_run=False,
    )
