from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from collections.abc import Callable

from mps.gui.dialogs import (
    BODY_FONT,
    MpsDialog,
    configure_three_action_footer,
    measure_action_button_column_width,
    minimum_three_action_dialog_width,
)
from mps.gui.import_interaction_adapter import PendingImportInteraction
from mps.models.import_file_result import (
    ImportFileResult,
    ImportFileResultStatus,
)
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_progress import ImportProgress
from mps.models.import_workflow import ImportEvent, ImportEventType
from mps.models.import_workflow import ImportResponse, ImportWaitingReason
from mps.services.import_controller import (
    ImportController,
    ImportControllerStatus,
)


EMPTY_VALUE = "—"
IMPORT_WINDOW_GEOMETRY = "1180x900"
IMPORT_WINDOW_MINIMUM = (980, 820)
IMPORT_WINDOW_VERTICAL_RESERVE = 180
SUMMARY_ROW_MIN_HEIGHT = 145
SUMMARY_LEFT_LABEL_MIN_WIDTH = 160
SUMMARY_RIGHT_LABEL_MIN_WIDTH = 110
SUMMARY_VALUE_MIN_WIDTH = 300
SUMMARY_VALUE_WRAP_LENGTH = SUMMARY_VALUE_MIN_WIDTH - 20
RESULTS_ROW_MIN_HEIGHT = 225
RESULTS_TREE_MIN_HEIGHT = 185
RESULTS_TREE_VISIBLE_ROWS = 7
RESULT_TOTALS_MIN_HEIGHT = 30
RESULT_DETAILS_MIN_HEIGHT = 78
RESULT_DETAIL_LINE_MIN_HEIGHT = 24
RESULT_MESSAGES_MIN_HEIGHT = 60
RESULT_MESSAGE_LINE_MIN_HEIGHT = 28
WAITING_DIALOG_GEOMETRY = "760x440"
WAITING_DIALOG_MINIMUM = (720, 400)
WAITING_DIALOG_CONTENT_MIN_WIDTH = 650
WAITING_DIALOG_BUTTON_MIN_WIDTH = 180
WAITING_DIALOG_ACTION_LABELS = (
    "Stop and Resume Later",
    "All Cards Ready",
    "Scan Again",
)

IMPORT_CODE_MESSAGES = {
    "no_new_media": "No new media found.",
    "media_already_processed": "This media has already been processed.",
    "nothing_to_import": "No files need to be imported.",
    "batch_processing_failed": "One or more files could not be processed.",
    "partial_batch_state_recovered": (
        "Verified files from an interrupted batch were recovered."
    ),
    "cancelled_preserve_state": (
        "Import stopped. The session can be resumed later."
    ),
    "no_initial_media": "No import media was found.",
    "worker_returned_incomplete": (
        "The import ended before the session was completed."
    ),
    "runner_exception": "The import could not be started.",
    "worker_exception": (
        "The import worker encountered an unexpected error."
    ),
    "session_not_reconciled": (
        "The import session could not be reconciled."
    ),
    "already_imported": "Already imported.",
    "copy_failed": "The file could not be copied and verified.",
}


def humanize_import_code(
    code: str | None,
    fallback: str | None = None,
) -> str:
    if code in IMPORT_CODE_MESSAGES:
        return IMPORT_CODE_MESSAGES[code]
    if fallback:
        return fallback
    return "The import reported an additional status."


IMPORT_STATUS_LABELS = {
    "idle": "Idle",
    "starting": "Starting",
    "running": "Running",
    "waiting_for_media": "Waiting for media",
    "cancelling": "Stopping safely",
    "stopped": "Stopped",
    "failed": "Failed",
    "completed": "Completed",
}


def humanize_import_status(status: str) -> str:
    return IMPORT_STATUS_LABELS.get(
        status,
        status.replace("_", " ").strip().capitalize() or "Unknown",
    )


IMPORT_PHASE_LABELS = {
    "planned": "Planned",
    "checking": "Checking media",
    "copying": "Copying files",
    "provenance": "Recording provenance",
    "verifying": "Verifying import session",
}


def humanize_import_phase(phase: str) -> str:
    return IMPORT_PHASE_LABELS.get(
        phase,
        phase.replace("_", " ").strip().capitalize() or EMPTY_VALUE,
    )


class WaitingForMediaDialog:
    def __init__(self, parent: tk.Misc, reason: ImportWaitingReason) -> None:
        self._result = ImportResponse.CANCEL_PRESERVE_STATE
        self._dialog = MpsDialog(
            parent,
            title="Waiting for Media",
            size="small",
            resizable=False,
        )
        measured_button_width = measure_action_button_column_width(
            self._dialog.window,
            WAITING_DIALOG_ACTION_LABELS,
        )
        button_column_width = max(
            WAITING_DIALOG_BUTTON_MIN_WIDTH,
            measured_button_width,
        )
        required_dialog_width = minimum_three_action_dialog_width(
            button_column_width
        )
        base_width, base_height = (
            int(value) for value in WAITING_DIALOG_GEOMETRY.split("x")
        )
        dialog_width = max(base_width, required_dialog_width)
        minimum_width = max(WAITING_DIALOG_MINIMUM[0], required_dialog_width)
        self._dialog.window.geometry(f"{dialog_width}x{base_height}")
        self._dialog.window.minsize(
            minimum_width,
            WAITING_DIALOG_MINIMUM[1],
        )
        self._dialog.content.columnconfigure(
            0,
            weight=1,
            minsize=WAITING_DIALOG_CONTENT_MIN_WIDTH,
        )
        configure_three_action_footer(
            self._dialog,
            minimum_button_width=button_column_width,
        )
        descriptions = {
            ImportWaitingReason.PROCESSED_MEDIA_MOUNTED: (
                "Eject the processed card and insert the next card."
            ),
            ImportWaitingReason.NO_MEDIA_MOUNTED: (
                "Insert the next card from this photo session."
            ),
            ImportWaitingReason.BATCH_COMPLETED: (
                "The current card is complete. Insert the next card."
            ),
        }
        self._dialog.add_header("Waiting for Media", descriptions[reason])
        ttk.Label(
            self._dialog.content,
            text="Choose what MPS should do next.",
            font=BODY_FONT,
        ).grid(row=0, column=0, sticky="nw")
        self._dialog.add_footer_button(
            text=WAITING_DIALOG_ACTION_LABELS[0],
            command=lambda: self._choose(
                ImportResponse.CANCEL_PRESERVE_STATE
            ),
            column=1,
        )
        self._dialog.add_footer_button(
            text=WAITING_DIALOG_ACTION_LABELS[1],
            command=lambda: self._choose(ImportResponse.ALL_MEDIA_READY),
            column=2,
        )
        self._dialog.add_footer_button(
            text=WAITING_DIALOG_ACTION_LABELS[2],
            command=lambda: self._choose(ImportResponse.RESCAN_MEDIA),
            column=3,
            padx=(0, 0),
        )
        self._dialog.window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._choose(ImportResponse.CANCEL_PRESERVE_STATE),
        )

    def _choose(self, response: ImportResponse) -> None:
        self._result = response
        self._dialog.close()

    def wait(self) -> ImportResponse:
        self._dialog.show()
        self._dialog.window.wait_window()
        return self._result


def choose_waiting_for_media_action(
    parent: tk.Misc,
    reason: ImportWaitingReason,
) -> ImportResponse:
    return WaitingForMediaDialog(parent, reason).wait()


class ImportWindow:
    """Native status view for structured import workflow events."""

    def __init__(
        self,
        parent: tk.Misc,
        controller: ImportController,
        *,
        destination: str | Path | None = None,
        action: str | None = None,
        poll_interval_ms: int = 75,
        on_terminal: Callable[[], None] | None = None,
    ) -> None:
        self._controller = controller
        self._poll_interval_ms = poll_interval_ms
        self._after_id: str | None = None
        self._destroyed = False
        self._on_terminal = on_terminal
        self._terminal_notified = False
        self._file_results: dict[tuple[str, str], ImportFileResult] = {}
        self._result_rows: dict[tuple[str, str], str] = {}
        self._last_warning_code: str | None = None
        self._last_terminal_code: str | None = None
        self._status_code = ImportControllerStatus.IDLE.value
        self._current_progress: ImportProgress | None = None
        self._dialog = MpsDialog(
            parent,
            title="Import Photographs",
            size="wide",
            modal=False,
        )
        self._dialog.add_header(
            "Import Photographs",
            "Follow the current native import session.",
        )
        self._window = self._dialog.window
        self._window.geometry(IMPORT_WINDOW_GEOMETRY)
        self._window.minsize(*IMPORT_WINDOW_MINIMUM)
        self._variables = {
            name: tk.StringVar(master=self._window, value=value)
            for name, value in {
                "status": humanize_import_status(
                    ImportControllerStatus.IDLE.value
                ),
                "session_id": EMPTY_VALUE,
                "destination": (
                    str(destination) if destination is not None else EMPTY_VALUE
                ),
                "action": action or EMPTY_VALUE,
                "source_card": EMPTY_VALUE,
                "raw": EMPTY_VALUE,
                "jpeg": EMPTY_VALUE,
                "pairs": EMPTY_VALUE,
                "phase": EMPTY_VALUE,
                "current_file": EMPTY_VALUE,
                "current_total": EMPTY_VALUE,
                "percentage": "0%",
                "result_counts": "Verified: 0    Skipped: 0    Failed: 0",
                "selected_source": EMPTY_VALUE,
                "selected_destination": EMPTY_VALUE,
                "selected_detail": EMPTY_VALUE,
                "warning": EMPTY_VALUE,
                "final_result": EMPTY_VALUE,
            }.items()
        }
        self._build_content()
        self._close_button = self._dialog.add_footer_button(
            text="Close",
            command=self.close,
            column=1,
            padx=(0, 0),
        )
        self._window.protocol("WM_DELETE_WINDOW", self.close)
        self._window.bind("<Destroy>", self._on_destroy)
        self._schedule_poll()

    def _build_content(self) -> None:
        content = ttk.Frame(self._dialog.content)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(
            0,
            weight=0,
            minsize=SUMMARY_ROW_MIN_HEIGHT,
        )
        content.rowconfigure(
            1,
            weight=1,
            minsize=RESULTS_ROW_MIN_HEIGHT,
        )
        content.rowconfigure(
            2,
            weight=0,
            minsize=RESULT_TOTALS_MIN_HEIGHT,
        )
        content.rowconfigure(
            3,
            weight=0,
            minsize=RESULT_DETAILS_MIN_HEIGHT,
        )

        self._summary_frame = ttk.Frame(content)
        self._summary_frame.grid(row=0, column=0, sticky="ew")
        self._summary_frame.columnconfigure(
            0,
            weight=0,
            minsize=SUMMARY_LEFT_LABEL_MIN_WIDTH,
        )
        self._summary_frame.columnconfigure(
            1,
            weight=1,
            minsize=SUMMARY_VALUE_MIN_WIDTH,
            uniform="summary-values",
        )
        self._summary_frame.columnconfigure(
            2,
            weight=0,
            minsize=SUMMARY_RIGHT_LABEL_MIN_WIDTH,
        )
        self._summary_frame.columnconfigure(
            3,
            weight=1,
            minsize=SUMMARY_VALUE_MIN_WIDTH,
            uniform="summary-values",
        )
        fields = (
            ("Status", "status", "Destination", "destination"),
            ("Session ID", "session_id", "Current file", "current_file"),
            ("Action", "action", "Phase", "phase"),
            ("Current source", "source_card", "Progress", "current_total"),
            ("RAW / JPG / pairs", "media_counts", "", "percentage"),
        )
        self._summary_labels: dict[str, ttk.Label] = {}
        self._summary_values: dict[str, ttk.Label] = {}
        for row, field_row in enumerate(fields):
            for pair in range(2):
                label, key = field_row[pair * 2:pair * 2 + 2]
                label_column = pair * 2
                if label:
                    self._summary_labels[key] = ttk.Label(
                        self._summary_frame,
                        text=label,
                        font=BODY_FONT,
                    )
                    self._summary_labels[key].grid(
                        row=row,
                        column=label_column,
                        sticky="nw",
                        padx=(0, 12),
                        pady=2,
                    )
                variable = (
                    self._variables[key]
                    if key != "media_counts"
                    else self._media_counts_variable()
                )
                self._summary_values[key] = ttk.Label(
                    self._summary_frame,
                    textvariable=variable,
                    font=BODY_FONT,
                    wraplength=SUMMARY_VALUE_WRAP_LENGTH,
                    justify="left",
                )
                self._summary_values[key].grid(
                    row=row,
                    column=label_column + 1,
                    sticky="nw",
                    padx=(0, 18 if pair == 0 else 0),
                    pady=2,
                )

        self._progressbar = ttk.Progressbar(
            self._summary_frame,
            maximum=100,
            value=0,
            mode="determinate",
        )
        self._progressbar.grid(
            row=len(fields), column=0, columnspan=4, sticky="ew", pady=(6, 8)
        )

        results = ttk.LabelFrame(content, text="Files processed", padding=8)
        results.grid(row=1, column=0, sticky="nsew", pady=(2, 6))
        results.columnconfigure(0, weight=1)
        results.rowconfigure(
            0,
            weight=1,
            minsize=RESULTS_TREE_MIN_HEIGHT,
        )
        self._results_tree = ttk.Treeview(
            results,
            columns=("file", "type", "status"),
            show="headings",
            height=RESULTS_TREE_VISIBLE_ROWS,
            selectmode="browse",
        )
        self._results_tree.heading("file", text="File")
        self._results_tree.heading("type", text="Type")
        self._results_tree.heading("status", text="Status")
        self._results_tree.column("file", width=430, stretch=True)
        self._results_tree.column("type", width=100, stretch=False)
        self._results_tree.column("status", width=130, stretch=False)
        scrollbar = ttk.Scrollbar(
            results,
            orient="vertical",
            command=self._results_tree.yview,
        )
        self._results_tree.configure(yscrollcommand=scrollbar.set)
        self._results_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._results_tree.bind("<<TreeviewSelect>>", self._on_result_selected)

        self._result_totals_frame = ttk.Frame(content)
        self._result_totals_frame.grid(row=2, column=0, sticky="ew")
        self._result_totals_frame.columnconfigure(0, weight=1)
        self._result_counts_label = ttk.Label(
            self._result_totals_frame,
            textvariable=self._variables["result_counts"],
            font=BODY_FONT,
        )
        self._result_counts_label.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(2, 4),
        )

        self._details_frame = ttk.Frame(content)
        self._details_frame.grid(row=3, column=0, sticky="ew")
        self._details_frame.columnconfigure(1, weight=1)
        self._detail_value_labels: dict[str, ttk.Label] = {}
        for row, (label, key) in enumerate((
            ("Source", "selected_source"),
            ("Destination", "selected_destination"),
            ("Details", "selected_detail"),
        )):
            self._details_frame.rowconfigure(
                row,
                weight=0,
                minsize=RESULT_DETAIL_LINE_MIN_HEIGHT,
            )
            ttk.Label(self._details_frame, text=label, font=BODY_FONT).grid(
                row=row, column=0, sticky="nw", padx=(0, 12), pady=0
            )
            self._detail_value_labels[key] = ttk.Label(
                self._details_frame,
                textvariable=self._variables[key],
                font=BODY_FONT,
                wraplength=940,
            )
            self._detail_value_labels[key].grid(
                row=row,
                column=1,
                sticky="ew",
                pady=0,
            )

        self._dialog.footer.rowconfigure(
            0,
            weight=0,
            minsize=RESULT_MESSAGES_MIN_HEIGHT,
        )
        self._dialog.footer.columnconfigure(0, weight=1)
        self._dialog.footer.columnconfigure(1, weight=0)
        self._messages_frame = ttk.Frame(self._dialog.footer)
        self._messages_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 18),
        )
        self._messages_frame.columnconfigure(1, weight=1)
        message_labels: dict[str, ttk.Label] = {}
        for row, (label, key) in enumerate((
            ("Warning", "warning"),
            ("Final result", "final_result"),
        )):
            self._messages_frame.rowconfigure(
                row,
                weight=0,
                minsize=RESULT_MESSAGE_LINE_MIN_HEIGHT,
            )
            ttk.Label(
                self._messages_frame,
                text=label,
                font=BODY_FONT,
            ).grid(row=row, column=0, sticky="nw", padx=(0, 12), pady=0)
            message_labels[key] = ttk.Label(
                self._messages_frame,
                textvariable=self._variables[key],
                font=BODY_FONT,
                wraplength=940,
            )
            message_labels[key].grid(
                row=row,
                column=1,
                sticky="ew",
                pady=0,
            )
        self._warning_label = message_labels["warning"]
        self._final_result_label = message_labels["final_result"]

    def _media_counts_variable(self) -> tk.StringVar:
        variable = tk.StringVar(master=self._window)

        def update(*_args: object) -> None:
            variable.set(
                f"{self._variables['raw'].get()} / "
                f"{self._variables['jpeg'].get()} / "
                f"{self._variables['pairs'].get()}"
            )

        for key in ("raw", "jpeg", "pairs"):
            self._variables[key].trace_add("write", update)
        update()
        return variable

    def _schedule_poll(self) -> None:
        if self._destroyed or self._after_id is not None:
            return
        self._after_id = self._window.after(
            self._poll_interval_ms,
            self._poll_events,
        )

    def _poll_events(self) -> None:
        self._after_id = None
        if self._destroyed or not self._window.winfo_exists():
            return
        for event in self._controller.drain_events():
            self.apply_event(event)
        self._schedule_poll()

    def apply_event(self, event: ImportEvent) -> None:
        payload = event.payload
        status_by_event = {
            ImportEventType.SESSION_STARTED: "running",
            ImportEventType.MEDIA_DISCOVERY_STARTED: "running",
            ImportEventType.WAITING_FOR_MEDIA: "waiting_for_media",
            ImportEventType.BATCH_STARTED: "running",
            ImportEventType.BATCH_PLANNED: "running",
            ImportEventType.RECONCILIATION_STARTED: "running",
            ImportEventType.FAILED: "failed",
            ImportEventType.STOPPED: "stopped",
            ImportEventType.COMPLETED: "completed",
        }
        if event.type in status_by_event:
            self._status_code = status_by_event[event.type]
            self._set(
                "status",
                humanize_import_status(self._status_code),
            )

        if event.type is ImportEventType.SESSION_STARTED:
            self._set("session_id", payload.get("session_id"))
            self._set("destination", payload.get("destination"))
            self._set("action", payload.get("action"))
        elif event.type is ImportEventType.MEDIA_DISCOVERED:
            self._apply_media_discovered(payload)
        elif event.type is ImportEventType.BATCH_PLANNED:
            self._set("destination", payload.get("destination"))
            self._set("phase", humanize_import_phase("planned"))
        elif event.type is ImportEventType.PROGRESS:
            progress = payload.get("progress")
            if isinstance(progress, ImportProgress):
                self._apply_progress(progress)
        elif event.type is ImportEventType.FILE_RESULT:
            result = payload.get("result")
            if isinstance(result, ImportFileResult):
                self._apply_file_result(result)
        elif event.type is ImportEventType.INTERACTION_REQUESTED:
            interaction = payload.get("interaction")
            if isinstance(interaction, PendingImportInteraction):
                self._resolve_interaction(interaction)
        elif event.type is ImportEventType.WARNING:
            code = payload.get("code")
            fallback = payload.get("message")
            self._last_warning_code = str(code) if code is not None else None
            self._set(
                "warning",
                humanize_import_code(
                    self._last_warning_code,
                    str(fallback) if fallback is not None else None,
                ),
            )
        elif event.type is ImportEventType.FAILED:
            code = payload.get("code")
            self._last_terminal_code = str(code) if code is not None else None
            fallback = payload.get("message")
            reason = humanize_import_code(
                self._last_terminal_code,
                str(fallback) if fallback is not None else None,
            )
            self._set(
                "final_result",
                f"Import failed. {reason}",
            )
        elif event.type is ImportEventType.STOPPED:
            code = payload.get("code")
            self._last_terminal_code = str(code) if code is not None else None
            self._set(
                "final_result",
                humanize_import_code(
                    self._last_terminal_code,
                    "Import stopped. The session can be resumed later.",
                ),
            )
        elif event.type is ImportEventType.COMPLETED:
            self._last_terminal_code = None
            self._set("final_result", "Import completed successfully.")

        if event.type in {
            ImportEventType.FAILED,
            ImportEventType.STOPPED,
            ImportEventType.COMPLETED,
        }:
            self._notify_terminal()

    def _resolve_interaction(
        self,
        interaction: PendingImportInteraction,
    ) -> None:
        interaction.respond(choose_waiting_for_media_action(
            self._window,
            interaction.request.reason,
        ))

    def _notify_terminal(self) -> None:
        if self._terminal_notified:
            return
        self._terminal_notified = True
        if self._on_terminal is not None:
            self._on_terminal()

    def _apply_media_discovered(self, payload: object) -> None:
        if not hasattr(payload, "get"):
            return
        selection = payload.get("selection")
        if isinstance(selection, ImportMediaSelection):
            sources = tuple(source.root for source in selection.sources)
            self._set("source_card", sources[0] if sources else None)
            self._set("raw", selection.total_raw_files)
            self._set("jpeg", selection.total_jpeg_files)
            self._set(
                "pairs",
                sum(source.pair_count for source in selection.sources),
            )
            return
        self._set("source_card", payload.get("source"))
        self._set("raw", payload.get("raw_file_count"))
        self._set("jpeg", payload.get("jpeg_file_count"))
        self._set("pairs", payload.get("pair_count"))

    def _apply_progress(self, progress: ImportProgress) -> None:
        self._current_progress = progress
        self._set("phase", humanize_import_phase(progress.phase))
        self._set(
            "current_file",
            EMPTY_VALUE if progress.phase == "verifying" else progress.source.name,
        )
        self._set("current_total", f"{progress.current} / {progress.total}")
        self._set("percentage", f"{progress.percent}%")
        self._progressbar.configure(value=progress.percent)

    @staticmethod
    def _result_key(result: ImportFileResult) -> tuple[str, str]:
        return (
            str(result.source),
            str(result.destination) if result.destination is not None else "",
        )

    def _apply_file_result(self, result: ImportFileResult) -> None:
        key = self._result_key(result)
        previous = self._file_results.get(key)
        ranks = {
            ImportFileResultStatus.SKIPPED: 1,
            ImportFileResultStatus.VERIFIED: 2,
            ImportFileResultStatus.FAILED: 3,
        }
        if previous == result:
            return
        if previous is not None and ranks[result.status] <= ranks[previous.status]:
            return

        self._file_results[key] = result
        values = (
            result.source.name,
            result.media_type.value.upper(),
            result.status.value.title(),
        )
        row = self._result_rows.get(key)
        if row is None:
            row = f"file-result-{len(self._result_rows)}"
            self._result_rows[key] = row
            self._results_tree.insert("", "end", iid=row, values=values)
        else:
            self._results_tree.item(row, values=values)
        self._update_result_counts()

    def _update_result_counts(self) -> None:
        counts = {
            status: sum(
                result.status is status for result in self._file_results.values()
            )
            for status in ImportFileResultStatus
        }
        self._set(
            "result_counts",
            f"Verified: {counts[ImportFileResultStatus.VERIFIED]}    "
            f"Skipped: {counts[ImportFileResultStatus.SKIPPED]}    "
            f"Failed: {counts[ImportFileResultStatus.FAILED]}",
        )

    def _on_result_selected(self, _event: object | None = None) -> None:
        selected = self._results_tree.selection()
        if not selected:
            return
        row = selected[0]
        key = next(
            (key for key, value in self._result_rows.items() if value == row),
            None,
        )
        if key is None:
            return
        result = self._file_results[key]
        self._set("selected_source", result.source)
        self._set(
            "selected_destination",
            result.destination if result.destination is not None else EMPTY_VALUE,
        )
        message = humanize_import_code(result.reason_code, result.detail)
        if result.detail and message != result.detail:
            message = f"{message} {result.detail}"
        self._set("selected_detail", message)

    def _set(self, key: str, value: object | None) -> None:
        if value is not None:
            self._variables[key].set(str(value))

    def close(self) -> None:
        if not self._controller.worker_alive:
            for event in self._controller.drain_events():
                self.apply_event(event)

        terminal_status = self._controller.status in {
            ImportControllerStatus.IDLE,
            ImportControllerStatus.COMPLETED,
            ImportControllerStatus.FAILED,
            ImportControllerStatus.STOPPED,
        }
        if not terminal_status and self._controller.worker_alive:
            stop_requested = messagebox.askyesno(
                "Import Still Active",
                (
                    "The import is still active and cannot be closed yet.\n\n"
                    "Stop safely and resume later?"
                ),
                parent=self._window,
            )
            if stop_requested:
                self._controller.request_cancel()
            return
        self._destroyed = True
        if self._after_id is not None:
            self._window.after_cancel(self._after_id)
            self._after_id = None
        self._dialog.close()

    def _on_destroy(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget is self._window:
            self._destroyed = True
            self._after_id = None
