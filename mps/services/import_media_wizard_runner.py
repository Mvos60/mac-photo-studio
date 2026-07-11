from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from mps.config import Settings
from mps.models.import_media_session import ImportMediaSession
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


def _new_session_id() -> str:
    return f"MPS-SESSION-{uuid4()}"


def run_import_media_session(
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
    session_id: str | None = None,
) -> ImportMediaWizardResult:
    """Process and reconcile one or more photo media batches."""

    active_session_id = session_id or _new_session_id()
    session = ImportMediaSession()

    batches_processed = 0
    copied = 0
    failed = 0
    import_root: Path | None = None

    while True:
        selection = discover_import_media(settings)
        new_media = detect_new_media_sources(
            session,
            selection,
        )

        print(build_media_report(new_media))
        print()

        if new_media.empty:
            if batches_processed == 0:
                print("No new photo media available.")
                return ImportMediaWizardResult(
                    session=session,
                    session_id=active_session_id,
                    batches_processed=0,
                    copied=0,
                    failed=0,
                    completed=False,
                )

            answer = input(
                "No new media found. Finish import session? [Y/n]: "
            ).strip().lower()

            if answer in {"n", "no"}:
                continue

            break

        result = process_import_media_batch(
            new_media,
            session,
            settings,
            year=year,
            project=project,
            day=day,
            session_id=active_session_id,
        )

        copied += result.copied
        failed += result.failed

        if not result.success:
            print("Media batch processing failed.")
            return ImportMediaWizardResult(
                session=session,
                session_id=active_session_id,
                batches_processed=batches_processed,
                copied=copied,
                failed=failed,
                completed=False,
            )

        batches_processed += 1
        import_root = result.plan.destination

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
        return ImportMediaWizardResult(
            session=session,
            session_id=active_session_id,
            batches_processed=batches_processed,
            copied=copied,
            failed=failed,
            completed=False,
        )

    reconciliation = reconcile_import_media_session(
        session,
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

    return ImportMediaWizardResult(
        session=session,
        session_id=active_session_id,
        batches_processed=batches_processed,
        copied=copied,
        failed=failed,
        completed=True,
        reconciliation=reconciliation,
    )
