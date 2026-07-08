from __future__ import annotations

from collections.abc import Callable

from mps.models.import_decision import ImportDecision
from mps.models.import_progress import ImportProgress
from mps.models.import_result import ImportResult
from mps.services.safe_copy import copy_one_file


def run_import(
    decision: ImportDecision,
    dry_run: bool = True,
    progress_callback: Callable[[ImportProgress], None] | None = None,
) -> ImportResult:
    """Run an import."""

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

    total = len(decision.copy_operations)

    for index, operation in enumerate(decision.copy_operations, start=1):

        if progress_callback is not None:
            progress_callback(
                ImportProgress(
                    current=index,
                    total=total,
                    source=operation.source,
                    destination=operation.destination,
                )
            )

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
