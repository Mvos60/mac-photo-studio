from __future__ import annotations

from pathlib import Path


class ResourceNotFoundError(FileNotFoundError):
    """Raised when a required packaged resource is unavailable."""


PACKAGE_ROOT = Path(__file__).resolve().parent
ASSET_ROOT = PACKAGE_ROOT / "assets"


def asset_path(relative_path: str | Path) -> Path:
    """Return a packaged asset path independent of the current directory."""

    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Asset path must be package-relative")

    resolved = ASSET_ROOT.joinpath(relative)
    if not resolved.is_file():
        raise ResourceNotFoundError(
            f"Required Mac Photo Studio asset is missing: {relative.as_posix()}"
        )
    return resolved
