from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from mps.config import load_settings
from mps.constants import ACTIVE_IMPORT_SESSION
from mps.gui.culling_review import show_culling_review
from mps.gui.quarantine_manager import show_quarantine_manager
from mps.gui.verify_photograph import show_verify_photograph
from mps.gui.photo_history import (
    show_photo_history as show_photo_history_dialog,
)
from mps.gui.session_picker import (
    choose_import_session as choose_import_session_dialog,
)
from mps.gui.photo_picker import choose_photo as choose_photo_dialog
from mps.paths import get_photo_library
from mps.services.app_resolver import resolve_application
from mps.version import get_version


TerminalResolver = Callable[[str], str | None]


def build_cli_command(arguments: list[str]) -> str:
    return shlex.join(
        [
            "mac-photo-studio",
            *arguments,
        ]
    )


def resolve_terminal_command(
    cli_command: str,
    resolver: TerminalResolver = shutil.which,
) -> list[str] | None:
    shell_command = (
        f"{cli_command}; "
        'echo; read -rp "Press Enter to close..."'
    )

    candidates = [
        (
            "gnome-terminal",
            [
                "gnome-terminal",
                "--",
                "bash",
                "-lc",
                shell_command,
            ],
        ),
        (
            "kgx",
            [
                "kgx",
                "--",
                "bash",
                "-lc",
                shell_command,
            ],
        ),
        (
            "x-terminal-emulator",
            [
                "x-terminal-emulator",
                "-e",
                "bash",
                "-lc",
                shell_command,
            ],
        ),
        (
            "konsole",
            [
                "konsole",
                "-e",
                "bash",
                "-lc",
                shell_command,
            ],
        ),
        (
            "xfce4-terminal",
            [
                "xfce4-terminal",
                "--command",
                "bash -lc " + shlex.quote(shell_command),
            ],
        ),
    ]

    for executable, command in candidates:
        if resolver(executable):
            return command

    return None


def launch_cli(arguments: list[str]) -> None:
    cli_command = build_cli_command(arguments)
    terminal_command = resolve_terminal_command(
        cli_command
    )

    if terminal_command is None:
        messagebox.showerror(
            "Terminal Unavailable",
            (
                "No supported terminal application was found.\n\n"
                "Run this command manually:\n\n"
                f"{cli_command}"
            ),
        )
        return

    try:
        subprocess.Popen(
            terminal_command,
            start_new_session=True,
        )
    except OSError as exc:
        messagebox.showerror(
            "Could Not Start Command",
            (
                "The terminal could not be opened.\n\n"
                f"{exc}\n\n"
                f"Command:\n{cli_command}"
            ),
        )


def open_path(path: Path) -> None:
    expanded = path.expanduser()

    if not expanded.exists():
        messagebox.showinfo(
            "Location Unavailable",
            f"This location does not exist yet:\n\n{expanded}",
        )
        return

    opener = shutil.which("xdg-open")

    if opener is None:
        messagebox.showerror(
            "File Manager Unavailable",
            (
                "The desktop file manager could not be started.\n\n"
                f"Location:\n{expanded}"
            ),
        )
        return

    try:
        subprocess.Popen(
            [opener, str(expanded)],
            start_new_session=True,
        )
    except OSError as exc:
        messagebox.showerror(
            "Could Not Open Location",
            f"{exc}\n\nLocation:\n{expanded}",
        )


def choose_import_session(
    parent: tk.Misc,
    title: str,
) -> Path | None:
    return choose_import_session_dialog(
        parent=parent,
        photo_library=get_photo_library(),
        title=title,
    )



def choose_photo(
    parent: tk.Misc,
    title: str,
    description: str,
) -> Path | None:
    return choose_photo_dialog(
        parent=parent,
        photo_library=get_photo_library(),
        title=title,
        description=description,
    )



def build_status_items() -> list[tuple[str, str]]:
    archive = get_photo_library()
    active_session = ACTIVE_IMPORT_SESSION

    settings = load_settings()

    digikam_available = resolve_application(
        settings,
        "digikam",
        "digikam",
    ).found

    darktable_available = resolve_application(
        settings,
        "darktable",
        "darktable",
    ).found

    items: list[tuple[str, str]] = []

    if archive.is_dir():
        items.append(
            (
                "green",
                f"Photo archive found:\n{archive}",
            )
        )
    else:
        items.append(
            (
                "red",
                f"Photo archive not found:\n{archive}",
            )
        )

    if active_session.exists():
        items.append(
            (
                "amber",
                "An interrupted import session is available",
            )
        )
    else:
        items.append(
            (
                "green",
                "No interrupted import session",
            )
        )

    items.append(
        (
            "green" if digikam_available else "amber",
            (
                "digiKam detected"
                if digikam_available
                else "digiKam not detected automatically"
            ),
        )
    )

    items.append(
        (
            "green" if darktable_available else "amber",
            (
                "darktable detected"
                if darktable_available
                else "darktable not detected automatically"
            ),
        )
    )

    return items


def run_gui() -> None:
    root = tk.Tk()
    root.title("Mac Photo Studio")
    root.geometry("1040x880")
    root.minsize(980, 840)

    style = ttk.Style(root)

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    title_font = ("Sans", 24, "bold")
    subtitle_font = ("Sans", 13)
    version_font = ("Sans", 11)
    section_font = ("Sans", 13, "bold")
    ready_font = ("Sans", 16, "bold")
    primary_button_font = ("Sans", 14, "bold")
    button_font = ("Sans", 12)
    status_font = ("Sans", 12)
    body_font = ("Sans", 11)
    footer_font = ("Sans", 11, "italic")

    style.configure(
        "MPS.Primary.TButton",
        font=primary_button_font,
        padding=(18, 14),
    )

    style.configure(
        "MPS.TButton",
        font=button_font,
        padding=(14, 6),
    )

    style.configure(
        "MPS.TLabelframe",
        padding=18,
    )

    style.configure(
        "MPS.TLabelframe.Label",
        font=section_font,
    )

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)

    header = ttk.Frame(
        root,
        padding=(30, 20, 30, 14),
    )
    header.grid(
        row=0,
        column=0,
        sticky="ew",
    )
    header.columnconfigure(0, weight=1)

    ttk.Label(
        header,
        text="📷  Mac Photo Studio",
        font=title_font,
    ).grid(
        row=0,
        column=0,
        sticky="w",
    )

    ttk.Label(
        header,
        text="Photography Workflow Manager",
        font=subtitle_font,
    ).grid(
        row=1,
        column=0,
        sticky="w",
        pady=(4, 0),
    )

    ttk.Label(
        header,
        text=f"Version {get_version()}",
        font=version_font,
    ).grid(
        row=0,
        column=1,
        rowspan=2,
        sticky="e",
        padx=(20, 0),
    )

    content = ttk.Frame(
        root,
        padding=(30, 0, 30, 14),
    )
    content.grid(
        row=1,
        column=0,
        sticky="nsew",
    )

    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=0, minsize=292)
    content.rowconfigure(1, weight=1, minsize=258)

    status = ttk.LabelFrame(
        content,
        text="System Status",
        style="MPS.TLabelframe",
    )
    status.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0, 8),
        pady=(0, 8),
    )
    status.columnconfigure(1, weight=1)

    status_items = build_status_items()

    overall_ready = all(
        level == "green"
        for level, _ in status_items
    )

    overall_level = (
        "green"
        if overall_ready
        else "amber"
    )

    indicator_colours = {
        "green": "#2e7d32",
        "amber": "#b26a00",
        "red": "#b3261e",
    }

    tk.Label(
        status,
        text="●",
        font=("Sans", 18, "bold"),
        foreground=indicator_colours[overall_level],
    ).grid(
        row=0,
        column=0,
        sticky="n",
        padx=(0, 12),
        pady=(2, 10),
    )

    ttk.Label(
        status,
        text=(
            "READY FOR IMPORT"
            if overall_ready
            else "ATTENTION RECOMMENDED"
        ),
        font=ready_font,
        anchor="w",
    ).grid(
        row=0,
        column=1,
        sticky="ew",
        pady=(2, 10),
    )

    for row, (level, message) in enumerate(
        status_items,
        start=1,
    ):
        tk.Label(
            status,
            text="●",
            font=("Sans", 13, "bold"),
            foreground=indicator_colours[level],
        ).grid(
            row=row,
            column=0,
            sticky="n",
            padx=(0, 12),
            pady=4,
        )

        ttk.Label(
            status,
            text=message,
            font=status_font,
            anchor="w",
            justify="left",
            wraplength=430,
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            pady=4,
        )

    ttk.Label(
        status,
        text=(
            "Everything looks ready."
            if overall_ready
            else "Review the amber or red items before importing."
        ),
        font=body_font,
        justify="left",
        anchor="w",
    ).grid(
        row=len(status_items) + 1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(10, 2),
    )

    import_frame = ttk.LabelFrame(
        content,
        text="Import",
        style="MPS.TLabelframe",
    )
    import_frame.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=(8, 0),
        pady=(0, 8),
    )
    import_frame.columnconfigure(0, weight=1)
    import_frame.rowconfigure(0, weight=1)
    import_frame.rowconfigure(2, weight=1)

    ttk.Button(
        import_frame,
        text="📥  Import Photographs",
        command=lambda: launch_cli(["import"]),
        style="MPS.Primary.TButton",
    ).grid(
        row=1,
        column=0,
        sticky="ew",
        padx=18,
    )

    tools = ttk.LabelFrame(
        content,
        text="Photographer Tools",
        style="MPS.TLabelframe",
    )
    tools.grid(
        row=1,
        column=0,
        sticky="nsew",
        padx=(0, 8),
        pady=(8, 0),
    )
    tools.columnconfigure(0, weight=1)

    def analyze_culling() -> None:
        session = choose_import_session(
            root,
            "Select an import session to analyze",
        )

        if session is not None:
            show_culling_review(
                root,
                session,
            )

    def verify_photo() -> None:
        while True:
            photo = choose_photo(
                root,
                "Select a photograph to verify",
                (
                    "Select the photograph you want MPS to verify. "
                    "MPS will compare the file with its recorded identity "
                    "and provenance information."
                ),
            )

            if photo is None:
                return

            choose_another = show_verify_photograph(
                root,
                photo,
            )

            if not choose_another:
                return

    def show_photo_history() -> None:
        while True:
            photo = choose_photo(
                root,
                "Select a photograph for Photo History",
                (
                    "Select the photograph whose MPS provenance history "
                    "you want to view."
                ),
            )

            if photo is None:
                return

            choose_another = show_photo_history_dialog(
                root,
                photo,
            )

            if not choose_another:
                return

    ttk.Button(
        tools,
        text="🔍  Analyze Culling",
        command=analyze_culling,
        style="MPS.TButton",
    ).grid(
        row=0,
        column=0,
        sticky="ew",
        pady=(0, 5),
    )

    ttk.Button(
        tools,
        text="🗄️  Quarantine Manager",
        command=lambda: show_quarantine_manager(root),
        style="MPS.TButton",
    ).grid(
        row=1,
        column=0,
        sticky="ew",
        pady=5,
    )

    ttk.Button(
        tools,
        text="✓  Verify Photograph",
        command=verify_photo,
        style="MPS.TButton",
    ).grid(
        row=2,
        column=0,
        sticky="ew",
        pady=5,
    )

    ttk.Button(
        tools,
        text="📜  Show Photo History",
        command=show_photo_history,
        style="MPS.TButton",
    ).grid(
        row=3,
        column=0,
        sticky="ew",
        pady=(5, 0),
    )

    utility_tools = ttk.LabelFrame(
        content,
        text="Application Tools",
        style="MPS.TLabelframe",
    )
    utility_tools.grid(
        row=1,
        column=1,
        sticky="nsew",
        padx=(8, 0),
        pady=(8, 0),
    )
    utility_tools.columnconfigure(0, weight=1)
    utility_tools.columnconfigure(1, weight=1)
    utility_tools.columnconfigure(2, weight=1)

    ttk.Button(
        utility_tools,
        text="⚙  Settings",
        command=lambda: launch_cli(["--show-config"]),
        style="MPS.TButton",
    ).grid(
        row=0,
        column=0,
        sticky="ew",
        padx=(0, 5),
    )

    ttk.Button(
        utility_tools,
        text="📄  Logs",
        command=lambda: open_path(
            Path.home()
            / ".local"
            / "state"
            / "mac-photo-studio"
            / "logs"
        ),
        style="MPS.TButton",
    ).grid(
        row=0,
        column=1,
        sticky="ew",
        padx=5,
    )

    def show_about() -> None:
        messagebox.showinfo(
            "About Mac Photo Studio",
            (
                f"Mac Photo Studio {get_version()}\n\n"
                "A provenance-aware photographer workflow "
                "for verified imports, safe culling and "
                "traceable photographic history.\n\n"
                "Observe first. Decide second. Act last. "
                "Verify before trust."
            ),
        )

    ttk.Button(
        utility_tools,
        text="ℹ  About",
        command=show_about,
        style="MPS.TButton",
    ).grid(
        row=0,
        column=2,
        sticky="ew",
        padx=(5, 0),
    )

    footer = ttk.Frame(
        root,
        padding=(30, 4, 30, 20),
    )
    footer.grid(
        row=2,
        column=0,
        sticky="ew",
    )
    footer.columnconfigure(0, weight=1)

    ttk.Label(
        footer,
        text="Trust through verification.",
        font=footer_font,
    ).grid(
        row=0,
        column=0,
        sticky="w",
    )

    ttk.Button(
        footer,
        text="Close",
        command=root.destroy,
        style="MPS.TButton",
    ).grid(
        row=0,
        column=1,
        sticky="e",
    )

    root.mainloop()
