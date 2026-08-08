from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_photo_selection import ImportPhotoCandidate
from mps.services.import_media_batch_planner import (
    configured_photos_root,
    filter_new_source_files,
    source_files_for_selection,
)


def build_import_photo_candidates(
    selection: ImportMediaSelection,
    settings: Settings,
    *,
    processed_source_files: tuple[Path, ...] | list[Path] = (),
) -> tuple[ImportPhotoCandidate, ...]:
    """Build deterministic capture candidates without changing source media."""

    processed = set(processed_source_files)
    discovered = [
        path
        for path in source_files_for_selection(selection, settings)
        if path not in processed
    ]
    eligible = filter_new_source_files(
        discovered,
        configured_photos_root(settings),
    )
    raw_extensions = {
        str(value).lower().lstrip(".")
        for value in settings.get("media.raw_extensions", [])
    }
    jpeg_extensions = {
        str(value).lower().lstrip(".")
        for value in settings.get("media.jpeg_extensions", [])
    }
    grouped: dict[str, dict[str, object]] = defaultdict(
        lambda: {"stem": "", "raw": [], "jpeg": []}
    )

    for path in eligible:
        key = path.stem.casefold()
        group = grouped[key]
        if not group["stem"]:
            group["stem"] = path.stem
        extension = path.suffix.lower().lstrip(".")
        if extension in raw_extensions:
            bucket = "raw"
        elif extension in jpeg_extensions:
            bucket = "jpeg"
        else:
            continue
        paths = group[bucket]
        assert isinstance(paths, list)
        paths.append(path)

    candidates = []
    for key, group in sorted(grouped.items()):
        raw_paths = group["raw"]
        jpeg_paths = group["jpeg"]
        assert isinstance(raw_paths, list)
        assert isinstance(jpeg_paths, list)
        candidates.append(ImportPhotoCandidate(
            key=key,
            stem=str(group["stem"]),
            raw_paths=tuple(sorted(raw_paths)),
            jpeg_paths=tuple(sorted(jpeg_paths)),
        ))
    return tuple(candidates)


def source_candidate_paths(
    source: CardScanResult,
    candidates: tuple[ImportPhotoCandidate, ...],
) -> set[Path]:
    scan_root = source.dcim_path or source.root
    return {
        path
        for candidate in candidates
        for path in candidate.source_paths
        if path.is_relative_to(scan_root)
    }
