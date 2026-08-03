from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from mps.gui.dialogs import BODY_FONT, MpsDialog
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_progress import ImportProgress
from mps.models.import_workflow import ImportEvent, ImportEventType
from mps.services.import_controller import (
    ImportController,
    ImportControllerStatus,
)


EMPTY_VALUE = "—"


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
    ) -> None:
        self._controller = controller
        self._poll_interval_ms = poll_interval_ms
        self._after_id: str | None = None
        self._destroyed = False
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
        self._variables = {
            name: tk.StringVar(master=self._window, value=value)
            for name, value in {
                "status": ImportControllerStatus.IDLE.value,
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
                "source": EMPTY_VALUE,
                "progress_destination": EMPTY_VALUE,
                "current_total": EMPTY_VALUE,
                "percentage": "0%",
                "message": EMPTY_VALUE,
                "final_status": EMPTY_VALUE,
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
        content.columnconfigure(1, weight=1)
        fields = (
            ("Status", "status"),
            ("Session ID", "session_id"),
            ("Destination", "destination"),
            ("Action", "action"),
            ("Current source", "source_card"),
            ("RAW / JPG / pairs", "media_counts"),
            ("Phase", "phase"),
            ("Current file", "current_file"),
            ("Source", "source"),
            ("File destination", "progress_destination"),
            ("Progress", "current_total"),
            ("Message", "message"),
            ("Final status", "final_status"),
        )
        for row, (label, key) in enumerate(fields):
            ttk.Label(content, text=label, font=BODY_FONT).grid(
                row=row, column=0, sticky="nw", padx=(0, 14), pady=4
            )
            variable = (
                self._variables[key]
                if key != "media_counts"
                else self._media_counts_variable()
            )
            ttk.Label(
                content,
                textvariable=variable,
                font=BODY_FONT,
                wraplength=820,
            ).grid(row=row, column=1, sticky="ew", pady=4)

        self._progressbar = ttk.Progressbar(
            content,
            maximum=100,
            value=0,
            mode="determinate",
        )
        self._progressbar.grid(
            row=len(fields), column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )
        ttk.Label(
            content,
            textvariable=self._variables["percentage"],
            font=BODY_FONT,
        ).grid(row=len(fields) + 1, column=1, sticky="e", pady=(4, 0))

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
            ImportEventType.COMPLETED: "completed",
        }
        if event.type in status_by_event:
            self._set("status", status_by_event[event.type])

        if event.type is ImportEventType.SESSION_STARTED:
            self._set("session_id", payload.get("session_id"))
            self._set("destination", payload.get("destination"))
            self._set("action", payload.get("action"))
        elif event.type is ImportEventType.MEDIA_DISCOVERED:
            self._apply_media_discovered(payload)
        elif event.type is ImportEventType.BATCH_PLANNED:
            self._set("destination", payload.get("destination"))
            self._set("phase", "planned")
        elif event.type is ImportEventType.PROGRESS:
            progress = payload.get("progress")
            if isinstance(progress, ImportProgress):
                self._apply_progress(progress)
        elif event.type is ImportEventType.WARNING:
            self._set("message", payload.get("message") or payload.get("code"))
        elif event.type is ImportEventType.FAILED:
            self._set(
                "message",
                payload.get("message")
                or payload.get("exception_type")
                or payload.get("code"),
            )
            self._set("final_status", "failed")
        elif event.type is ImportEventType.RECONCILIATION_COMPLETED:
            reconciliation = payload.get("reconciliation")
            self._set("final_status", getattr(reconciliation, "status", None))
        elif event.type is ImportEventType.COMPLETED:
            self._set("final_status", payload.get("status") or "completed")

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
        self._set("phase", progress.phase)
        self._set("current_file", progress.source.name)
        self._set("source", progress.source)
        self._set("progress_destination", progress.destination)
        self._set("current_total", f"{progress.current} / {progress.total}")
        self._set("percentage", f"{progress.percent}%")
        self._progressbar.configure(value=progress.percent)

    def _set(self, key: str, value: object | None) -> None:
        if value is not None:
            self._variables[key].set(str(value))

    def close(self) -> None:
        if self._controller.status not in {
            ImportControllerStatus.IDLE,
            ImportControllerStatus.COMPLETED,
            ImportControllerStatus.FAILED,
        }:
            messagebox.showinfo(
                "Import Still Active",
                "The import is still active and cannot be closed yet.",
                parent=self._window,
            )
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
