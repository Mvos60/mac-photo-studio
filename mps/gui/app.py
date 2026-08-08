from __future__ import annotations

from pathlib import Path
import shlex
import shutil
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk
from typing import Callable

from mps.config import load_settings
from mps.constants import ACTIVE_IMPORT_SESSION
from mps.gui.about import show_about
from mps.gui.branding import apply_window_icon, load_camera_image
from mps.gui.culling_review import show_culling_review
from mps.gui.import_destination_selector import (
    choose_import_destination,
)
from mps.gui.import_interaction_adapter import GuiImportInteractionAdapter
from mps.gui.import_window import ImportWindow
from mps.gui.legacy_import_resume_dialog import (
    choose_legacy_import_destination,
)
from mps.gui.import_session_action_selector import (
    choose_import_session_action,
)
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
from mps.models.import_workflow import ImportEvent, ImportEventType
from mps.services.app_resolver import resolve_application
from mps.services.import_controller import ImportController
from mps.services.import_media_batch_planner import media_import_destination
from mps.services.import_media_resume_validator import (
    can_resume_import_media_session,
)
from mps.services.import_media_session_store import load_import_media_session
from mps.services.import_media_wizard_runner import run_import_media_session
from mps.version import get_version


TerminalResolver = Callable[[str], str | None]
SYSTEM_STATUS_HEADLINE_MARGIN = 12
_active_import_process: subprocess.Popen | None = None
_import_controller = ImportController()


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
    *,
    import_command: bool = False,
    title: str | None = None,
) -> list[str] | None:
    if import_command:
        shell_command = (
            f"{cli_command}; "
            'status=$?; '
            'if [ "$status" -ne 0 ]; then '
            'echo; '
            'echo "Import exited with status $status."; '
            'read -rp "Press Enter to close..."; '
            'fi; '
            'exit "$status"'
        )
    else:
        shell_command = (
            f"{cli_command}; "
            'echo; read -rp "Press Enter to close..."'
        )

    candidates = [
        (
            "gnome-terminal",
            [
                "gnome-terminal",
                *( ["-t", title] if title else [] ),
                "--wait",
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
                *( ["--title", title] if title else [] ),
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
                *( ["-T", title] if title else [] ),
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
                *( ["--title", title] if title else [] ),
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
                *( ["--title", title] if title else [] ),
                "--command",
                "bash -lc " + shlex.quote(shell_command),
            ],
        ),
    ]

    for executable, command in candidates:
        if resolver(executable):
            return command

    return None


def _import_terminal_title(arguments: list[str]) -> str:
    if "--active-session-action" in arguments:
        index = arguments.index("--active-session-action")
        if index + 1 < len(arguments):
            action = arguments[index + 1]
            if action == "resume":
                return "Mac Photo Studio Import — Resume"
            if action == "start-new":
                return "Mac Photo Studio Import — Start new"
    return "Mac Photo Studio Import"


def launch_cli(arguments: list[str]) -> None:
    global _active_import_process

    is_import = bool(arguments) and arguments[0] == "import"
    if is_import and _active_import_process is not None:
        if _active_import_process.poll() is None:
            messagebox.showwarning(
                "Import Already Running",
                "An import terminal is already running.",
            )
            return
        _active_import_process = None

    cli_command = build_cli_command(arguments)
    terminal_command = resolve_terminal_command(
        cli_command,
        import_command=is_import,
        title=_import_terminal_title(arguments) if is_import else None,
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
        process = subprocess.Popen(
            terminal_command,
            start_new_session=True,
        )
        if is_import:
            _active_import_process = process
    except OSError as exc:
        messagebox.showerror(
            "Could Not Start Command",
            (
                "The terminal could not be opened.\n\n"
                f"{exc}\n\n"
                f"Command:\n{cli_command}"
            ),
        )


def start_import(
    parent: tk.Misc,
    refresh_status: Callable[[], None] | None = None,
) -> None:
    if _import_controller.is_active:
        messagebox.showwarning(
            "Import Already Running",
            "A native import is already running.",
            parent=parent,
        )
        return

    settings = load_settings()
    active_action = None
    restored_session = None
    legacy_values = None

    if ACTIVE_IMPORT_SESSION.exists():
        active_action = choose_import_session_action(
            parent=parent,
        )

        if active_action in {None, "cancel"}:
            return

        if active_action == "resume":
            try:
                restored_session = load_import_media_session(
                    ACTIVE_IMPORT_SESSION
                )
            except (OSError, ValueError):
                messagebox.showerror(
                    "Import Session Unavailable",
                    "The saved import session could not be read safely.",
                    parent=parent,
                )
                return

            stored_destination = restored_session.destination
            if stored_destination is None:
                legacy_values = choose_legacy_import_destination(
                    parent=parent,
                    settings=settings,
                )
                if legacy_values is None:
                    return
                destination_selection = None
                year = legacy_values.year
                project = legacy_values.project
                day = legacy_values.day
                import_root = media_import_destination(
                    settings,
                    year=year,
                    project=project,
                    day=day,
                )
            else:
                destination_selection = stored_destination.selection
                year = destination_selection.year
                project = destination_selection.project
                day = destination_selection.day_session
                import_root = stored_destination.import_root

            if not can_resume_import_media_session(
                restored_session,
                import_root,
                settings=settings,
            ):
                messagebox.showerror(
                    "Import Session Unavailable",
                    "The saved import session cannot be resumed safely.",
                    parent=parent,
                )
                return

            _start_native_import(
                parent,
                settings=settings,
                year=year,
                project=project,
                day=day,
                destination_selection=destination_selection,
                destination=import_root,
                action="Resume",
                session=restored_session,
                protect_existing_state=False,
                refresh_status=refresh_status,
            )
            return

    selection = choose_import_destination(
        parent=parent,
        photos_root=get_photo_library(),
    )

    if selection is None:
        return

    if active_action == "start-new":
        confirmed = messagebox.askyesno(
            "Confirm Start New",
            (
                "START NEW will replace the saved session only after "
                "the first new media batch has copied and verified "
                "successfully.\n\nContinue?"
            ),
            parent=parent,
        )
        if not confirmed:
            return

    import_root = media_import_destination(
        settings,
        year=selection.year,
        project=selection.project,
        day=selection.day_session,
        destination_selection=selection,
    )
    _start_native_import(
        parent,
        settings=settings,
        year=selection.year,
        project=selection.project,
        day=selection.day_session,
        destination_selection=selection,
        destination=import_root,
        action=("Start new" if active_action == "start-new" else "New import"),
        session=None,
        protect_existing_state=(active_action == "start-new"),
        refresh_status=refresh_status,
    )


def _start_native_import(
    parent: tk.Misc,
    *,
    settings: object,
    year: int,
    project: str,
    day: str,
    destination_selection: object | None,
    destination: Path,
    action: str,
    session: object | None,
    protect_existing_state: bool,
    refresh_status: Callable[[], None] | None,
) -> None:
    window = ImportWindow(
        parent,
        _import_controller,
        destination=destination,
        action=action,
        on_terminal=refresh_status,
    )

    def runner(event_sink, cancellation) -> object:
        interaction = GuiImportInteractionAdapter(
            event_sink,
            cancellation,
        )

        def progress_callback(progress) -> None:
            event_sink(ImportEvent(
                ImportEventType.PROGRESS,
                {"progress": progress},
            ))

        return run_import_media_session(
            settings,
            year=year,
            project=project,
            day=day,
            destination_selection=destination_selection,
            session=session,
            session_state_path=ACTIVE_IMPORT_SESSION,
            protect_existing_state_until_first_verified_batch=(
                protect_existing_state
            ),
            progress_callback=progress_callback,
            event_sink=event_sink,
            interaction_adapter=interaction,
            wait_for_initial_media=True,
            enable_photo_selection=True,
        )

    _import_controller.start(runner)
    del window


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


def render_system_status(
    status: ttk.LabelFrame,
    *,
    ready_font: tuple,
    status_font: tuple,
    body_font: tuple,
) -> None:
    for child in status.winfo_children():
        child.destroy()

    status_items = build_status_items()
    overall_ready = all(
        level == "green"
        for level, _ in status_items
    )
    overall_level = "green" if overall_ready else "amber"
    headline = (
        "READY FOR IMPORT"
        if overall_ready
        else "ATTENTION RECOMMENDED"
    )
    headline_width = tkfont.Font(font=ready_font).measure(headline)
    status.columnconfigure(
        1,
        weight=1,
        minsize=headline_width + SYSTEM_STATUS_HEADLINE_MARGIN,
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
        text=headline,
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


def bind_system_status_refresh(
    root: tk.Misc,
    refresh: Callable[[], None],
) -> None:
    refresh_pending = False

    def on_focus_in(_event: tk.Event) -> None:
        nonlocal refresh_pending

        if refresh_pending:
            return

        refresh_pending = True

        def run_refresh() -> None:
            nonlocal refresh_pending
            refresh_pending = False
            refresh()

        root.after_idle(run_refresh)

    root.bind("<FocusIn>", on_focus_in)


def run_gui() -> None:
    root = tk.Tk()
    root.title("Mac Photo Studio")
    apply_window_icon(root)
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
    header.columnconfigure(1, weight=1)

    header_camera = load_camera_image(root, 96)
    root._mps_header_camera_image = header_camera
    ttk.Label(
        header,
        image=header_camera,
    ).grid(
        row=0,
        column=0,
        rowspan=2,
        sticky="w",
        padx=(0, 16),
    )

    ttk.Label(
        header,
        text="Mac Photo Studio",
        font=title_font,
    ).grid(
        row=0,
        column=1,
        sticky="w",
    )

    ttk.Label(
        header,
        text="Photography Workflow Manager",
        font=subtitle_font,
    ).grid(
        row=1,
        column=1,
        sticky="w",
        pady=(4, 0),
    )

    ttk.Label(
        header,
        text=f"Version {get_version()}",
        font=version_font,
    ).grid(
        row=0,
        column=2,
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

    def refresh_system_status() -> None:
        render_system_status(
            status,
            ready_font=ready_font,
            status_font=status_font,
            body_font=body_font,
        )

    refresh_system_status()
    bind_system_status_refresh(root, refresh_system_status)

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
        command=lambda: start_import(root, refresh_system_status),
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

    ttk.Button(
        utility_tools,
        text="ℹ  About",
        command=lambda: show_about(root),
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
