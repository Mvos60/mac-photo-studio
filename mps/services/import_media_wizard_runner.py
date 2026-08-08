from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

from mps.config import Settings
from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.models.import_media_session import (
    ImportMediaSession,
    ImportMediaSessionDestination,
)
from mps.models.import_media_batch_plan import ImportMediaBatchPlan
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_photo_selection import ImportPhotoSelectionResponse
from mps.models.import_progress import ImportProgress
from mps.models.import_file_result import ImportFileResult
from mps.models.import_workflow import (
    ImportEvent,
    ImportEventType,
    ImportInteractionAdapter,
    ImportRequest,
    ImportRequestType,
    ImportResponse,
    ImportWaitingReason,
)
from mps.models.import_media_wizard_result import (
    ImportMediaWizardResult,
)
from mps.services.import_media_batch_planner import media_import_destination
from mps.services.import_media_batch_processor import (
    process_import_media_batch,
)
from mps.services.import_media_discovery import discover_import_media
from mps.services.import_photo_candidates import (
    build_import_photo_candidates,
    source_candidate_paths,
)
from mps.services.import_media_new_source_detector import (
    detect_new_media_sources,
)
from mps.services.media_source_identity import media_source_fingerprint
from mps.services.import_media_partial_batch_recovery import (
    recover_verified_partial_batch_sources,
)
from mps.services.import_media_cli_adapter import (
    CliImportEventSink,
    CliImportInteractionAdapter,
)
from mps.services.import_media_session_reconciler import (
    reconcile_import_media_session,
)
from mps.services.import_media_session_store import (
    save_import_media_session,
)


def _new_session_id() -> str:
    return f"MPS-SESSION-{uuid4()}"


def _validate_active_destination(
    session: ImportMediaSession,
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
    destination_selection: ImportDestinationSelection | None,
) -> None:
    stored = session.destination

    if stored is None:
        if destination_selection is not None and (
            session.processed_source_files
            or session.source_fingerprints
        ):
            raise ValueError(
                "A structured destination cannot be attached to "
                "a non-empty legacy import session"
            )
        return

    if destination_selection is None:
        raise ValueError(
            "The active import session requires its structured "
            "destination selection"
        )

    if destination_selection != stored.selection:
        raise ValueError(
            "The supplied destination selection conflicts with "
            "the active import session"
        )

    requested_import_root = media_import_destination(
        settings,
        year=year,
        project=project,
        day=day,
        destination_selection=destination_selection,
    )

    if requested_import_root != stored.import_root:
        raise ValueError(
            "The configured import destination conflicts with "
            "the active import session"
        )


def _record_destination(
    session: ImportMediaSession,
    selection: ImportDestinationSelection | None,
    import_root: Path,
) -> None:
    if selection is None:
        return

    destination = ImportMediaSessionDestination(
        selection=selection,
        import_root=import_root,
    )

    if session.destination is None:
        session.destination = destination
        return

    if session.destination != destination:
        raise ValueError(
            "Import session destination conflicts with "
            "the verified media batch destination"
        )


def _reconciliation_failure_payload(reconciliation) -> dict[str, object]:
    sources = reconciliation.source_reconciliation
    verification = reconciliation.verification
    return {
        "code": "session_not_reconciled",
        "missing_manifest_sources": tuple(sources.missing_from_manifest),
        "unexpected_manifest_sources": tuple(
            sources.unexpected_manifest_sources
        ),
        "unverified_destinations": tuple(sources.unverified_destinations),
        "provenance_failures": tuple(sources.provenance_failures),
        "missing_files": tuple(verification.missing_files),
        "checksum_mismatches": tuple(verification.checksum_mismatches),
        "provenance_errors": tuple(verification.provenance_errors),
    }


def _run_import_media_session(
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
    destination_selection: ImportDestinationSelection | None = None,
    session_id: str | None = None,
    session: ImportMediaSession | None = None,
    session_state_path: str | Path | None = None,
    protect_existing_state_until_first_verified_batch: bool = False,
    progress_callback: Callable[[ImportProgress], None] | None = None,
    event_sink: Callable[[ImportEvent], None] | None = None,
    interaction_adapter: ImportInteractionAdapter | None = None,
    wait_for_initial_media: bool = False,
    enable_photo_selection: bool = False,
) -> ImportMediaWizardResult:
    """Process and reconcile one or more photo media batches."""

    emit = event_sink or CliImportEventSink()
    interaction = interaction_adapter or CliImportInteractionAdapter()

    active_session_id = (
        session.session_id
        if session is not None and session.session_id is not None
        else session_id or _new_session_id()
    )

    active_session = session or ImportMediaSession()
    active_session.session_id = active_session_id

    emit(ImportEvent(
        ImportEventType.SESSION_STARTED,
        {"session_id": active_session_id},
    ))

    _validate_active_destination(
        active_session,
        settings,
        year=year,
        project=project,
        day=day,
        destination_selection=destination_selection,
    )

    state_path = (
        Path(session_state_path)
        if session_state_path is not None
        else None
    )
    protected_state_pending = bool(
        protect_existing_state_until_first_verified_batch
        and state_path is not None
        and state_path.exists()
    )

    batches_processed = 0
    copied = 0
    failed = 0
    import_root: Path | None = None
    runtime_seen_source_fingerprints: set[str] = set()

    def stop_incomplete(code: str) -> ImportMediaWizardResult:
        emit(ImportEvent(
            ImportEventType.STOPPED,
            {"code": code},
        ))
        return ImportMediaWizardResult(
            session=active_session,
            session_id=active_session_id,
            batches_processed=batches_processed,
            copied=copied,
            failed=failed,
            completed=False,
        )

    while True:
        emit(ImportEvent(
            ImportEventType.MEDIA_DISCOVERY_STARTED,
            {"session_id": active_session_id},
        ))
        selection = discover_import_media(settings)
        new_media = detect_new_media_sources(
            active_session,
            selection,
        )
        if enable_photo_selection and runtime_seen_source_fingerprints:
            new_media = ImportMediaSelection(sources=[
                source
                for source in new_media.sources
                if media_source_fingerprint(source)
                not in runtime_seen_source_fingerprints
            ])

        emit(ImportEvent(
            ImportEventType.MEDIA_DISCOVERED,
            {
                "selection": new_media,
                "mounted_source_count": selection.source_count,
                "new_source_count": new_media.source_count,
                "raw_file_count": new_media.total_raw_files,
                "jpeg_file_count": new_media.total_jpeg_files,
                "already_processed": (
                    new_media.empty and not selection.empty
                ),
            },
        ))

        if new_media.empty:
            if (
                batches_processed == 0
                and not active_session.processed_source_files
            ):
                emit(ImportEvent(
                    ImportEventType.WARNING,
                    {
                        "code": "no_new_media",
                    },
                ))
                if wait_for_initial_media:
                    reason = ImportWaitingReason.NO_MEDIA_MOUNTED
                    emit(ImportEvent(
                        ImportEventType.WAITING_FOR_MEDIA,
                        {"reason": reason},
                    ))
                    response = interaction.request(ImportRequest(
                        ImportRequestType.NEXT_MEDIA_ACTION,
                        reason,
                    ))
                    if response is ImportResponse.RESCAN_MEDIA:
                        continue
                    if response is ImportResponse.CANCEL_PRESERVE_STATE:
                        return stop_incomplete("cancelled_preserve_state")
                    return stop_incomplete("no_initial_media")
                return ImportMediaWizardResult(
                    session=active_session,
                    session_id=active_session_id,
                    batches_processed=0,
                    copied=0,
                    failed=0,
                    completed=False,
                )

            if not selection.empty:
                reason = ImportWaitingReason.PROCESSED_MEDIA_MOUNTED
                emit(ImportEvent(
                    ImportEventType.WARNING,
                    {"code": "media_already_processed"},
                ))
                emit(ImportEvent(
                    ImportEventType.WAITING_FOR_MEDIA,
                    {"reason": reason},
                ))
                response = interaction.request(ImportRequest(
                    ImportRequestType.NEXT_MEDIA_ACTION,
                    reason,
                ))

                if response is ImportResponse.RESCAN_MEDIA:
                    continue

                if response is ImportResponse.CANCEL_PRESERVE_STATE:
                    return stop_incomplete("cancelled_preserve_state")

                break

            reason = ImportWaitingReason.NO_MEDIA_MOUNTED
            emit(ImportEvent(
                ImportEventType.WAITING_FOR_MEDIA,
                {"reason": reason},
            ))
            response = interaction.request(ImportRequest(
                ImportRequestType.NEXT_MEDIA_ACTION,
                reason,
            ))

            if response is ImportResponse.RESCAN_MEDIA:
                continue

            if response is ImportResponse.CANCEL_PRESERVE_STATE:
                return stop_incomplete("cancelled_preserve_state")

            break

        selected_source_files: tuple[Path, ...] | None = None
        completed_selection: ImportMediaSelection | None = None
        partial_sources = []
        if enable_photo_selection:
            candidates = build_import_photo_candidates(
                new_media,
                settings,
                processed_source_files=active_session.processed_source_files,
            )
            ambiguous = tuple(
                candidate for candidate in candidates if candidate.ambiguous
            )
            if ambiguous:
                emit(ImportEvent(
                    ImportEventType.FAILED,
                    {
                        "code": "ambiguous_photo_stem",
                        "conflicting_paths": tuple(
                            str(path)
                            for candidate in ambiguous
                            for path in candidate.source_paths
                        ),
                    },
                ))
                return ImportMediaWizardResult(
                    session=active_session,
                    session_id=active_session_id,
                    batches_processed=batches_processed,
                    copied=copied,
                    failed=failed,
                    completed=False,
                )
            if not candidates:
                selected_source_files = ()
                completed_selection = new_media
            else:
                response = interaction.request(ImportRequest(
                    ImportRequestType.SELECT_PHOTOS,
                    candidates=candidates,
                ))
                if not isinstance(response, ImportPhotoSelectionResponse):
                    return stop_incomplete("photo_selection_cancelled")
                selected_source_files = response.selected_paths(candidates)
                if not selected_source_files:
                    return stop_incomplete("photo_selection_empty")
                selected_paths = set(selected_source_files)
                completed_sources = []
                for source in new_media.sources:
                    offered = source_candidate_paths(source, candidates)
                    if offered and offered <= selected_paths:
                        completed_sources.append(source)
                    elif offered:
                        partial_sources.append(source)
                completed_selection = ImportMediaSelection(
                    sources=completed_sources
                )

        emit(ImportEvent(
            ImportEventType.BATCH_STARTED,
            {"source_count": new_media.source_count},
        ))

        def publish_plan(plan: ImportMediaBatchPlan) -> None:
            emit(ImportEvent(
                ImportEventType.BATCH_PLANNED,
                {
                    "destination": plan.destination,
                    "raw_file_count": new_media.total_raw_files,
                    "jpeg_file_count": new_media.total_jpeg_files,
                },
            ))

        def publish_file_result(file_result: ImportFileResult) -> None:
            emit(ImportEvent(
                ImportEventType.FILE_RESULT,
                {"result": file_result},
            ))

        result = process_import_media_batch(
            new_media,
            active_session,
            settings,
            year=year,
            project=project,
            day=day,
            session_id=active_session_id,
            destination_selection=destination_selection,
            progress_callback=progress_callback,
            plan_callback=publish_plan,
            file_result_callback=publish_file_result,
            source_files=selected_source_files,
            completed_selection=completed_selection,
        )

        copied += result.copied
        failed += result.failed

        if result.nothing_to_import:
            emit(ImportEvent(
                ImportEventType.WARNING,
                {
                    "code": "nothing_to_import",
                },
            ))

            if (
                state_path is not None
                and not protected_state_pending
            ):
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
            emit(ImportEvent(
                ImportEventType.FAILED,
                {
                    "code": "batch_processing_failed",
                },
            ))
            return ImportMediaWizardResult(
                session=active_session,
                session_id=active_session_id,
                batches_processed=batches_processed,
                copied=copied,
                failed=failed,
                completed=False,
            )

        if enable_photo_selection:
            runtime_seen_source_fingerprints.update(
                media_source_fingerprint(source)
                for source in partial_sources
            )

        _record_destination(
            active_session,
            destination_selection,
            result.plan.destination,
        )

        batches_processed += 1
        import_root = result.plan.destination

        if state_path is not None:
            save_import_media_session(
                active_session,
                state_path,
            )
            protected_state_pending = False

        emit(ImportEvent(
            ImportEventType.BATCH_COMPLETED,
            {
                "batch_number": batches_processed,
                "copied": result.copied,
                "destination": result.plan.destination,
            },
        ))

        reason = ImportWaitingReason.BATCH_COMPLETED
        emit(ImportEvent(
            ImportEventType.WAITING_FOR_MEDIA,
            {"reason": reason},
        ))
        response = interaction.request(ImportRequest(
            ImportRequestType.NEXT_MEDIA_ACTION,
            reason,
        ))

        if response is ImportResponse.CANCEL_PRESERVE_STATE:
            return stop_incomplete("cancelled_preserve_state")

        if response is ImportResponse.ALL_MEDIA_READY:
            break

    if import_root is None:
        import_root = media_import_destination(
            settings,
            year=year,
            project=project,
            day=day,
            destination_selection=destination_selection,
        )

    emit(ImportEvent(
        ImportEventType.RECONCILIATION_STARTED,
        {"import_root": import_root},
    ))
    reconciliation = reconcile_import_media_session(
        active_session,
        import_root,
        session_id=active_session_id,
    )

    emit(ImportEvent(
        ImportEventType.RECONCILIATION_COMPLETED,
        {"reconciliation": reconciliation},
    ))

    if (
        not reconciliation.reconciled
        and reconciliation.source_reconciliation.unexpected_manifest_sources
    ):
        recovery = recover_verified_partial_batch_sources(
            active_session,
            import_root,
            session_id=active_session_id,
            protected_state_pending=protected_state_pending,
        )
        if recovery.recovered:
            if state_path is not None:
                save_import_media_session(active_session, state_path)
            emit(ImportEvent(
                ImportEventType.WARNING,
                {
                    "code": "partial_batch_state_recovered",
                    "recovered_source_count": len(
                        recovery.recovered_sources
                    ),
                },
            ))
            emit(ImportEvent(
                ImportEventType.RECONCILIATION_STARTED,
                {"import_root": import_root, "retry": True},
            ))
            reconciliation = reconcile_import_media_session(
                active_session,
                import_root,
                session_id=active_session_id,
            )
            emit(ImportEvent(
                ImportEventType.RECONCILIATION_COMPLETED,
                {"reconciliation": reconciliation, "retry": True},
            ))

    if not reconciliation.reconciled:
        emit(ImportEvent(
            ImportEventType.FAILED,
            _reconciliation_failure_payload(reconciliation),
        ))
        return ImportMediaWizardResult(
            session=active_session,
            session_id=active_session_id,
            batches_processed=batches_processed,
            copied=copied,
            failed=failed,
            completed=False,
            reconciliation=reconciliation,
        )

    if state_path is not None:
        state_path.unlink(missing_ok=True)

    result = ImportMediaWizardResult(
        session=active_session,
        session_id=active_session_id,
        batches_processed=batches_processed,
        copied=copied,
        failed=failed,
        completed=True,
        reconciliation=reconciliation,
    )
    emit(ImportEvent(
        ImportEventType.COMPLETED,
        {
            "batches_processed": batches_processed,
            "copied": copied,
        },
    ))
    return result


def run_import_media_session(
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
    destination_selection: ImportDestinationSelection | None = None,
    session_id: str | None = None,
    session: ImportMediaSession | None = None,
    session_state_path: str | Path | None = None,
    protect_existing_state_until_first_verified_batch: bool = False,
    progress_callback: Callable[[ImportProgress], None] | None = None,
    event_sink: Callable[[ImportEvent], None] | None = None,
    interaction_adapter: ImportInteractionAdapter | None = None,
    wait_for_initial_media: bool = False,
    enable_photo_selection: bool = False,
) -> ImportMediaWizardResult:
    """Process and reconcile one or more photo media batches."""

    try:
        return _run_import_media_session(
            settings,
            year=year,
            project=project,
            day=day,
            destination_selection=destination_selection,
            session_id=session_id,
            session=session,
            session_state_path=session_state_path,
            protect_existing_state_until_first_verified_batch=(
                protect_existing_state_until_first_verified_batch
            ),
            progress_callback=progress_callback,
            event_sink=event_sink,
            interaction_adapter=interaction_adapter,
            wait_for_initial_media=wait_for_initial_media,
            enable_photo_selection=enable_photo_selection,
        )
    except Exception as exc:
        if event_sink is not None:
            event_sink(ImportEvent(
                ImportEventType.FAILED,
                {
                    "code": "runner_exception",
                    "exception_type": type(exc).__name__,
                },
            ))
        raise
