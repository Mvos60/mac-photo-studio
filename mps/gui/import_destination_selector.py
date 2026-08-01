from __future__ import annotations

from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from mps.gui.dialogs import BODY_FONT, MpsDialog
from mps.models.import_destination_selection import ImportDestinationSelection


class ImportDestinationSelector:
    def __init__(self, parent: tk.Misc, photos_root: str | Path) -> None:
        today = date.today()

        self._photos_root = Path(photos_root).expanduser()
        self._result: ImportDestinationSelection | None = None
        self._dialog = MpsDialog(
            parent,
            title="Choose Import Destination",
            size="wide",
            resizable=False,
        )
        self._dialog.add_header(
            "Choose Import Destination",
            "Choose one destination for all cards in this photo session.",
        )

        window = self._dialog.window
        self._year_var = tk.StringVar(master=window, value=str(today.year))
        self._month_day_var = tk.StringVar(
            master=window,
            value=today.strftime("%m-%d"),
        )
        self._project_var = tk.StringVar(master=window)
        self._description_var = tk.StringVar(master=window)
        self._destination_var = tk.StringVar(master=window)

        self._build_fields()

        for variable in (
            self._year_var,
            self._month_day_var,
            self._project_var,
            self._description_var,
        ):
            variable.trace_add("write", self._update_preview)

        self._update_preview()

        self._dialog.add_footer_button(
            text="Cancel",
            command=self._cancel,
            column=1,
        )
        self._dialog.add_footer_button(
            text="Continue to Import",
            command=self._confirm,
            column=2,
            padx=(0, 0),
        )
        window.protocol("WM_DELETE_WINDOW", self._cancel)
        window.bind("<Escape>", lambda _event: self._cancel())

    @property
    def result(self) -> ImportDestinationSelection | None:
        return self._result

    def _build_fields(self) -> None:
        form = ttk.Frame(self._dialog.content)
        form.grid(row=0, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        fields = (
            ("Year", self._year_var),
            ("Date (MM-DD)", self._month_day_var),
            ("Project", self._project_var),
            (
                "Description / session name (optional)",
                self._description_var,
            ),
        )

        for row, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label, font=BODY_FONT).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 14),
                pady=8,
            )
            ttk.Entry(form, textvariable=variable, font=BODY_FONT).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=8,
            )

        ttk.Label(form, text="Destination", font=BODY_FONT).grid(
            row=len(fields),
            column=0,
            sticky="nw",
            padx=(0, 14),
            pady=8,
        )
        ttk.Entry(
            form,
            textvariable=self._destination_var,
            font=BODY_FONT,
            state="readonly",
        ).grid(
            row=len(fields),
            column=1,
            sticky="ew",
            pady=8,
        )

    def _selection_from_fields(self) -> ImportDestinationSelection:
        try:
            year = int(self._year_var.get())
        except ValueError as exc:
            raise ValueError("Year must be a four-digit integer") from exc

        return ImportDestinationSelection(
            year=year,
            month_day=self._month_day_var.get(),
            project=self._project_var.get(),
            description=self._description_var.get(),
        )

    def _update_preview(self, *_args: object) -> None:
        try:
            selection = self._selection_from_fields()
        except ValueError:
            preview = "Complete the fields to preview the destination."
        else:
            preview = str(selection.destination_path(self._photos_root))

        self._destination_var.set(preview)

    def _confirm(self) -> None:
        try:
            selection = self._selection_from_fields()
        except ValueError as exc:
            messagebox.showerror(
                "Invalid Import Destination",
                str(exc),
                parent=self._dialog.window,
            )
            return

        self._result = selection
        self._dialog.close()

    def _cancel(self) -> None:
        self._result = None
        self._dialog.close()

    def wait(self) -> ImportDestinationSelection | None:
        self._dialog.show()
        self._dialog.window.wait_window()
        return self._result


def choose_import_destination(
    parent: tk.Misc,
    photos_root: str | Path,
) -> ImportDestinationSelection | None:
    return ImportDestinationSelector(parent, photos_root).wait()
