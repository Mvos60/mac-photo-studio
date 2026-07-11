from __future__ import annotations

from mps.config import Settings
from mps.models.import_media_batch_result import ImportMediaBatchResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.camera_identifier import identify_camera_model
from mps.services.import_engine import run_import
from mps.services.import_media_batch_planner import (
    create_media_batch_plan,
)
from mps.services.import_media_session import add_media_to_session
from mps.services.post_import_verifier import verify_import_root


def process_import_media_batch(
    selection: ImportMediaSelection,
    session: ImportMediaSession,
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
    session_id: str,
) -> ImportMediaBatchResult:
    """Copy and verify currently mounted media before registering it."""

    plan = create_media_batch_plan(
        selection,
        settings,
        year=year,
        project=project,
        day=day,
    )

    if plan.decision.warnings:
        return ImportMediaBatchResult(
            plan=plan,
            copied=0,
            failed=0,
            verification=None,
            media_registered=False,
        )

    if not plan.decision.copy_operations:
        return ImportMediaBatchResult(
            plan=plan,
            copied=0,
            failed=0,
            verification=None,
            media_registered=False,
        )

    first_source = plan.decision.copy_operations[0].source
    camera_model = identify_camera_model(first_source)

    result = run_import(
        plan.decision,
        dry_run=False,
        log_path=plan.destination / "mps_import.log",
        write_provenance=True,
        camera_model=camera_model,
        manifest_path=plan.destination / "import_manifest.json",
        project=project,
        day_session=day,
        session_id=session_id,
    )

    if not result.success:
        return ImportMediaBatchResult(
            plan=plan,
            copied=result.copied,
            failed=result.failed,
            verification=None,
            media_registered=False,
        )

    verification = verify_import_root(
        plan.destination,
    )

    if verification.safe_to_release:
        add_media_to_session(
            session,
            selection,
        )

        session.add_processed_source_files(
            [
                operation.source
                for operation in plan.decision.copy_operations
            ]
        )

    return ImportMediaBatchResult(
        plan=plan,
        copied=result.copied,
        failed=result.failed,
        verification=verification,
        media_registered=verification.safe_to_release,
    )
