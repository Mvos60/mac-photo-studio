from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from mps.models.import_decision import ImportDecision
from mps.models.import_progress import ImportProgress
from mps.models.import_result import ImportResult
from mps.services.manifest_writer import (
    add_file_entry,
    load_or_create_manifest,
    write_manifest_to_path,
)
from mps.services.provenance_certificate import create_certificate
from mps.services.provenance_index_builder import index_entry_from_certificate
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import (
    load_or_create_index,
    write_index,
)
from mps.services.provenance_writer import write_certificate_for_import
from mps.services.safe_copy import CopyResult, copy_one_file
from mps.version import get_version


def _write_log_header(
    log_file: Path,
    decision: ImportDecision,
) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")

    if log_file.exists():
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(
                "\nImport Batch\n"
                "============\n\n"
                f"Started: {timestamp}\n"
                f"Destination: {decision.destination}\n"
                f"Planned files: {decision.total_files}\n"
                f"Estimated size bytes: "
                f"{decision.estimated_size_bytes}\n\n"
                "Operations\n"
                "----------\n"
            )
        return

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


def _append_log_operation(
    log_file: Path,
    source: Path,
    destination: Path,
    success: bool,
    message: str,
) -> None:
    status = "OK" if success else "FAILED"

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(
            f"{status}: {source} -> {destination}\n"
        )

        if message:
            handle.write(f"  {message}\n")


def _append_log_summary(
    log_file: Path,
    copied: int,
    failed: int,
    skipped: int,
) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\nSummary\n")
        handle.write("-------\n")
        handle.write(f"Finished: {timestamp}\n")
        handle.write(f"Copied: {copied}\n")
        handle.write(f"Failed: {failed}\n")
        handle.write(f"Skipped: {skipped}\n")
        handle.write(f"Success: {failed == 0}\n")


def _new_session_id() -> str:
    return f"MPS-SESSION-{uuid4()}"


def _write_manifest_for_copies(
    *,
    session_id: str,
    manifest_path: Path,
    project: str,
    day_session: str,
    copy_results: list[CopyResult],
) -> None:
    manifest = load_or_create_manifest(
        manifest_path,
        project=project,
        day_session=day_session,
        mps_version=get_version(),
        session_id=session_id,
    )

    for result in copy_results:
        if not result.success or result.checksum is None:
            continue

        add_file_entry(
            manifest,
            source_path=result.source,
            destination_path=result.destination,
            action="copied",
            status="verified",
        )

    write_manifest_to_path(
        manifest,
        manifest_path,
    )


def _write_provenance_for_copies(
    *,
    import_root: Path,
    session_id: str,
    manifest_path: Path,
    camera_model: str,
    copy_results: list[CopyResult],
) -> None:
    certificate_index_path = index_path(import_root)
    certificate_index = load_or_create_index(
        certificate_index_path
    )

    for result in copy_results:
        if not result.success or result.checksum is None:
            continue

        certificate = create_certificate(
            session_id=session_id,
            source_path=str(result.source),
            destination_path=str(result.destination),
            sha256=result.checksum,
            camera_model=camera_model,
            manifest_path=str(manifest_path),
        )

        certificate_path = write_certificate_for_import(
            certificate,
            import_root,
        )

        certificate_index.entries.append(
            index_entry_from_certificate(
                certificate,
                certificate_path,
            )
        )

    write_index(
        certificate_index,
        certificate_index_path,
    )


def run_import(
    decision: ImportDecision,
    dry_run: bool = True,
    progress_callback: Callable[[ImportProgress], None] | None = None,
    log_path: Path | None = None,
    write_provenance: bool = False,
    camera_model: str = "Unknown camera",
    manifest_path: Path | None = None,
    project: str = "",
    day_session: str = "",
    session_id: str | None = None,
) -> ImportResult:
    """Run an import decision.

    Dry runs remain fully read-only.

    A supplied session ID allows multiple media batches to contribute to one
    persistent import manifest and provenance index.
    """

    if dry_run:
        return ImportResult(
            copied=0,
            failed=0,
            skipped=len(decision.copy_operations),
            dry_run=True,
            log_path=None,
        )

    decision.destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    if log_path is not None:
        _write_log_header(
            log_path,
            decision,
        )

    copied = 0
    failed = 0
    total = len(decision.copy_operations)
    copy_results: list[CopyResult] = []

    for index, operation in enumerate(
        decision.copy_operations,
        start=1,
    ):
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
        copy_results.append(result)

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

    if write_provenance:
        resolved_manifest_path = (
            manifest_path
            or decision.destination / "import_manifest.json"
        )
        resolved_session_id = (
            session_id
            or _new_session_id()
        )

        _write_manifest_for_copies(
            session_id=resolved_session_id,
            manifest_path=resolved_manifest_path,
            project=project,
            day_session=day_session,
            copy_results=copy_results,
        )

        _write_provenance_for_copies(
            import_root=decision.destination,
            session_id=resolved_session_id,
            manifest_path=resolved_manifest_path,
            camera_model=camera_model,
            copy_results=copy_results,
        )

    if log_path is not None:
        _append_log_summary(
            log_path,
            copied,
            failed,
            skipped,
        )

    return ImportResult(
        copied=copied,
        failed=failed,
        skipped=skipped,
        dry_run=False,
        log_path=log_path,
    )
