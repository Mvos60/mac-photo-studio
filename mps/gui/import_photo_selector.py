from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mps.gui.dialogs import BODY_FONT, MpsDialog
from mps.models.import_photo_selection import (
    ImportPhotoCandidate,
    ImportPhotoSelectionResponse,
)


class ImportPhotoSelector:
    """Modal native selector showing one row per photographic capture."""

    def __init__(
        self,
        parent: tk.Misc,
        candidates: tuple[ImportPhotoCandidate, ...],
    ) -> None:
        self._candidates = candidates
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

    def _build_table(self) -> None:
        container = ttk.Frame(self._dialog.content)
        container.grid(row=0, column=0, sticky="nsew")
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
) -> ImportPhotoSelectionResponse | None:
    return ImportPhotoSelector(parent, candidates).wait()
