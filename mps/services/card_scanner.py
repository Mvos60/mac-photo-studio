from __future__ import annotations

from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.services.media_path_policy import media_files


def format_bytes(size_bytes: int) -> str:
    """Return a human-readable size string."""
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    if size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} B"


def _extensions(
    settings: Settings,
    key: str,
) -> set[str]:
    return {
        str(ext).lower().lstrip(".")
        for ext in settings.get(key, [])
    }


def _candidate_roots(
    settings: Settings,
) -> list[Path]:
    roots: list[Path] = []

    for item in settings.get("media.scan_roots", []):
        root = Path(item).expanduser()

        if root.exists():
            roots.append(root)

    return roots


def _find_dcim(
    root: Path,
) -> Path | None:
    if root.name.upper() == "DCIM":
        return root

    direct = root / "DCIM"

    if direct.exists() and direct.is_dir():
        return direct

    try:
        for child in root.iterdir():
            if (
                child.is_dir()
                and child.name.upper() == "DCIM"
            ):
                return child
    except PermissionError:
        return None

    return None


def _scan_photo_root(
    root: Path,
    settings: Settings,
) -> CardScanResult:
    raw_exts = _extensions(
        settings,
        "media.raw_extensions",
    )
    jpg_exts = _extensions(
        settings,
        "media.jpeg_extensions",
    )
    heif_exts = _extensions(
        settings,
        "media.heif_extensions",
    )
    video_exts = _extensions(
        settings,
        "media.video_extensions",
    )

    dcim = _find_dcim(root)
    scan_root = dcim or root

    raw_count = 0
    jpeg_count = 0
    heif_count = 0
    video_count = 0
    other_count = 0
    total_size = 0

    raw_stems: set[str] = set()
    jpeg_stems: set[str] = set()

    files = media_files(scan_root)

    for file in files:
        ext = file.suffix.lower().lstrip(".")

        try:
            total_size += file.stat().st_size
        except OSError:
            pass

        if ext in raw_exts:
            raw_count += 1
            raw_stems.add(file.stem)
        elif ext in jpg_exts:
            jpeg_count += 1
            jpeg_stems.add(file.stem)
        elif ext in heif_exts:
            heif_count += 1
        elif ext in video_exts:
            video_count += 1
        else:
            other_count += 1

    pair_count = len(
        raw_stems & jpeg_stems
    )
    orphan_raw_count = len(
        raw_stems - jpeg_stems
    )
    orphan_jpeg_count = len(
        jpeg_stems - raw_stems
    )

    return CardScanResult(
        root=root,
        dcim_path=dcim,
        raw_count=raw_count,
        jpeg_count=jpeg_count,
        heif_count=heif_count,
        video_count=video_count,
        pair_count=pair_count,
        orphan_raw_count=orphan_raw_count,
        orphan_jpeg_count=orphan_jpeg_count,
        other_count=other_count,
        total_size_bytes=total_size,
    )


def scan_cards(
    settings: Settings,
) -> list[CardScanResult]:
    """Scan configured removable-media roots.

    This operation is strictly read-only.
    """
    results: list[CardScanResult] = []
    seen: set[Path] = set()

    for base in _candidate_roots(settings):
        try:
            children = [
                path
                for path in base.iterdir()
                if path.is_dir()
            ]
        except PermissionError:
            continue

        for child in children:
            resolved = child.resolve()

            if resolved in seen:
                continue

            seen.add(resolved)

            result = _scan_photo_root(
                child,
                settings,
            )

            if (
                result.dcim_path
                or result.has_photos
            ):
                results.append(result)

    return results


def scan_path(
    path: Path,
    settings: Settings,
) -> CardScanResult:
    """Analyze one explicit folder path.

    This is useful for development and testing when no SD card is inserted.
    The operation is read-only.
    """
    return _scan_photo_root(
        path.expanduser(),
        settings,
    )
