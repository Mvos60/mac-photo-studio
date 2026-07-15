from __future__ import annotations

from pathlib import Path

_EXCLUDED_DIRECTORY_NAMES = {
    "$recycle.bin",
    "system volume information",
}


def is_excluded_media_directory_name(
    name: str,
) -> bool:
    normalized = name.casefold()

    if normalized.startswith(".trash"):
        return True

    return normalized in _EXCLUDED_DIRECTORY_NAMES


def is_excluded_media_path(
    path: str | Path,
    scan_root: str | Path,
) -> bool:
    candidate = Path(path)
    root = Path(scan_root)

    try:
        relative = candidate.relative_to(root)
    except ValueError:
        relative = candidate

    return any(
        is_excluded_media_directory_name(part)
        for part in relative.parts[:-1]
    )


def media_files(
    scan_root: str | Path,
) -> list[Path]:
    root = Path(scan_root)

    try:
        return sorted(
            path
            for path in root.rglob("*")
            if (
                path.is_file()
                and not is_excluded_media_path(
                    path,
                    root,
                )
            )
        )
    except PermissionError:
        return []
