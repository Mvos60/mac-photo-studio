from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from mps.config import Settings
from mps.models.import_media_session import ImportMediaSession
from mps.models.import_progress import ImportProgress
from mps.models.import_media_wizard_result import (
    ImportMediaWizardResult,
)
from mps.services.import_media_batch_processor import (
    process_import_media_batch,
)
from mps.services.import_media_discovery import discover_import_media
from mps.services.import_media_new_source_detector import (
    detect_new_media_sources,
)
from mps.services.import_media_report import build_media_report
from mps.services.import_media_session_reconciler import (
    reconcile_import_media_session,
)
from mps.services.import_media_session_store import (
    save_import_media_session,
)


def _new_session_id() -> str:
    return f"MPS-SESSION-{uuid4()}"


def run_import_media_session(
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
    session_id: str | None = None,
    session: ImportMediaSession | None = None,
    session_state_path: str | Path | None = None,
    progress_callback: Callable[[ImportProgress], None] | None = None,
) -> ImportMediaWizardResult:
    """Process and reconcile one or more photo media batches."""

    active_session_id = (
        session.session_id
        if session is not None and session.session_id is not None
        else session_id or _new_session_id()
    )

    active_session = session or ImportMediaSession()
    active_session.session_id = active_session_id

    state_path = (
        Path(session_state_path)
        if session_state_path is not None
        else None
    )

    batches_processed = 0
    copied = 0
    failed = 0
    import_root: Path | None = None

    while True:
        selection = discover_import_media(settings)
        new_media = detect_new_media_sources(
            active_session,
            selection,
        )

        if new_media.empty and not selection.empty:
            print(
                "Mounted photo media has already been processed "
                "in this session."
            )
        else:
            print(build_media_report(new_media))

        print()

        if new_media.empty:
            if (
                batches_processed == 0
                and not active_session.processed_source_files
            ):
                print("No new photo media available.")
                return ImportMediaWizardResult(
                    session=active_session,
                    session_id=active_session_id,
                    batches_processed=0,
                    copied=0,
                    failed=0,
                    completed=False,
                )

            if not selection.empty:
                print(
                    "Eject or unmount the processed media and "
                    "insert the next source."
                )

                answer = input(
                    "Retry media search? [Y/n]: "
                ).strip().lower()

                if answer not in {"n", "no"}:
                    continue

                break

            answer = input(
                "No media mounted. Finish import session? [Y/n]: "
            ).strip().lower()

            if answer in {"n", "no"}:
                continue

            break

        result = process_import_media_batch(
            new_media,
            active_session,
            settings,
            year=year,
            project=project,
            day=day,
            session_id=active_session_id,
            progress_callback=progress_callback,
        )

        copied += result.copied
        failed += result.failed

        if result.nothing_to_import:
            print("No new photo files found.")
            print(
                "All discovered photo files were "
                "already imported."
            )

            if state_path is not None:
                state_path.unlink(
                    missing_ok=True
                )

            return ImportMediaWizardResult(
                session=active_session,
                session_id=active_session_id,
                batches_processed=batches_processed,
                copied=copied,
                failed=failed,
                completed=True,
                nothing_to_import=True,
            )

        if not result.success:
            print("Media batch processing failed.")
            return ImportMediaWizardResult(
                session=active_session,
                session_id=active_session_id,
                batches_processed=batches_processed,
                copied=copied,
                failed=failed,
                completed=False,
            )

        batches_processed += 1
        import_root = result.plan.destination

        if state_path is not None:
            save_import_media_session(
                active_session,
                state_path,
            )

        print(
            f"Media batch verified. "
            f"Copied {result.copied} file(s)."
        )
        print("MPS has finished reading the current media.")
        print(
            "Eject or unmount the media before physical removal."
        )
        print()

        answer = input(
            "Process another card or media source? [y/N]: "
        ).strip().lower()

        if answer not in {"y", "yes"}:
            break

    if import_root is None:
        from mps.services.import_media_batch_planner import (
            media_import_destination,
        )

        import_root = media_import_destination(
            settings,
            year=year,
            project=project,
            day=day,
        )

    reconciliation = reconcile_import_media_session(
        active_session,
        import_root,
        session_id=active_session_id,
    )

    print("Final Import Session Reconciliation")
    print("===================================")
    print()
    print(
        f"Sources expected   : "
        f"{reconciliation.source_reconciliation.expected_sources}"
    )
    print(
        f"Sources reconciled : "
        f"{reconciliation.source_reconciliation.reconciled_sources}"
    )
    print(
        f"Session ID matches : "
        f"{reconciliation.session_id_matches}"
    )
    print(
        f"Verification safe  : "
        f"{reconciliation.verification.safe_to_release}"
    )
    print(
        f"FINAL STATUS       : "
        f"{reconciliation.status}"
    )
    print()

    if reconciliation.reconciled and state_path is not None:
        state_path.unlink(missing_ok=True)

    return ImportMediaWizardResult(
        session=active_session,
        session_id=active_session_id,
        batches_processed=batches_processed,
        copied=copied,
        failed=failed,
        completed=True,
        reconciliation=reconciliation,
    )
