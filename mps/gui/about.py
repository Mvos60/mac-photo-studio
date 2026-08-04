from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mps.gui.branding import load_camera_image
from mps.gui.dialogs import BODY_FONT, BODY_ITALIC_FONT, TITLE_FONT, MpsDialog
from mps.version import get_version


class AboutDialog:
    def __init__(self, parent: tk.Misc) -> None:
        self._dialog = MpsDialog(
            parent,
            title="About Mac Photo Studio",
            size="small",
            resizable=False,
        )
        self._dialog.window.geometry("660x540")
        self._dialog.window.minsize(620, 500)
        self._camera_image = load_camera_image(self._dialog.window, 144)
        self._dialog.window._mps_about_camera_image = self._camera_image

        content = self._dialog.content
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=0, minsize=154)
        self._camera_label = ttk.Label(
            content,
            image=self._camera_image,
        )
        self._camera_label.image = self._camera_image
        self._camera_label.grid(
            row=0, column=0, sticky="n", pady=(4, 10)
        )
        ttk.Label(content, text="Mac Photo Studio", font=TITLE_FONT).grid(
            row=1, column=0
        )
        ttk.Label(
            content,
            text=f"Version {get_version()}",
            font=BODY_FONT,
        ).grid(row=2, column=0, pady=(4, 8))
        ttk.Label(
            content,
            text="Real Photography. Proven.",
            font=BODY_ITALIC_FONT,
        ).grid(row=3, column=0, pady=(0, 10))
        ttk.Label(
            content,
            text=(
                "A provenance-aware photographer workflow for verified "
                "imports, safe culling and traceable photographic history."
                "\n\nObserve first. Decide second. Act last. "
                "Verify before trust."
            ),
            font=BODY_FONT,
            justify="center",
            wraplength=520,
        ).grid(row=4, column=0)
        self._dialog.add_close_button()

    def show(self) -> None:
        self._dialog.show()
        self._dialog.window.wait_window()


def show_about(parent: tk.Misc) -> None:
    AboutDialog(parent).show()
