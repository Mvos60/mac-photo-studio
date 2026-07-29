from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from mps.config import Settings


@dataclass(frozen=True)
class ApplicationResolution:
    name: str
    found: bool
    method: str
    command: str | None
    message: str


def _is_executable_file(path: Path) -> bool:
    return (
        path.exists()
        and path.is_file()
        and os.access(path, os.X_OK)
    )


def _appimage_version(path: Path) -> tuple[int, ...]:
    match = re.search(
        r"(?<!\d)(\d+(?:\.\d+)+)",
        path.name,
    )

    if match is None:
        return ()

    return tuple(
        int(part)
        for part in match.group(1).split(".")
    )


def _appimage_sort_key(
    path: Path,
) -> tuple[tuple[int, ...], float, str]:
    try:
        modified_at = path.stat().st_mtime
    except OSError:
        modified_at = 0.0

    return (
        _appimage_version(path),
        modified_at,
        path.name.lower(),
    )


def _find_appimage(
    search_dirs: list[str],
    name_contains: str,
) -> str | None:
    needle = name_contains.lower()

    for directory in search_dirs:
        root = Path(directory).expanduser()

        if not root.is_dir():
            continue

        candidates = [
            candidate
            for pattern in ("*.AppImage", "*.appimage")
            for candidate in root.glob(pattern)
            if (
                candidate.is_file()
                and needle in candidate.name.lower()
                and os.access(candidate, os.X_OK)
            )
        ]

        if candidates:
            newest = max(
                candidates,
                key=_appimage_sort_key,
            )
            return str(newest)

    return None


def _flatpak_available(
    flatpak_id: str | None,
) -> bool:
    if (
        not flatpak_id
        or not shutil.which("flatpak")
    ):
        return False

    try:
        result = subprocess.run(
            ["flatpak", "info", flatpak_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


def resolve_application(
    settings: Settings,
    key: str,
    command_name: str,
) -> ApplicationResolution:
    base = f"applications.{key}"
    configured = settings.get(
        f"{base}.executable",
        "auto",
    )
    configured_problem: str | None = None

    if configured and configured != "auto":
        path = Path(configured).expanduser()

        if _is_executable_file(path):
            return ApplicationResolution(
                key,
                True,
                "configured",
                str(path),
                f"configured path: {path}",
            )

        configured_problem = (
            f"configured path not found or not executable: "
            f"{path}"
        )

    path_command = shutil.which(command_name)

    if path_command:
        message = path_command

        if configured_problem:
            message = (
                f"{configured_problem}; "
                f"automatic fallback: {path_command}"
            )

        return ApplicationResolution(
            key,
            True,
            "PATH",
            path_command,
            message,
        )

    flatpak_id = settings.get(
        f"{base}.flatpak_id"
    )

    if _flatpak_available(flatpak_id):
        command = f"flatpak run {flatpak_id}"
        message = str(flatpak_id)

        if configured_problem:
            message = (
                f"{configured_problem}; "
                f"automatic fallback: {flatpak_id}"
            )

        return ApplicationResolution(
            key,
            True,
            "flatpak",
            command,
            message,
        )

    appimage_dirs = settings.get(
        f"{base}.appimage_search_dirs",
        [],
    )
    appimage = _find_appimage(
        appimage_dirs,
        command_name,
    )

    if appimage:
        message = appimage

        if configured_problem:
            message = (
                f"{configured_problem}; "
                f"automatic fallback: {appimage}"
            )

        return ApplicationResolution(
            key,
            True,
            "AppImage",
            appimage,
            message,
        )

    message = "not found"

    if configured_problem:
        message = (
            f"{configured_problem}; "
            "no automatic installation found"
        )

    return ApplicationResolution(
        key,
        False,
        "not found",
        None,
        message,
    )
