from __future__ import annotations

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
    return path.exists() and path.is_file()


def _find_appimage(search_dirs: list[str], name_contains: str) -> str | None:
    candidates: list[Path] = []
    for directory in search_dirs:
        root = Path(directory).expanduser()
        if not root.exists():
            continue
        candidates.extend(root.glob("*.AppImage"))
        candidates.extend(root.glob("*.appimage"))

    needle = name_contains.lower()
    for candidate in sorted(candidates):
        if needle in candidate.name.lower():
            return str(candidate)
    return None


def _flatpak_available(flatpak_id: str | None) -> bool:
    if not flatpak_id or not shutil.which("flatpak"):
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


def resolve_application(settings: Settings, key: str, command_name: str) -> ApplicationResolution:
    base = f"applications.{key}"
    configured = settings.get(f"{base}.executable", "auto")

    if configured and configured != "auto":
        path = Path(configured).expanduser()
        if _is_executable_file(path):
            return ApplicationResolution(key, True, "configured", str(path), f"configured path: {path}")
        return ApplicationResolution(key, False, "configured", str(path), f"configured path not found: {path}")

    path_command = shutil.which(command_name)
    if path_command:
        return ApplicationResolution(key, True, "PATH", path_command, path_command)

    flatpak_id = settings.get(f"{base}.flatpak_id")
    if _flatpak_available(flatpak_id):
        return ApplicationResolution(key, True, "flatpak", f"flatpak run {flatpak_id}", flatpak_id)

    appimage_dirs = settings.get(f"{base}.appimage_search_dirs", [])
    appimage = _find_appimage(appimage_dirs, command_name)
    if appimage:
        return ApplicationResolution(key, True, "AppImage", appimage, appimage)

    return ApplicationResolution(key, False, "not found", None, "not found")
