from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from mps.models.import_decision import ImportDecision
from mps.models.import_progress import ImportProgress
from mps.models.import_result import ImportResult
from mps.services.safe_copy import copy_one_file


def _write_log_header(log_file: Path, decision: ImportDecision) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")

    log_file.write_text(
        "Mac Photo Studio Import Log\n"
        "===========================\n\n"
        f"Started: {timestamp}\n"
        f"Destination: {decision.destination}\n"
        f"Planned files: {decision.total_files}\n"
        f"Estimated size bytes: {decision.estimated_size_bytes}\n\n"
        "Operations\n"
        "----------\n",
        encoding="utf-8",
    )


def _append_log_operation(log_file: Path, source: Path, destination: Path, success: bool, message: str) -> None:
    status = "OK" if success else "FAILED"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{status}: {source} -> {destination}\n")
        if message:
            handle.write(f"  {message}\n")


def _append_log_summary(log_file: Path, copied: int, failed: int, skipped: int) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\nSummary\n")
        handle.write("-------\n")
        handle.write(f"Finished: {timestamp}\n")
        handle.write(f"Copied: {copied}\n")
        handle.write(f"Failed: {failed}\n")
        handle.write(f"Skipped: {skipped}\n")
        handle.write(f"Success: {failed == 0}\n")


def run_import(
    decision: ImportDecision,
    dry_run: bool = True,
    progress_callback: Callable[[ImportProgress], None] | None = None,
    log_path: Path | None = None,
) -> ImportResult:
    """Run an import decision.

    Dry runs remain fully read-only: no folders, files, or logs are created.
    Real imports create the destination folder, copy files through Safe Copy,
    and optionally write a human-readable import log.
    """

    if dry_run:
        return ImportResult(
            copied=0,
            failed=0,
            skipped=len(decision.copy_operations),
            dry_run=True,
            log_path=None,
        )

    decision.destination.mkdir(parents=True, exist_ok=True)

    if log_path is not None:
        _write_log_header(log_path, decision)

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

        if log_path is not None:
            _append_log_operation(
                log_path,
                operation.source,
                operation.destination,
                result.success,
                result.message,
            )

    skipped = 0

    if log_path is not None:
        _append_log_summary(log_path, copied, failed, skipped)

    return ImportResult(
        copied=copied,
        failed=failed,
        skipped=skipped,
        dry_run=False,
        log_path=log_path,
    )
