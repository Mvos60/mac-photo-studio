from __future__ import annotations

from pathlib import Path

from mps.config import Settings
from mps.models.import_decision import CopyOperation, ImportDecision
from mps.models.import_media_batch_plan import ImportMediaBatchPlan
from mps.models.import_media_selection import ImportMediaSelection


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

        try:
            source_files = sorted(
                path
                for path in scan_root.rglob("*")
                if (
                    path.is_file()
                    and path.suffix.lower().lstrip(".")
                    in extensions
                )
            )
        except PermissionError:
            source_files = []

        files.extend(source_files)

    return files


def media_import_destination(
    settings: Settings,
    *,
    year: int,
    project: str,
    day: str,
) -> Path:
    photos_root = Path(
        settings.get(
            "paths.photos_root",
            "~/Photos_Master",
        )
    ).expanduser()

    return (
        photos_root
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
    destination = media_import_destination(
        settings,
        year=year,
        project=project,
        day=day,
    )

    source_files = _source_files(
        selection,
        settings,
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
