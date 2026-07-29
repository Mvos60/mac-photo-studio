from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from mps.gui.dialogs import (
    BODY_ITALIC_FONT,
    MpsDialog,
)


def run_photo_history(photo: Path) -> tuple[int, str]:
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "mps.main",
            "photo-history",
            str(photo),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = "\n".join(
        part.strip()
        for part in (
            process.stdout,
            process.stderr,
        )
        if part.strip()
    )
    return process.returncode, output


def history_state(
    returncode: int,
    output: str,
) -> tuple[str, str]:
    normalized = output.upper()

    if any(
        marker in normalized
        for marker in (
            "NOT INSIDE A MANAGED PROVENANCE IMPORT",
            "NOT MANAGED",
            "NO CERTIFICATE",
        )
    ):
        return (
            "NOT MANAGED BY MPS",
            (
                "This photograph was found, but MPS could not link "
                "it to a verified MPS import. This does not mean "
                "that the photograph was altered or is AI-generated."
            ),
        )

    if any(
        marker in normalized
        for marker in (
            "HASH MISMATCH",
            "SHA-256 DOES NOT MATCH",
            "DOES NOT MATCH RECORDED IDENTITY",
            "HASH CONTINUITY MISMATCH",
            "INVALID",
        )
    ):
        return (
            "CHANGED OR INVALID HISTORY",
            (
                "MPS found provenance information, but the current "
                "file or its recorded event chain does not fully match."
            ),
        )

    if returncode == 0 and (
        "STATUS:        TRUSTED" in normalized
        or "STATUS: TRUSTED" in normalized
    ):
        return (
            "TRUSTED HISTORY",
            (
                "MPS found a valid recorded history for this "
                "photograph. The entries below show the events "
                "that MPS has recorded."
            ),
        )

    if returncode == 0:
        return (
            "HISTORY AVAILABLE",
            (
                "MPS found recorded history information. "
                "Review the entries below."
            ),
        )

    return (
        "HISTORY UNAVAILABLE",
        (
            "MPS could not display a complete recorded history. "
            "Review the details below."
        ),
    )


class PhotoHistoryDialog:
    def __init__(
        self,
        parent: tk.Misc,
        photo: Path,
    ) -> None:
        self._choose_another = False

        self._dialog = MpsDialog(
            parent,
            title="Photo History",
            size="medium",
        )
        self._window = self._dialog.window

        self._window.geometry("1180x940")
        self._window.minsize(980, 800)

        self._dialog.add_header(
            "Photo History",
            (
                "This shows the provenance events that MPS has "
                "recorded for the selected photograph. It does not "
                "change the photograph or its history."
            ),
            wraplength=760,
        )

        ttk.Label(
            self._dialog.header,
            text=str(photo),
            font=BODY_ITALIC_FONT,
            justify="left",
            wraplength=760,
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        content = self._dialog.content
        content.rowconfigure(1, weight=1)

        returncode, output = run_photo_history(photo)
        state, explanation = history_state(
            returncode,
            output,
        )

        status_box = self._dialog.create_section(
            content,
            title="History status",
            padding=(14, 12),
        )
        status_box.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )

        ttk.Label(
            status_box,
            text=state,
            font=("Sans", 14, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            status_box,
            text=explanation,
            justify="left",
            wraplength=720,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        history_box = self._dialog.create_section(
            content,
            title="Recorded provenance history",
            padding=(10, 10),
        )
        history_box.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        history_box.rowconfigure(0, weight=1)

        text = tk.Text(
            history_box,
            wrap="word",
            height=16,
            padx=10,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(
            history_box,
            orient="vertical",
            command=text.yview,
        )
        text.configure(
            yscrollcommand=scrollbar.set,
        )

        text.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        text.insert(
            "1.0",
            output or "No recorded history details were returned.",
        )
        text.configure(state="disabled")

        self._dialog.add_footer_button(
            text="Choose another photograph",
            command=self._choose_another_photo,
            column=0,
        )
        self._dialog.add_close_button()
        self._dialog.show()
        self._window.update_idletasks()
        self._window.lift()
        self._window.focus_force()
        self._window.wait_window()

    @property
    def choose_another(self) -> bool:
        return self._choose_another

    def _choose_another_photo(self) -> None:
        self._choose_another = True
        self._dialog.close()


def show_photo_history(
    parent: tk.Misc,
    photo: Path,
) -> bool:
    try:
        dialog = PhotoHistoryDialog(
            parent,
            photo,
        )
        return dialog.choose_another
    except OSError as exc:
        messagebox.showerror(
            "Photo History unavailable",
            (
                "MPS could not open the photograph history.\n\n"
                f"{exc}"
            ),
            parent=parent,
        )
        return False
