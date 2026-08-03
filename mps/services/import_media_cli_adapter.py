from __future__ import annotations

from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_workflow import (
    ImportEvent,
    ImportEventType,
    ImportRequest,
    ImportResponse,
    ImportWaitingReason,
)
from mps.services.import_media_report import build_media_report


class CliImportInteractionAdapter:
    """Translate typed import interaction into the existing CLI dialogue."""

    def request(self, request: ImportRequest) -> ImportResponse:
        if request.reason is ImportWaitingReason.PROCESSED_MEDIA_MOUNTED:
            print(
                "Eject or unmount the processed media and "
                "insert the next card from the same photo session."
            )
        elif request.reason is ImportWaitingReason.NO_MEDIA_MOUNTED:
            print(
                "No new media is mounted. The next card from the "
                "same photo session may still need to be inserted."
            )
            print("This includes a matching RAW or JPG card.")

        answer = input(
            "Press Enter to scan; type no only when all "
            "cards are imported: "
        ).strip().lower()

        if answer in {"n", "no"}:
            return ImportResponse.ALL_MEDIA_READY
        return ImportResponse.RESCAN_MEDIA


class CliImportEventSink:
    """Render structured runner events with the legacy CLI wording."""

    def __call__(self, event: ImportEvent) -> None:
        if event.type is ImportEventType.MEDIA_DISCOVERED:
            selection = event.payload["selection"]
            if not isinstance(selection, ImportMediaSelection):
                raise TypeError("media_discovered requires a selection")
            if event.payload.get("already_processed"):
                print(
                    "Mounted photo media has already been processed "
                    "in this session."
                )
            else:
                print(build_media_report(selection))
            print()
        elif event.type in {
            ImportEventType.WARNING,
            ImportEventType.FAILED,
        }:
            messages = {
                "no_new_media": "No new photo media available.",
                "nothing_to_import": (
                    "No new photo files found.\n"
                    "All discovered photo files were already imported."
                ),
                "batch_processing_failed": (
                    "Media batch processing failed."
                ),
            }
            message = messages.get(event.payload.get("code"))
            if message is not None:
                print(message)
        elif event.type is ImportEventType.BATCH_COMPLETED:
            print(
                "Media batch verified. "
                f"Copied {event.payload['copied']} file(s)."
            )
            print("MPS has finished reading the current media.")
            print(
                "Keep all cards from the same photo session together, "
                "including a matching RAW or JPG card."
            )
            print(
                "Eject or unmount the current card, then insert the "
                "next card."
            )
            print()
        elif event.type is ImportEventType.RECONCILIATION_COMPLETED:
            reconciliation = event.payload["reconciliation"]
            print("Final Import Session Reconciliation")
            print("===================================")
            print()
            print(
                "Sources expected   : "
                f"{reconciliation.source_reconciliation.expected_sources}"
            )
            print(
                "Sources reconciled : "
                f"{reconciliation.source_reconciliation.reconciled_sources}"
            )
            print(
                "Session ID matches : "
                f"{reconciliation.session_id_matches}"
            )
            print(
                "Verification safe  : "
                f"{reconciliation.verification.safe_to_release}"
            )
            print(f"FINAL STATUS       : {reconciliation.status}")
            print()
