from mps.gui.app import (
    build_cli_command,
    build_status_items,
    resolve_terminal_command,
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
