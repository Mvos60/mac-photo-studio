import pytest

from mps.gui import app as app_module
from mps.gui.app import (
    bind_system_status_refresh,
    build_cli_command,
    build_status_items,
    launch_cli,
    open_path,
    render_system_status,
    resolve_terminal_command,
    run_gui,
    start_import,
)
from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.services.app_resolver import (
    ApplicationResolution,
)


def test_build_cli_command_quotes_paths():
    command = build_cli_command(
        [
            "--analyze-culling",
            "/home/mac/Photos Master/Session",
        ]
    )

    assert command == (
        "mac-photo-studio --analyze-culling "
        "'/home/mac/Photos Master/Session'"
    )


def test_terminal_resolution_prefers_gnome_terminal():
    available = {
        "gnome-terminal",
        "x-terminal-emulator",
    }

    result = resolve_terminal_command(
        "mac-photo-studio import",
        resolver=lambda executable: (
            f"/usr/bin/{executable}"
            if executable in available
            else None
        ),
    )

    assert result is not None
    assert result[0] == "gnome-terminal"


def test_terminal_resolution_uses_fallback():
    result = resolve_terminal_command(
        "mac-photo-studio import",
        resolver=lambda executable: (
            "/usr/bin/x-terminal-emulator"
            if executable
            == "x-terminal-emulator"
            else None
        ),
    )

    assert result is not None
    assert result[0] == "x-terminal-emulator"


def test_terminal_resolution_returns_none_without_terminal():
    result = resolve_terminal_command(
        "mac-photo-studio import",
        resolver=lambda executable: None,
    )

    assert result is None


def test_status_items_use_shared_application_resolver(
    tmp_path,
    monkeypatch,
):
    settings = object()
    calls = []

    monkeypatch.setattr(
        "mps.gui.app.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.gui.app.get_photo_library",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "mps.gui.app.ACTIVE_IMPORT_SESSION",
        tmp_path / "no-active-session.json",
    )

    def resolve(
        received_settings,
        key,
        command_name,
    ):
        calls.append(
            (
                received_settings,
                key,
                command_name,
            )
        )

        return ApplicationResolution(
            name=key,
            found=(key == "digikam"),
            method="test",
            command=(
                "/opt/digikam"
                if key == "digikam"
                else None
            ),
            message="test",
        )

    monkeypatch.setattr(
        "mps.gui.app.resolve_application",
        resolve,
    )

    items = build_status_items()

    assert calls == [
        (settings, "digikam", "digikam"),
        (settings, "darktable", "darktable"),
    ]
    assert (
        "green",
        "digiKam detected",
    ) in items
    assert (
        "amber",
        "darktable not detected automatically",
    ) in items

def test_status_items_show_photo_archive_path_on_own_line(
    tmp_path,
    monkeypatch,
):
    settings = object()

    monkeypatch.setattr(
        "mps.gui.app.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.gui.app.get_photo_library",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "mps.gui.app.ACTIVE_IMPORT_SESSION",
        tmp_path / "no-active-session.json",
    )
    monkeypatch.setattr(
        "mps.gui.app.resolve_application",
        lambda settings, key, command_name:
        ApplicationResolution(
            name=key,
            found=True,
            method="test",
            command=f"/opt/{command_name}",
            message="test",
        ),
    )

    items = build_status_items()

    assert (
        "green",
        f"Photo archive found:\n{tmp_path}",
    ) in items


def test_system_status_refresh_removes_interrupted_session(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    state_path.write_text("active", encoding="utf-8")
    monkeypatch.setattr(
        app_module,
        "ACTIVE_IMPORT_SESSION",
        state_path,
    )
    monkeypatch.setattr(
        app_module,
        "get_photo_library",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        app_module,
        "load_settings",
        lambda: object(),
    )
    monkeypatch.setattr(
        app_module,
        "resolve_application",
        lambda *args: ApplicationResolution(
            name="test",
            found=True,
            method="test",
            command="/opt/test",
            message="test",
        ),
    )

    created = []

    class Widget:
        def __init__(self, _parent, **kwargs):
            self.kwargs = kwargs
            self.destroyed = False
            created.append(self)

        def grid(self, **kwargs):
            return self

        def destroy(self):
            self.destroyed = True

    class Status:
        def __init__(self):
            self.children = []

        def winfo_children(self):
            children = self.children
            self.children = []
            return children

    status = Status()
    monkeypatch.setattr(app_module.tk, "Label", Widget)
    monkeypatch.setattr(app_module.ttk, "Label", Widget)

    def render():
        start = len(created)
        render_system_status(
            status,
            ready_font=("ready",),
            status_font=("status",),
            body_font=("body",),
        )
        status.children = created[start:]

    render()
    first_texts = [widget.kwargs.get("text") for widget in created]

    assert "An interrupted import session is available" in first_texts
    assert "ATTENTION RECOMMENDED" in first_texts

    first_widgets = list(status.children)
    state_path.unlink()
    render()
    refreshed_texts = [
        widget.kwargs.get("text")
        for widget in status.children
    ]

    assert all(widget.destroyed for widget in first_widgets)
    assert "An interrupted import session is available" not in refreshed_texts
    assert "No interrupted import session" in refreshed_texts
    assert "READY FOR IMPORT" in refreshed_texts
    assert "Everything looks ready." in refreshed_texts


def test_focus_restore_schedules_exactly_one_status_refresh():
    callbacks = []
    bindings = []
    refreshes = []

    class Root:
        def bind(self, sequence, callback):
            bindings.append((sequence, callback))

        def after_idle(self, callback):
            callbacks.append(callback)

    bind_system_status_refresh(
        Root(),
        lambda: refreshes.append(True),
    )

    assert len(bindings) == 1
    assert bindings[0][0] == "<FocusIn>"

    focus_callback = bindings[0][1]
    focus_callback(object())
    focus_callback(object())

    assert len(callbacks) == 1
    callbacks.pop()()
    assert refreshes == [True]


def test_start_screen_uses_consistent_action_labels():
    import inspect

    source = inspect.getsource(run_gui)

    expected_labels = (
        "📥  Import Photographs",
        "🔍  Analyze Culling",
        "🗄️  Quarantine Manager",
        "✓  Verify Photograph",
        "📜  Show Photo History",
        "Application Tools",
        "⚙  Settings",
        "📄  Logs",
        "ℹ  About",
        "Close",
    )

    for label in expected_labels:
        assert f'text="{label}"' in source

    old_labels = (
        "📥  Import photographs",
        "🔍  Analyze culling",
        "✓  Verify photograph",
        "📜  Show photo history",
    )

    for label in old_labels:
        assert f'text="{label}"' not in source

def test_start_screen_default_height_keeps_bottom_action_visible():
    import inspect

    source = inspect.getsource(run_gui)

    assert 'root.geometry("1040x880")' in source
    assert "root.minsize(980, 840)" in source

def test_launch_cli_starts_resolved_terminal(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "mps.gui.app.resolve_terminal_command",
        lambda command: [
            "gnome-terminal",
            "--",
            "bash",
            "-lc",
            command,
        ],
    )
    monkeypatch.setattr(
        "mps.gui.app.subprocess.Popen",
        lambda command, **kwargs: calls.append(
            (command, kwargs)
        ),
    )

    launch_cli(["--show-config"])

    assert calls == [
        (
            [
                "gnome-terminal",
                "--",
                "bash",
                "-lc",
                "mac-photo-studio --show-config",
            ],
            {
                "start_new_session": True,
            },
        )
    ]


def test_launch_cli_reports_missing_terminal(monkeypatch):
    dialogs = []

    monkeypatch.setattr(
        "mps.gui.app.resolve_terminal_command",
        lambda command: None,
    )
    monkeypatch.setattr(
        "mps.gui.app.messagebox.showerror",
        lambda title, message: dialogs.append(
            (title, message)
        ),
    )

    launch_cli(["import"])

    assert dialogs == [
        (
            "Terminal Unavailable",
            (
                "No supported terminal application was found.\n\n"
                "Run this command manually:\n\n"
                "mac-photo-studio import"
            ),
        )
    ]


def test_launch_cli_reports_start_failure(monkeypatch):
    dialogs = []

    monkeypatch.setattr(
        "mps.gui.app.resolve_terminal_command",
        lambda command: ["terminal", command],
    )

    def fail(*args, **kwargs):
        raise OSError("launch failed")

    monkeypatch.setattr(
        "mps.gui.app.subprocess.Popen",
        fail,
    )
    monkeypatch.setattr(
        "mps.gui.app.messagebox.showerror",
        lambda title, message: dialogs.append(
            (title, message)
        ),
    )

    launch_cli(["import"])

    assert dialogs == [
        (
            "Could Not Start Command",
            (
                "The terminal could not be opened.\n\n"
                "launch failed\n\n"
                "Command:\nmac-photo-studio import"
            ),
        )
    ]


def test_open_path_opens_existing_location(
    tmp_path,
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        "mps.gui.app.shutil.which",
        lambda executable: "/usr/bin/xdg-open",
    )
    monkeypatch.setattr(
        "mps.gui.app.subprocess.Popen",
        lambda command, **kwargs: calls.append(
            (command, kwargs)
        ),
    )

    open_path(tmp_path)

    assert calls == [
        (
            [
                "/usr/bin/xdg-open",
                str(tmp_path),
            ],
            {
                "start_new_session": True,
            },
        )
    ]


def test_open_path_reports_missing_location(
    tmp_path,
    monkeypatch,
):
    dialogs = []
    missing = tmp_path / "missing"

    monkeypatch.setattr(
        "mps.gui.app.messagebox.showinfo",
        lambda title, message: dialogs.append(
            (title, message)
        ),
    )

    open_path(missing)

    assert dialogs == [
        (
            "Location Unavailable",
            f"This location does not exist yet:\n\n{missing}",
        )
    ]


def test_open_path_reports_missing_file_manager(
    tmp_path,
    monkeypatch,
):
    dialogs = []

    monkeypatch.setattr(
        "mps.gui.app.shutil.which",
        lambda executable: None,
    )
    monkeypatch.setattr(
        "mps.gui.app.messagebox.showerror",
        lambda title, message: dialogs.append(
            (title, message)
        ),
    )

    open_path(tmp_path)

    assert dialogs == [
        (
            "File Manager Unavailable",
            (
                "The desktop file manager could not be started.\n\n"
                f"Location:\n{tmp_path}"
            ),
        )
    ]


def test_open_path_reports_open_failure(
    tmp_path,
    monkeypatch,
):
    dialogs = []

    monkeypatch.setattr(
        "mps.gui.app.shutil.which",
        lambda executable: "/usr/bin/xdg-open",
    )

    def fail(*args, **kwargs):
        raise OSError("open failed")

    monkeypatch.setattr(
        "mps.gui.app.subprocess.Popen",
        fail,
    )
    monkeypatch.setattr(
        "mps.gui.app.messagebox.showerror",
        lambda title, message: dialogs.append(
            (title, message)
        ),
    )

    open_path(tmp_path)

    assert dialogs == [
        (
            "Could Not Open Location",
            f"open failed\n\nLocation:\n{tmp_path}",
        )
    ]


def test_import_action_cancel_starts_no_terminal(
    tmp_path,
    monkeypatch,
):
    parent = object()
    photos_root = tmp_path / "Photos_Master"
    monkeypatch.setattr(
        app_module,
        "ACTIVE_IMPORT_SESSION",
        tmp_path / "missing-state.json",
    )
    selector_calls = []
    launches = []

    monkeypatch.setattr(
        app_module,
        "get_photo_library",
        lambda: photos_root,
    )
    monkeypatch.setattr(
        app_module,
        "choose_import_destination",
        lambda **kwargs: selector_calls.append(kwargs) or None,
    )
    monkeypatch.setattr(
        app_module,
        "launch_cli",
        lambda arguments: launches.append(arguments),
    )

    start_import(parent)

    assert selector_calls == [
        {
            "parent": parent,
            "photos_root": photos_root,
        }
    ]
    assert launches == []


@pytest.mark.parametrize(
    "description",
    [
        "Ljubljana Old Town",
        "",
    ],
)
def test_import_action_launches_one_structured_command(
    description,
    tmp_path,
    monkeypatch,
):
    parent = object()
    photos_root = tmp_path / "Alternate Photos"
    monkeypatch.setattr(
        app_module,
        "ACTIVE_IMPORT_SESSION",
        tmp_path / "missing-state.json",
    )
    destination_selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic Journey",
        description=description,
    )
    selector_calls = []
    launches = []

    monkeypatch.setattr(
        app_module,
        "get_photo_library",
        lambda: photos_root,
    )
    monkeypatch.setattr(
        app_module,
        "choose_import_destination",
        lambda **kwargs: (
            selector_calls.append(kwargs)
            or destination_selection
        ),
    )
    monkeypatch.setattr(
        app_module,
        "launch_cli",
        lambda arguments: launches.append(arguments),
    )

    start_import(parent)

    assert selector_calls == [
        {
            "parent": parent,
            "photos_root": photos_root,
        }
    ]
    assert launches == [
        [
            "import",
            "--destination-year",
            "2026",
            "--destination-month-day",
            "08-01",
            "--destination-project",
            "Adriatic Journey",
            "--destination-description",
            description,
        ]
    ]


def test_import_button_uses_destination_import_action():
    import inspect

    source = inspect.getsource(run_gui)

    assert "command=lambda: start_import(root)" in source


@pytest.mark.parametrize("state_bytes", [b"active", b"{malformed"])
def test_import_action_with_active_state_launches_plain_import(
    state_bytes,
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    state_path.write_bytes(state_bytes)
    launches = []
    library_calls = []
    selector_calls = []

    monkeypatch.setattr(
        app_module,
        "ACTIVE_IMPORT_SESSION",
        state_path,
    )
    monkeypatch.setattr(
        app_module,
        "get_photo_library",
        lambda: library_calls.append(True),
    )
    monkeypatch.setattr(
        app_module,
        "choose_import_destination",
        lambda **kwargs: selector_calls.append(kwargs),
    )
    monkeypatch.setattr(
        app_module,
        "launch_cli",
        lambda arguments: launches.append(arguments),
    )

    start_import(object())

    assert library_calls == []
    assert selector_calls == []
    assert launches == [["import"]]
    assert state_path.read_bytes() == state_bytes
