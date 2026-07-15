from __future__ import annotations

from pathlib import Path

from mps.config import Settings
from mps.models.import_decision import CopyOperation, ImportDecision
from mps.models.import_media_batch_plan import ImportMediaBatchPlan
from mps.models.import_media_selection import ImportMediaSelection
from mps.services.imported_photo_registry import (
    file_sha256,
    load_imported_photo_registry,
)
from mps.services.media_path_policy import media_files


def _extensions(
    settings: Settings,
    key: str,
) -> set[str]:
    return {
        str(extension).lower().lstrip(".")
        for extension in settings.get(key, [])
    }


def _photo_extensions(
    settings: Settings,
) -> set[str]:
    return (
        _extensions(settings, "media.raw_extensions")
        | _extensions(settings, "media.jpeg_extensions")
    )


def _source_files(
    selection: ImportMediaSelection,
    settings: Settings,
) -> list[Path]:
    extensions = _photo_extensions(settings)
    files: list[Path] = []

    for source in selection.sources:
        scan_root = source.dcim_path or source.root

        source_files = [
            path
            for path in media_files(scan_root)
            if (
                path.suffix.lower().lstrip(".")
                in extensions
            )
        ]

        files.extend(source_files)

    return files


def _photos_root(
    settings: Settings,
) -> Path:
    return Path(
        settings.get(
            "paths.photos_root",
            "~/Photos_Master",
        )
    ).expanduser()


def _new_source_files(
    source_files: list[Path],
    photos_root: Path,
) -> list[Path]:
    registry = load_imported_photo_registry(
        photos_root
    )

    new_files: list[Path] = []

    for source in source_files:
        try:
            source_hash = file_sha256(source)
        except OSError:
            new_files.append(source)
            continue

        if registry.contains_hash(source_hash):
            continue

        new_files.append(source)

    return new_files


def media_import_destination(
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
) -> Path:
    return (
        _photos_root(settings)
        / str(year)
        / project
        / day
    )


def create_media_batch_plan(
    selection: ImportMediaSelection,
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
) -> ImportMediaBatchPlan:
    photos_root = _photos_root(settings)

    destination = media_import_destination(
        settings,
        year=year,
        project=project,
        day=day,
    )

    discovered_files = _source_files(
        selection,
        settings,
    )

    source_files = _new_source_files(
        discovered_files,
        photos_root,
    )

    copy_operations = [
        CopyOperation(
            source=source,
            destination=destination / source.name,
        )
        for source in source_files
    ]

    estimated_size_bytes = 0

    for source in source_files:
        try:
            estimated_size_bytes += source.stat().st_size
        except OSError:
            pass

    warnings: list[str] = []

    destination_names = [
        operation.destination.name
        for operation in copy_operations
    ]

    if len(destination_names) != len(set(destination_names)):
        warnings.append(
            "Multiple source files map to the same destination filename"
        )

    decision = ImportDecision(
        destination=destination,
        total_files=len(copy_operations),
        estimated_size_bytes=estimated_size_bytes,
        copy_operations=copy_operations,
        warnings=warnings,
    )

    return ImportMediaBatchPlan(
        selection=selection,
        destination=destination,
        decision=decision,
    )
