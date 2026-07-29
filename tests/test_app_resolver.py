from pathlib import Path

from mps.config import Settings
from mps.services.app_resolver import (
    resolve_application,
)


def _settings(
    *,
    executable: str = "auto",
    search_dirs: list[str] | None = None,
) -> Settings:
    return Settings(
        {
            "applications": {
                "digikam": {
                    "executable": executable,
                    "flatpak_id": (
                        "org.kde.digikam"
                    ),
                    "appimage_search_dirs": (
                        search_dirs or []
                    ),
                },
            },
        }
    )


def _appimage(path: Path) -> Path:
    path.write_text(
        "#!/bin/sh\nexit 0\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _disable_automatic_commands(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "mps.services.app_resolver.shutil.which",
        lambda command: None,
    )
    monkeypatch.setattr(
        "mps.services.app_resolver."
        "_flatpak_available",
        lambda flatpak_id: False,
    )


def test_configured_executable_is_preferred(
    tmp_path,
):
    configured = _appimage(
        tmp_path / "digiKam-custom.appimage"
    )

    result = resolve_application(
        _settings(executable=str(configured)),
        "digikam",
        "digikam",
    )

    assert result.found is True
    assert result.method == "configured"
    assert result.command == str(configured)


def test_missing_configured_path_uses_automatic_fallback(
    tmp_path,
    monkeypatch,
):
    missing = tmp_path / "digiKam-old.appimage"

    monkeypatch.setattr(
        "mps.services.app_resolver.shutil.which",
        lambda command: (
            "/usr/bin/digikam"
            if command == "digikam"
            else None
        ),
    )

    result = resolve_application(
        _settings(executable=str(missing)),
        "digikam",
        "digikam",
    )

    assert result.found is True
    assert result.method == "PATH"
    assert result.command == "/usr/bin/digikam"
    assert "configured path not found" in result.message
    assert "automatic fallback" in result.message


def test_newest_versioned_appimage_is_selected(
    tmp_path,
    monkeypatch,
):
    older = _appimage(
        tmp_path
        / "digiKam-8.8.0-Qt6-x86-64.appimage"
    )
    newest = _appimage(
        tmp_path
        / "digiKam-9.1.0-Qt6-x86-64.appimage"
    )

    _disable_automatic_commands(monkeypatch)

    result = resolve_application(
        _settings(search_dirs=[str(tmp_path)]),
        "digikam",
        "digikam",
    )

    assert older.exists()
    assert result.found is True
    assert result.method == "AppImage"
    assert result.command == str(newest)


def test_search_directory_order_is_respected(
    tmp_path,
    monkeypatch,
):
    applications = tmp_path / "Applications"
    downloads = tmp_path / "Downloads"
    applications.mkdir()
    downloads.mkdir()

    preferred = _appimage(
        applications
        / "digiKam-9.1.0-Qt6-x86-64.appimage"
    )
    _appimage(
        downloads
        / "digiKam-10.0.0-Qt6-x86-64.appimage"
    )

    _disable_automatic_commands(monkeypatch)

    result = resolve_application(
        _settings(
            search_dirs=[
                str(applications),
                str(downloads),
            ]
        ),
        "digikam",
        "digikam",
    )

    assert result.command == str(preferred)


def test_non_executable_appimage_is_ignored(
    tmp_path,
    monkeypatch,
):
    candidate = (
        tmp_path
        / "digiKam-9.1.0-Qt6-x86-64.appimage"
    )
    candidate.write_text(
        "not executable",
        encoding="utf-8",
    )
    candidate.chmod(0o644)

    _disable_automatic_commands(monkeypatch)

    result = resolve_application(
        _settings(search_dirs=[str(tmp_path)]),
        "digikam",
        "digikam",
    )

    assert result.found is False
    assert result.method == "not found"
    assert result.command is None
