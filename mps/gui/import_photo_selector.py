from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from mps.gui.dialogs import BODY_FONT, MpsDialog
from mps.models.import_photo_selection import (
    ImportPhotoCandidate,
    ImportPhotoSelectionResponse,
    summarize_import_photo_selection,
)


class ImportPhotoSelector:
    """Modal native selector showing one row per photographic capture."""

    def __init__(
        self,
        parent: tk.Misc,
        candidates: tuple[ImportPhotoCandidate, ...],
        *,
        session_date: date | None = None,
    ) -> None:
        self._candidates = candidates
        self._session_date = session_date
        self._result: ImportPhotoSelectionResponse | None = None
        self._dialog = MpsDialog(
            parent,
            title="Select Photographs",
            size="wide",
        )
        self._dialog.add_header(
            "Select Photographs",
            "Choose the photographic captures to import from the current media.",
        )
        self._window = self._dialog.window
        self._variables = {
            candidate.key: tk.BooleanVar(master=self._window, value=True)
            for candidate in candidates
        }
        for variable in self._variables.values():
            variable.trace_add("write", self._selection_changed)
        self._build_summary()
        self._build_table()
        footer = self._dialog.footer
        for column in range(1, 5):
            footer.columnconfigure(column, weight=0)
        self._dialog.add_footer_button(
            text="Select All", command=self.select_all, column=1
        )
        self._dialog.add_footer_button(
            text="Select None", command=self.select_none, column=2
        )
        self._dialog.add_footer_button(
            text="Cancel", command=self.cancel, column=3
        )
        self._dialog.add_footer_button(
            text="Import Selection",
            command=self.confirm,
            column=4,
            padx=(0, 0),
        )
        self._window.protocol("WM_DELETE_WINDOW", self.cancel)

    def _build_summary(self) -> None:
        self._dialog.content.rowconfigure(0, weight=0)
        self._dialog.content.rowconfigure(1, weight=1)
        container = ttk.Frame(self._dialog.content)
        container.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        container.columnconfigure(1, weight=1)
        self._summary_variables = {
            "selection": tk.StringVar(master=self._window),
            "exif_label": tk.StringVar(master=self._window),
            "session": tk.StringVar(master=self._window),
            "range": tk.StringVar(master=self._window),
            "status": tk.StringVar(master=self._window),
        }
        rows = (
            ("Selectie:", "selection"),
            ("Sessiedatum:", "session"),
            (None, "range"),
            ("Status:", "status"),
        )
        for row, (label, key) in enumerate(rows):
            label_options = (
                {"textvariable": self._summary_variables["exif_label"]}
                if label is None else {"text": label}
            )
            ttk.Label(container, font=BODY_FONT, **label_options).grid(
                row=row, column=0, sticky="nw", padx=(0, 12), pady=2
            )
            ttk.Label(
                container, textvariable=self._summary_variables[key],
                font=BODY_FONT, justify="left",
            ).grid(row=row, column=1, sticky="w", pady=2)
        self._refresh_summary()

    def _build_table(self) -> None:
        container = ttk.Frame(self._dialog.content)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        headings = ("Photograph", "Type", "Captured", "Camera")
        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        for column, heading in enumerate(headings):
            header.columnconfigure(column, weight=1 if column in {0, 2, 3} else 0)
            ttk.Label(header, text=heading, font=BODY_FONT).grid(
                row=0, column=column, sticky="w", padx=(0, 16)
            )

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        rows = ttk.Frame(canvas)
        rows.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=rows, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        for column in range(4):
            rows.columnconfigure(column, weight=1 if column in {0, 2, 3} else 0)
        for row, candidate in enumerate(self._candidates):
            ttk.Checkbutton(
                rows,
                text=candidate.stem,
                variable=self._variables[candidate.key],
            ).grid(row=row, column=0, sticky="w", padx=(0, 16), pady=4)
            values = (
                candidate.media_type,
                candidate.display_captured_at,
                candidate.display_camera_model,
            )
            for column, value in enumerate(values, start=1):
                ttk.Label(rows, text=value, font=BODY_FONT).grid(
                    row=row,
                    column=column,
                    sticky="w",
                    padx=(0, 16),
                    pady=4,
                )

    def select_all(self) -> None:
        for variable in self._variables.values():
            variable.set(True)

    def select_none(self) -> None:
        for variable in self._variables.values():
            variable.set(False)

    def _selection_changed(self, *_args: object) -> None:
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        if not hasattr(self, "_summary_variables"):
            return
        summary = summarize_import_photo_selection(
            self._candidates,
            (key for key, variable in self._variables.items() if variable.get()),
            self._session_date,
        )
        self._summary_variables["selection"].set(
            f"{summary.selected_count} van {len(self._candidates)} opnamen"
        )
        self._summary_variables["exif_label"].set(
            "EXIF-opname:" if summary.selected_count == 1 else "EXIF-selectie:"
        )
        self._summary_variables["session"].set(
            self._session_date.strftime("%d-%m-%Y")
            if self._session_date is not None else "—"
        )
        if summary.earliest is None or summary.latest is None:
            exif_text = "—"
        elif summary.selected_count == 1:
            exif_text = f"{summary.earliest:%d-%m-%Y %H:%M}"
        else:
            exif_text = (
                f"{summary.earliest:%d-%m-%Y %H:%M} → "
                f"{summary.latest:%d-%m-%Y %H:%M}"
            )
        self._summary_variables["range"].set(exif_text)
        statuses = []
        if len(summary.unique_dates) > 1:
            statuses.append(
                f"⚠ De {summary.selected_count} geselecteerde opnamen vallen "
                f"op {len(summary.unique_dates)} kalenderdagen."
            )
        if summary.mismatch_count:
            verb = "wijkt" if summary.mismatch_count == 1 else "wijken"
            statuses.append(
                f"⚠ {summary.mismatch_count} van de {summary.selected_count} "
                f"geselecteerde opnamen {verb} af van de sessiedatum."
            )
        if summary.unknown_count:
            verb = "heeft" if summary.unknown_count == 1 else "hebben"
            statuses.append(
                f"⚠ {summary.unknown_count} van de {summary.selected_count} "
                f"geselecteerde opnamen {verb} geen leesbare opnamedatum."
            )
        if summary.conflict_count:
            verb = "heeft" if summary.conflict_count == 1 else "hebben"
            statuses.append(
                f"⚠ {summary.conflict_count} van de {summary.selected_count} "
                f"geselecteerde opnamen {verb} tegenstrijdige RAW/JPG-opnamedatums."
            )
        if not summary.selected_count:
            statuses.append("Geen opnamen geselecteerd.")
        elif (not statuses and summary.earliest is not None
              and self._session_date is not None):
            if summary.selected_count == 1:
                statuses.append(
                    "✓ De geselecteerde opname komt overeen met de sessiedatum."
                )
            else:
                statuses.append(
                    "✓ Alle geselecteerde opnamen met een leesbare EXIF-datum "
                    "komen overeen met de sessiedatum."
                )
        self._summary_variables["status"].set("\n".join(statuses) or "—")

    def confirm(self) -> None:
        selected = frozenset(
            key for key, variable in self._variables.items() if variable.get()
        )
        if not selected:
            messagebox.showwarning(
                "No Photographs Selected",
                "Select at least one photograph to import.",
                parent=self._window,
            )
            return
        self._result = ImportPhotoSelectionResponse(selected)
        self._dialog.close()

    def cancel(self) -> None:
        self._result = None
        self._dialog.close()

    def wait(self) -> ImportPhotoSelectionResponse | None:
        self._dialog.show()
        self._window.wait_window()
        return self._result


def choose_import_photos(
    parent: tk.Misc,
    candidates: tuple[ImportPhotoCandidate, ...],
    *,
    session_date: date | None = None,
) -> ImportPhotoSelectionResponse | None:
    return ImportPhotoSelector(
        parent, candidates, session_date=session_date,
    ).wait()
