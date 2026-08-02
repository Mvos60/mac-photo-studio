from __future__ import annotations

from typing import Literal
import tkinter as tk
from tkinter import ttk

from mps.gui.dialogs import BODY_FONT, MpsDialog


ImportSessionAction = Literal["resume", "start-new", "cancel"]


class ImportSessionActionSelector:
    def __init__(self, parent: tk.Misc) -> None:
        self._result: ImportSessionAction | None = None
        self._dialog = MpsDialog(
            parent,
            title="Active Import Session",
            size="small",
            resizable=False,
        )
        self._dialog.add_header(
            "An active import session is available",
            (
                "Resume it, start a new photo session, "
                "or leave it unchanged."
            ),
        )

        ttk.Label(
            self._dialog.content,
            text=(
                "Resume continues the saved session.\n"
                "Start new lets you choose a new calendar-first "
                "destination.\n"
                "Cancel changes nothing."
            ),
            font=BODY_FONT,
            justify="left",
        ).grid(row=0, column=0, sticky="nw")

        self._dialog.add_footer_button(
            text="Cancel",
            command=self._cancel,
            column=1,
        )
        self._dialog.add_footer_button(
            text="Start new",
            command=lambda: self._choose("start-new"),
            column=2,
        )
        self._dialog.add_footer_button(
            text="Resume",
            command=lambda: self._choose("resume"),
            column=3,
            padx=(0, 0),
        )
        self._dialog.window.protocol(
            "WM_DELETE_WINDOW",
            self._cancel,
        )
        self._dialog.window.bind(
            "<Escape>",
            lambda _event: self._cancel(),
        )

    @property
    def result(self) -> ImportSessionAction | None:
        return self._result

    def _choose(self, action: ImportSessionAction) -> None:
        self._result = action
        self._dialog.close()

    def _cancel(self) -> None:
        self._result = "cancel"
        self._dialog.close()

    def wait(self) -> ImportSessionAction | None:
        self._dialog.show()
        self._dialog.window.wait_window()
        return self._result


def choose_import_session_action(
    parent: tk.Misc,
) -> ImportSessionAction | None:
    return ImportSessionActionSelector(parent).wait()
