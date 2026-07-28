from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk


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
            "Trusted",
            (
                "MPS recognises this photograph and its "
                "recorded identity still matches."
            ),
        )

    if any(
        marker in normalized
        for marker in (
            "HASH MISMATCH",
            "MODIFIED",
            "CHANGED",
            "INVALID",
            "FAILED",
        )
    ):
        return (
            "Changed or invalid",
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
        )
    ):
        return (
            "Not managed by MPS",
            (
                "No complete MPS provenance record could be "
                "confirmed for this file."
            ),
        )

    if returncode == 0:
        return (
            "Verification completed",
            (
                "MPS completed the technical verification. "
                "Review the details below."
            ),
        )

    return (
        "Verification unavailable",
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
        self._window = tk.Toplevel(parent)
        self._window.title("Verify Photograph")
        self._window.geometry("820x620")
        self._window.minsize(660, 480)
        self._window.transient(parent)

        self._window.columnconfigure(0, weight=1)
        self._window.rowconfigure(1, weight=1)

        header = ttk.Frame(
            self._window,
            padding=(22, 18, 22, 12),
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Verify Photograph",
            font=("Sans", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text=(
                "This checks the photograph's technical MPS "
                "identity and provenance records. It does not "
                "judge image quality, sharpness or editing style."
            ),
            justify="left",
            wraplength=760,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

        ttk.Label(
            header,
            text=str(photo),
            font=("Sans", 10, "italic"),
            justify="left",
            wraplength=760,
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        content = ttk.Frame(
            self._window,
            padding=(22, 0, 22, 0),
        )
        content.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        returncode, output = run_verification(photo)
        state, explanation = verification_state(
            returncode,
            output,
        )

        status_box = ttk.LabelFrame(
            content,
            text="Verification result",
            padding=(14, 12),
        )
        status_box.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )
        status_box.columnconfigure(0, weight=1)

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

        details_box = ttk.LabelFrame(
            content,
            text="Technical details",
            padding=(10, 10),
        )
        details_box.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        details_box.columnconfigure(0, weight=1)
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

        footer = ttk.Frame(
            self._window,
            padding=(22, 14, 22, 20),
        )
        footer.grid(
            row=2,
            column=0,
            sticky="ew",
        )
        footer.columnconfigure(0, weight=1)

        ttk.Button(
            footer,
            text="Close",
            command=self._window.destroy,
        ).grid(
            row=0,
            column=1,
        )

        self._window.protocol(
            "WM_DELETE_WINDOW",
            self._window.destroy,
        )
        self._window.bind(
            "<Escape>",
            lambda _event: self._window.destroy(),
        )
        self._window.grab_set()
        self._window.focus_set()


def show_verify_photograph(
    parent: tk.Misc,
    photo: Path,
) -> None:
    try:
        VerifyPhotographDialog(
            parent,
            photo,
        )
    except OSError as exc:
        messagebox.showerror(
            "Verification unavailable",
            (
                "MPS could not start the photograph "
                f"verification.\n\n{exc}"
            ),
            parent=parent,
        )
