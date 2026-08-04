import pytest

from mps.gui import app as app_module
from mps.config import Settings
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
            self.column_options = {}

        def winfo_children(self):
            children = self.children
            self.children = []
            return children

        def columnconfigure(self, column, **kwargs):
            self.column_options[column] = kwargs

    status = Status()
    monkeypatch.setattr(app_module.tk, "Label", Widget)
    monkeypatch.setattr(app_module.ttk, "Label", Widget)

    class Font:
        def __init__(self, *, font):
            assert font == ("ready",)

        def measure(self, text):
            assert text in {"ATTENTION RECOMMENDED", "READY FOR IMPORT"}
            return 237

    monkeypatch.setattr(app_module.tkfont, "Font", Font)

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
    attention = next(
        widget
        for widget in created
        if widget.kwargs.get("text") == "ATTENTION RECOMMENDED"
    )
    assert "padding" not in attention.kwargs
    assert status.column_options[1] == {
        "weight": 1,
        "minsize": 237 + app_module.SYSTEM_STATUS_HEADLINE_MARGIN,
    }

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


def test_main_window_uses_camera_icon_and_retained_header_image():
    import inspect

    source = inspect.getsource(run_gui)
    assert "apply_window_icon(root)" in source
    assert "header_camera = load_camera_image(root, 96)" in source
    assert "root._mps_header_camera_image = header_camera" in source
    assert "CAMERA_BACKDROP" not in source
    assert 'text="Mac Photo Studio"' in source
    assert 'text="📷  Mac Photo Studio"' not in source
    assert "command=lambda: show_about(root)" in source

def test_launch_cli_starts_resolved_terminal(monkeypatch):
    calls = []

    monkeypatch.setattr(
        "mps.gui.app.resolve_terminal_command",
        lambda command, **kwargs: [
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
        lambda command, **kwargs: None,
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
        lambda command, **kwargs: ["terminal", command],
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
def test_import_action_starts_one_native_structured_import(
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
    starts = []

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
        app_module, "load_settings", lambda: Settings({
            "paths": {"photos_root": str(photos_root)}
        })
    )
    monkeypatch.setattr(
        app_module, "_start_native_import",
        lambda *args, **kwargs: starts.append((args, kwargs)),
    )

    start_import(parent)

    assert selector_calls == [
        {
            "parent": parent,
            "photos_root": photos_root,
        }
    ]
    assert len(starts) == 1
    kwargs = starts[0][1]
    assert kwargs["destination_selection"] is destination_selection
    assert kwargs["destination"] == destination_selection.destination_path(
        photos_root
    )
    assert kwargs["session"] is None
    assert kwargs["protect_existing_state"] is False


def test_import_button_uses_destination_import_action():
    import inspect

    source = inspect.getsource(run_gui)

    assert "command=lambda: start_import(root, refresh_system_status)" in source


def test_import_action_with_structured_state_resumes_natively(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    original_state = b"active"
    state_path.write_bytes(original_state)
    starts = []
    library_calls = []
    selector_calls = []
    action_calls = []
    parent = object()

    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
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
    from mps.models.import_media_session import (
        ImportMediaSession,
        ImportMediaSessionDestination,
    )
    selection = ImportDestinationSelection(
        year=2026, month_day="08-01", project="Adriatic"
    )
    import_root = tmp_path / "Photos" / "2026" / "08" / "01" / "Adriatic"
    session = ImportMediaSession(
        session_id="S-RESUME",
        destination=ImportMediaSessionDestination(selection, import_root),
    )
    monkeypatch.setattr(
        app_module, "choose_import_session_action",
        lambda **kwargs: action_calls.append(kwargs) or "resume",
    )
    monkeypatch.setattr(
        app_module, "load_import_media_session", lambda path: session
    )
    monkeypatch.setattr(
        app_module, "can_resume_import_media_session", lambda *a, **k: True
    )
    monkeypatch.setattr(
        app_module,
        "_start_native_import",
        lambda *args, **kwargs: starts.append((args, kwargs)),
    )

    start_import(parent)

    assert library_calls == []
    assert selector_calls == []
    assert action_calls == [{"parent": parent}]
    assert len(starts) == 1
    assert starts[0][1]["destination_selection"] is selection
    assert starts[0][1]["destination"] is import_root
    assert starts[0][1]["session"] is session
    assert starts[0][1]["protect_existing_state"] is False
    assert state_path.read_bytes() == original_state


def test_import_action_with_active_state_start_new_uses_selector_once(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    original_state = b"active"
    state_path.write_bytes(original_state)
    parent = object()
    selection = ImportDestinationSelection(
        year=2026,
        month_day="08-02",
        project="Project With Spaces",
        description="Session Description",
    )
    action_calls = []
    selector_calls = []
    starts = []

    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
    monkeypatch.setattr(
        app_module,
        "choose_import_session_action",
        lambda **kwargs: action_calls.append(kwargs) or "start-new",
    )
    monkeypatch.setattr(
        app_module,
        "get_photo_library",
        lambda: tmp_path / "Photos Master",
    )
    monkeypatch.setattr(
        app_module,
        "choose_import_destination",
        lambda **kwargs: selector_calls.append(kwargs) or selection,
    )
    monkeypatch.setattr(
        app_module.messagebox, "askyesno", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        app_module, "load_settings", lambda: Settings({
            "paths": {"photos_root": str(tmp_path / "Photos Master")}
        })
    )
    monkeypatch.setattr(
        app_module, "_start_native_import",
        lambda *args, **kwargs: starts.append((args, kwargs)),
    )

    start_import(parent)

    assert action_calls == [{"parent": parent}]
    assert len(selector_calls) == 1
    assert len(starts) == 1
    assert starts[0][1]["session"] is None
    assert starts[0][1]["destination_selection"] is selection
    assert starts[0][1]["protect_existing_state"] is True
    assert state_path.read_bytes() == original_state


def test_import_action_with_active_state_cancel_starts_nothing(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    original_state = b"active"
    state_path.write_bytes(original_state)
    launches = []
    selectors = []

    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
    monkeypatch.setattr(
        app_module,
        "choose_import_session_action",
        lambda **kwargs: "cancel",
    )
    monkeypatch.setattr(
        app_module,
        "choose_import_destination",
        lambda **kwargs: selectors.append(kwargs),
    )
    monkeypatch.setattr(
        app_module,
        "launch_cli",
        lambda arguments: launches.append(arguments),
    )

    start_import(object())

    assert selectors == []
    assert launches == []
    assert state_path.read_bytes() == original_state


def test_legacy_resume_uses_native_legacy_values_without_migration(
    tmp_path,
    monkeypatch,
):
    from mps.gui.legacy_import_resume_dialog import LegacyImportDestination
    from mps.models.import_media_session import ImportMediaSession

    state_path = tmp_path / "active_import_session.json"
    original = b"legacy-state"
    state_path.write_bytes(original)
    photos_root = tmp_path / "Photos"
    settings = Settings({"paths": {"photos_root": str(photos_root)}})
    session = ImportMediaSession(session_id="S-LEGACY")
    legacy_calls = []
    calendar_calls = []
    starts = []
    validations = []
    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
    monkeypatch.setattr(app_module, "load_settings", lambda: settings)
    monkeypatch.setattr(
        app_module, "choose_import_session_action", lambda **kwargs: "resume"
    )
    monkeypatch.setattr(
        app_module, "load_import_media_session", lambda path: session
    )
    monkeypatch.setattr(
        app_module,
        "choose_legacy_import_destination",
        lambda **kwargs: legacy_calls.append(kwargs)
        or LegacyImportDestination(2024, "Legacy", "Day 3"),
    )
    monkeypatch.setattr(
        app_module, "choose_import_destination",
        lambda **kwargs: calendar_calls.append(kwargs),
    )
    monkeypatch.setattr(
        app_module, "can_resume_import_media_session",
        lambda current, root, **kwargs: validations.append(root) or True,
    )
    monkeypatch.setattr(
        app_module, "_start_native_import",
        lambda *args, **kwargs: starts.append(kwargs),
    )
    monkeypatch.setattr(
        app_module, "launch_cli",
        lambda arguments: pytest.fail("GUI resume must not launch terminal"),
    )

    start_import(object())

    expected_root = photos_root / "2024" / "Legacy" / "Day 3"
    assert len(legacy_calls) == 1
    assert calendar_calls == []
    assert validations == [expected_root]
    assert starts[0]["destination_selection"] is None
    assert starts[0]["destination"] == expected_root
    assert starts[0]["session"] is session
    assert session.destination is None
    assert state_path.read_bytes() == original


def test_legacy_resume_cancel_preserves_state_and_starts_nothing(
    tmp_path,
    monkeypatch,
):
    from mps.models.import_media_session import ImportMediaSession

    state_path = tmp_path / "active_import_session.json"
    state_path.write_bytes(b"legacy")
    starts = []
    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
    monkeypatch.setattr(
        app_module, "choose_import_session_action", lambda **kwargs: "resume"
    )
    monkeypatch.setattr(
        app_module, "load_import_media_session",
        lambda path: ImportMediaSession(session_id="S-LEGACY"),
    )
    monkeypatch.setattr(
        app_module, "choose_legacy_import_destination", lambda **kwargs: None
    )
    monkeypatch.setattr(
        app_module, "_start_native_import",
        lambda *args, **kwargs: starts.append(kwargs),
    )
    start_import(object())
    assert starts == []
    assert state_path.read_bytes() == b"legacy"


def test_corrupt_resume_state_shows_error_and_remains_unchanged(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    original = b"not-json"
    state_path.write_bytes(original)
    errors = []
    starts = []
    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
    monkeypatch.setattr(
        app_module, "choose_import_session_action", lambda **kwargs: "resume"
    )
    monkeypatch.setattr(
        app_module.messagebox, "showerror",
        lambda *args, **kwargs: errors.append((args, kwargs)),
    )
    monkeypatch.setattr(
        app_module, "_start_native_import",
        lambda *args, **kwargs: starts.append(kwargs),
    )
    start_import(object())
    assert errors
    assert starts == []
    assert state_path.read_bytes() == original


def test_start_new_rejection_preserves_state_and_starts_nothing(
    tmp_path,
    monkeypatch,
):
    state_path = tmp_path / "active_import_session.json"
    original = b"active"
    state_path.write_bytes(original)
    selection = ImportDestinationSelection(2026, "08-02", "Project")
    starts = []
    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", state_path)
    monkeypatch.setattr(
        app_module, "choose_import_session_action", lambda **kwargs: "start-new"
    )
    monkeypatch.setattr(
        app_module, "choose_import_destination", lambda **kwargs: selection
    )
    monkeypatch.setattr(
        app_module.messagebox, "askyesno", lambda *args, **kwargs: False
    )
    monkeypatch.setattr(
        app_module, "_start_native_import",
        lambda *args, **kwargs: starts.append(kwargs),
    )
    start_import(object())
    assert starts == []
    assert state_path.read_bytes() == original


def test_active_native_import_blocks_second_action(monkeypatch):
    class ActiveController:
        is_active = True

    warnings = []
    monkeypatch.setattr(app_module, "_import_controller", ActiveController())
    monkeypatch.setattr(
        app_module.messagebox, "showwarning",
        lambda *args, **kwargs: warnings.append((args, kwargs)),
    )
    monkeypatch.setattr(
        app_module, "choose_import_destination",
        lambda **kwargs: pytest.fail("selector must not open"),
    )
    start_import(object())
    assert warnings


def test_native_start_opens_window_and_starts_runner_once(
    tmp_path,
    monkeypatch,
):
    windows = []
    runner_calls = []

    class Controller:
        def start(self, runner):
            runner_calls.append(runner)

    monkeypatch.setattr(app_module, "_import_controller", Controller())
    monkeypatch.setattr(
        app_module, "ImportWindow",
        lambda *args, **kwargs: windows.append((args, kwargs)) or object(),
    )
    received = []
    monkeypatch.setattr(
        app_module, "run_import_media_session",
        lambda settings, **kwargs: received.append(kwargs) or object(),
    )
    selection = ImportDestinationSelection(2026, "08-01", "Project")
    settings = Settings({"paths": {"photos_root": str(tmp_path)}})
    app_module._start_native_import(
        object(), settings=settings, year=2026, project="Project",
        day=selection.day_session, destination_selection=selection,
        destination=selection.destination_path(tmp_path), action="New import",
        session=None, protect_existing_state=False, refresh_status=None,
    )
    assert len(windows) == 1
    assert len(runner_calls) == 1
    events = []
    event_sink = events.append
    runner_calls[0](event_sink, __import__("threading").Event())
    assert len(received) == 1
    assert received[0]["event_sink"] is event_sink
    assert received[0]["interaction_adapter"] is not None
    assert received[0]["destination_selection"] is selection
    assert received[0]["wait_for_initial_media"] is True


def test_import_terminal_command_closes_on_success_and_waits_on_error():
    command = resolve_terminal_command(
        "mac-photo-studio import",
        resolver=lambda executable: executable == "gnome-terminal",
        import_command=True,
        title="Mac Photo Studio Import",
    )

    assert command is not None
    shell = command[-1]
    assert 'status=$?' in shell
    assert 'if [ "$status" -ne 0 ]' in shell
    assert 'Import exited with status $status.' in shell
    assert 'read -rp "Press Enter to close..."' in shell
    assert 'exit "$status"' in shell


@pytest.mark.parametrize(
    ("arguments", "title"),
    [
        (["import"], "Mac Photo Studio Import"),
        (["import", "--active-session-action", "resume"], "Mac Photo Studio Import — Resume"),
        (["import", "--active-session-action", "start-new"], "Mac Photo Studio Import — Start new"),
    ],
)
def test_import_terminal_titles_are_derived_from_arguments(arguments, title):
    command = resolve_terminal_command(
        "mac-photo-studio import",
        resolver=lambda executable: executable == "gnome-terminal",
        import_command=True,
        title=title,
    )

    assert command[1:4] == ["-t", title, "--wait"]
    assert command[4:7] == ["--", "bash", "-lc"]


def test_import_terminal_without_title_capability_remains_usable():
    command = resolve_terminal_command(
        "mac-photo-studio import",
        resolver=lambda executable: executable == "xfce4-terminal",
        import_command=True,
    )

    assert command[0] == "xfce4-terminal"
    assert "--command" in command


def test_second_import_terminal_is_blocked_while_first_is_active(monkeypatch):
    class Process:
        def poll(self):
            return None

    calls = []
    dialogs = []
    monkeypatch.setattr(app_module, "_active_import_process", Process())
    monkeypatch.setattr("mps.gui.app.messagebox.showwarning", lambda *args: dialogs.append(args))
    monkeypatch.setattr("mps.gui.app.subprocess.Popen", lambda *args, **kwargs: calls.append(args))

    launch_cli(["import"])

    assert calls == []
    assert dialogs == [("Import Already Running", "An import terminal is already running.")]


@pytest.mark.parametrize("exit_status", [0, 1])
def test_finished_import_terminal_can_be_replaced(exit_status, monkeypatch):
    class FinishedProcess:
        def poll(self):
            return exit_status

    class NewProcess:
        def poll(self):
            return None

    calls = []
    monkeypatch.setattr(app_module, "_active_import_process", FinishedProcess())
    monkeypatch.setattr(
        app_module,
        "resolve_terminal_command",
        lambda command, **kwargs: ["terminal", command],
    )
    monkeypatch.setattr(
        "mps.gui.app.subprocess.Popen",
        lambda command, **kwargs: calls.append(NewProcess()) or calls[-1],
    )

    launch_cli(["import"])

    assert len(calls) == 1
    assert app_module._active_import_process is calls[0]


def test_cancel_does_not_register_import_terminal(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "_active_import_process", None)
    monkeypatch.setattr(app_module, "ACTIVE_IMPORT_SESSION", tmp_path / "missing-state.json")
    monkeypatch.setattr(app_module, "get_photo_library", lambda: tmp_path / "photos")
    monkeypatch.setattr(app_module, "choose_import_destination", lambda **kwargs: None)

    start_import(object())

    assert app_module._active_import_process is None
