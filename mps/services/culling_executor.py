from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from mps.services.culling_analyzer import MissingImportedJpeg
from mps.services.imported_photo_registry import file_sha256
from mps.services.manifest_writer import (
    load_manifest,
    write_manifest_to_path,
)
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import (
    load_index,
    write_index,
)


@dataclass(frozen=True, slots=True)
class CullingExecutionResult:
    success: bool
    stem: str
    raw_quarantine_path: Path | None
    removed_manifest_entries: int
    removed_index_entries: int
    quarantined_provenance_items: int
    message: str


def _manifest_path(import_root: Path) -> Path:
    return import_root / "import_manifest.json"


def _quarantine_root(
    import_root: Path,
    stem: str,
) -> Path:
    return (
        import_root
        / ".mps_quarantine"
        / "culling"
        / stem
    )


def _provenance_ids(
    candidate: MissingImportedJpeg,
) -> set[str]:
    return {
        provenance_id
        for provenance_id in (
            candidate.jpeg_provenance_id,
            candidate.raw_provenance_id,
        )
        if provenance_id is not None
    }


def _destination_paths(
    candidate: MissingImportedJpeg,
) -> set[Path]:
    paths = {
        candidate.jpeg_path,
    }

    if candidate.raw_path is not None:
        paths.add(candidate.raw_path)

    return {
        path.expanduser()
        for path in paths
    }


def _verify_candidate(
    candidate: MissingImportedJpeg,
) -> str | None:
    if not candidate.is_orphan_raw_candidate:
        return "Candidate is not a verified orphan RAW"

    if candidate.raw_path is None:
        return "Candidate has no RAW path"

    if candidate.raw_sha256 is None:
        return "Candidate has no imported RAW hash"

    if candidate.jpeg_path.exists():
        return "JPG exists again; culling action aborted"

    try:
        current_hash = file_sha256(
            candidate.raw_path
        )
    except OSError:
        return "RAW could not be read"

    if current_hash != candidate.raw_sha256:
        return "RAW hash changed; culling action aborted"

    return None


def _move_provenance_item(
    source: Path,
    destination: Path,
) -> bool:
    if not source.exists():
        return False

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.move(
        str(source),
        str(destination),
    )

    return True


def execute_culling_candidate(
    import_root: str | Path,
    candidate: MissingImportedJpeg,
) -> CullingExecutionResult:
    root = Path(import_root).expanduser()

    verification_error = _verify_candidate(
        candidate
    )

    if verification_error is not None:
        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message=verification_error,
        )

    manifest_file = _manifest_path(root)
    certificate_index_file = index_path(root)

    if not manifest_file.exists():
        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message="Import manifest is missing",
        )

    if not certificate_index_file.exists():
        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message="Certificate index is missing",
        )

    manifest = load_manifest(manifest_file)
    certificate_index = load_index(
        certificate_index_file
    )

    destination_paths = _destination_paths(
        candidate
    )
    provenance_ids = _provenance_ids(
        candidate
    )

    original_manifest_files = list(
        manifest.files
    )
    original_index_entries = list(
        certificate_index.entries
    )

    manifest.files = [
        entry
        for entry in manifest.files
        if (
            Path(entry.destination_path).expanduser()
            not in destination_paths
        )
    ]

    removed_manifest_entries = (
        len(original_manifest_files)
        - len(manifest.files)
    )

    removed_index_entries = [
        entry
        for entry in certificate_index.entries
        if entry.provenance_id in provenance_ids
    ]

    certificate_index.entries = [
        entry
        for entry in certificate_index.entries
        if entry.provenance_id not in provenance_ids
    ]

    if removed_manifest_entries != 2:
        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message=(
                "Expected exactly two manifest entries "
                "for RAW/JPG pair"
            ),
        )

    if len(removed_index_entries) != 2:
        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message=(
                "Expected exactly two certificate index "
                "entries for RAW/JPG pair"
            ),
        )

    quarantine_root = _quarantine_root(
        root,
        candidate.stem,
    )

    if quarantine_root.exists():
        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message="Culling quarantine already exists",
        )

    raw_quarantine_path = (
        quarantine_root
        / candidate.raw_path.name
    )

    quarantined_items: list[
        tuple[Path, Path]
    ] = []

    try:
        quarantine_root.mkdir(
            parents=True,
            exist_ok=False,
        )

        raw_quarantine_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.move(
            str(candidate.raw_path),
            str(raw_quarantine_path),
        )

        quarantined_items.append(
            (
                candidate.raw_path,
                raw_quarantine_path,
            )
        )

        for entry in removed_index_entries:
            certificate_path = Path(
                entry.certificate_path
            ).expanduser()

            certificate_destination = (
                quarantine_root
                / "provenance"
                / "certificates"
                / certificate_path.name
            )

            if _move_provenance_item(
                certificate_path,
                certificate_destination,
            ):
                quarantined_items.append(
                    (
                        certificate_path,
                        certificate_destination,
                    )
                )

            event_directory = (
                root
                / "provenance"
                / "events"
                / entry.provenance_id
            )

            event_destination = (
                quarantine_root
                / "provenance"
                / "events"
                / entry.provenance_id
            )

            if _move_provenance_item(
                event_directory,
                event_destination,
            ):
                quarantined_items.append(
                    (
                        event_directory,
                        event_destination,
                    )
                )

        write_manifest_to_path(
            manifest,
            manifest_file,
        )

        write_index(
            certificate_index,
            certificate_index_file,
        )

    except Exception:
        manifest.files = original_manifest_files
        certificate_index.entries = (
            original_index_entries
        )

        try:
            write_manifest_to_path(
                manifest,
                manifest_file,
            )
            write_index(
                certificate_index,
                certificate_index_file,
            )
        except Exception:
            pass

        for original, quarantined in reversed(
            quarantined_items
        ):
            if quarantined.exists():
                original.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                shutil.move(
                    str(quarantined),
                    str(original),
                )

        if quarantine_root.exists():
            shutil.rmtree(
                quarantine_root,
                ignore_errors=True,
            )

        return CullingExecutionResult(
            success=False,
            stem=candidate.stem,
            raw_quarantine_path=None,
            removed_manifest_entries=0,
            removed_index_entries=0,
            quarantined_provenance_items=0,
            message="Culling transaction failed and was rolled back",
        )

    return CullingExecutionResult(
        success=True,
        stem=candidate.stem,
        raw_quarantine_path=raw_quarantine_path,
        removed_manifest_entries=removed_manifest_entries,
        removed_index_entries=len(
            removed_index_entries
        ),
        quarantined_provenance_items=(
            len(quarantined_items) - 1
        ),
        message="Culling candidate quarantined successfully",
    )
