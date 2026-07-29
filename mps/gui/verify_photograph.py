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


def run_verification(photo: Path) -> tuple[int, str]:
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "mps.main",
            "verify-photo",
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


def verification_state(
    returncode: int,
    output: str,
) -> tuple[str, str]:
    normalized = output.upper()

    if returncode == 0 and any(
        marker in normalized
        for marker in (
            "VERIFIED",
            "TRUSTED",
            "VALID",
            "PASS",
        )
    ):
        return (
            "TRUSTED",
            (
                "MPS recognises this photograph and its "
                "recorded identity still matches."
            ),
        )

    if any(
        marker in normalized
        for marker in (
            "HASH MISMATCH",
            "SHA-256 DOES NOT MATCH",
            "DOES NOT MATCH RECORDED IDENTITY",
            "MODIFIED",
            "CHANGED",
            "INVALID",
            "FAILED",
        )
    ):
        return (
            "CHANGED OR INVALID",
            (
                "The current file does not fully match the "
                "identity recorded by MPS."
            ),
        )

    if any(
        marker in normalized
        for marker in (
            "NOT FOUND",
            "UNKNOWN",
            "NOT MANAGED",
            "NO CERTIFICATE",
            "NOT INSIDE A MANAGED PROVENANCE IMPORT",
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

    if returncode == 0:
        return (
            "VERIFICATION COMPLETED",
            (
                "MPS completed the technical verification. "
                "Review the details below."
            ),
        )

    return (
        "VERIFICATION UNAVAILABLE",
        (
            "MPS could not complete the verification. "
            "Review the details below."
        ),
    )


class VerifyPhotographDialog:
    def __init__(
        self,
        parent: tk.Misc,
        photo: Path,
    ) -> None:
        self._choose_another = False

        self._dialog = MpsDialog(
            parent,
            title="Verify Photograph",
            size="medium",
        )
        self._window = self._dialog.window

        self._window.geometry("1180x940")
        self._window.minsize(980, 800)

        self._dialog.add_header(
            "Verify Photograph",
            (
                "This checks the photograph's technical MPS "
                "identity and provenance records. It does not "
                "judge image quality, sharpness or editing style."
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

        returncode, output = run_verification(photo)
        state, explanation = verification_state(
            returncode,
            output,
        )

        status_box = self._dialog.create_section(
            content,
            title="MPS Status",
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

        details_box = self._dialog.create_section(
            content,
            title="Raw Verification Details",
            padding=(10, 10),
        )
        details_box.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        details_box.rowconfigure(0, weight=1)

        text = tk.Text(
            details_box,
            wrap="word",
            height=16,
            padx=10,
            pady=8,
        )
        scrollbar = ttk.Scrollbar(
            details_box,
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
            output or "No technical details were returned.",
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


def show_verify_photograph(
    parent: tk.Misc,
    photo: Path,
) -> bool:
    try:
        dialog = VerifyPhotographDialog(
            parent,
            photo,
        )
        return dialog.choose_another
    except OSError as exc:
        messagebox.showerror(
            "Verification unavailable",
            (
                "MPS could not start the photograph "
                f"verification.\n\n{exc}"
            ),
            parent=parent,
        )
        return False
