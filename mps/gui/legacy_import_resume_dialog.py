from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from mps.config import Settings
from mps.gui.dialogs import BODY_FONT, MpsDialog
from mps.services.import_media_batch_planner import media_import_destination


@dataclass(frozen=True, slots=True)
class LegacyImportDestination:
    year: int
    project: str
    day: str


class LegacyImportResumeDialog:
    def __init__(self, parent: tk.Misc, settings: Settings) -> None:
        self._settings = settings
        self._result: LegacyImportDestination | None = None
        self._dialog = MpsDialog(
            parent,
            title="Resume Legacy Import",
            size="medium",
            resizable=False,
        )
        self._dialog.add_header(
            "Resume Legacy Import",
            "Enter the original legacy destination values for this session.",
        )
        window = self._dialog.window
        self._year_var = tk.StringVar(
            master=window,
            value=str(datetime.now().year),
        )
        self._project_var = tk.StringVar(master=window)
        self._day_var = tk.StringVar(master=window)
        self._preview_var = tk.StringVar(master=window, value="—")
        self._build_fields()
        for variable in (
            self._year_var,
            self._project_var,
            self._day_var,
        ):
            variable.trace_add("write", self._update_preview)
        self._update_preview()
        self._dialog.add_footer_button(
            text="Cancel", command=self._cancel, column=1
        )
        self._dialog.add_footer_button(
            text="Resume", command=self._confirm, column=2, padx=(0, 0)
        )
        window.protocol("WM_DELETE_WINDOW", self._cancel)
        window.bind("<Escape>", lambda _event: self._cancel())

    @property
    def result(self) -> LegacyImportDestination | None:
        return self._result

    def _build_fields(self) -> None:
        form = ttk.Frame(self._dialog.content)
        form.grid(row=0, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)
        fields = (
            ("Year", self._year_var),
            ("Project", self._project_var),
            ("Day / Session", self._day_var),
            ("Destination", self._preview_var),
        )
        for row, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label, font=BODY_FONT).grid(
                row=row, column=0, sticky="w", padx=(0, 14), pady=8
            )
            ttk.Entry(
                form,
                textvariable=variable,
                font=BODY_FONT,
                state="readonly" if label == "Destination" else "normal",
            ).grid(row=row, column=1, sticky="ew", pady=8)

    def _values(self) -> LegacyImportDestination:
        year_text = self._year_var.get().strip()
        try:
            year = int(year_text)
        except ValueError as exc:
            raise ValueError("Year must be an integer") from exc
        return LegacyImportDestination(
            year=year,
            project=self._project_var.get().strip(),
            day=self._day_var.get().strip(),
        )

    def _update_preview(self, *_args: object) -> None:
        try:
            values = self._values()
        except ValueError:
            self._preview_var.set("Enter a valid year to preview the destination.")
            return
        self._preview_var.set(str(media_import_destination(
            self._settings,
            year=values.year,
            project=values.project,
            day=values.day,
        )))

    def _confirm(self) -> None:
        try:
            self._result = self._values()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Legacy Destination",
                str(exc),
                parent=self._dialog.window,
            )
            return
        self._dialog.close()

    def _cancel(self) -> None:
        self._result = None
        self._dialog.close()

    def wait(self) -> LegacyImportDestination | None:
        self._dialog.show()
        self._dialog.window.wait_window()
        return self._result


def choose_legacy_import_destination(
    parent: tk.Misc,
    settings: Settings,
) -> LegacyImportDestination | None:
    return LegacyImportResumeDialog(parent, settings).wait()
