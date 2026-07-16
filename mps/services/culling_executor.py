from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from mps.services.culling_analyzer import (
    CullingCandidateStatus,
    MissingImportedJpeg,
)
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


def _candidate_provenance_ids(
    candidate: MissingImportedJpeg,
) -> set[str]:
    if (
        candidate.status
        == CullingCandidateStatus.CULL_CANDIDATE
    ):
        values = (
            candidate.jpeg_provenance_id,
            candidate.raw_provenance_id,
        )
    elif (
        candidate.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    ):
        values = (
            candidate.jpeg_provenance_id,
        )
    else:
        values = ()

    return {
        value
        for value in values
        if value is not None
    }


def _candidate_destination_paths(
    candidate: MissingImportedJpeg,
) -> set[Path]:
    if (
        candidate.status
        == CullingCandidateStatus.CULL_CANDIDATE
    ):
        values = [
            candidate.jpeg_path,
        ]

        if candidate.raw_path is not None:
            values.append(candidate.raw_path)

    elif (
        candidate.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    ):
        values = [
            candidate.jpeg_path,
        ]

    else:
        values = []

    return {
        path.expanduser()
        for path in values
    }


def _expected_entry_count(
    candidate: MissingImportedJpeg,
) -> int:
    if (
        candidate.status
        == CullingCandidateStatus.CULL_CANDIDATE
    ):
        return 2

    if (
        candidate.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    ):
        return 1

    return 0


def _verify_candidate(
    candidate: MissingImportedJpeg,
) -> str | None:
    if candidate.jpeg_path.exists():
        return "JPG exists again; culling action aborted"

    if (
        candidate.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    ):
        if candidate.raw_path is not None:
            return (
                "JPG-only cleanup candidate unexpectedly "
                "contains an imported RAW"
            )

        return None

    if (
        candidate.status
        != CullingCandidateStatus.CULL_CANDIDATE
    ):
        return "Candidate is not actionable"

    if candidate.raw_path is None:
        return "Candidate has no RAW path"

    if candidate.raw_sha256 is None:
        return "Candidate has no imported RAW hash"

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


def _result_failure(
    candidate: MissingImportedJpeg,
    message: str,
) -> CullingExecutionResult:
    return CullingExecutionResult(
        success=False,
        stem=candidate.stem,
        raw_quarantine_path=None,
        removed_manifest_entries=0,
        removed_index_entries=0,
        quarantined_provenance_items=0,
        message=message,
    )


def execute_culling_candidate(
    import_root: str | Path,
    candidate: MissingImportedJpeg,
) -> CullingExecutionResult:
    root = Path(import_root).expanduser()

    verification_error = _verify_candidate(
        candidate
    )

    if verification_error is not None:
        return _result_failure(
            candidate,
            verification_error,
        )

    manifest_file = _manifest_path(root)
    certificate_index_file = index_path(root)

    if not manifest_file.exists():
        return _result_failure(
            candidate,
            "Import manifest is missing",
        )

    if not certificate_index_file.exists():
        return _result_failure(
            candidate,
            "Certificate index is missing",
        )

    manifest = load_manifest(manifest_file)
    certificate_index = load_index(
        certificate_index_file
    )

    destination_paths = (
        _candidate_destination_paths(
            candidate
        )
    )
    provenance_ids = (
        _candidate_provenance_ids(
            candidate
        )
    )
    expected_count = _expected_entry_count(
        candidate
    )

    original_manifest_files = list(
        manifest.files
    )
    original_index_entries = list(
        certificate_index.entries
    )

    removed_manifest_entries = [
        entry
        for entry in manifest.files
        if (
            Path(
                entry.destination_path
            ).expanduser()
            in destination_paths
        )
    ]

    remaining_manifest_entries = [
        entry
        for entry in manifest.files
        if (
            Path(
                entry.destination_path
            ).expanduser()
            not in destination_paths
        )
    ]

    removed_index_entries = [
        entry
        for entry in certificate_index.entries
        if entry.provenance_id in provenance_ids
    ]

    remaining_index_entries = [
        entry
        for entry in certificate_index.entries
        if entry.provenance_id not in provenance_ids
    ]

    if (
        len(removed_manifest_entries)
        != expected_count
    ):
        return _result_failure(
            candidate,
            (
                "Expected exactly "
                f"{expected_count} manifest "
                "entry or entries for this action"
            ),
        )

    if (
        len(removed_index_entries)
        != expected_count
    ):
        return _result_failure(
            candidate,
            (
                "Expected exactly "
                f"{expected_count} certificate index "
                "entry or entries for this action"
            ),
        )

    quarantine_root = _quarantine_root(
        root,
        candidate.stem,
    )

    if quarantine_root.exists():
        return _result_failure(
            candidate,
            "Culling quarantine already exists",
        )

    raw_quarantine_path: Path | None = None

    quarantined_items: list[
        tuple[Path, Path]
    ] = []

    try:
        quarantine_root.mkdir(
            parents=True,
            exist_ok=False,
        )

        if (
            candidate.status
            == CullingCandidateStatus.CULL_CANDIDATE
        ):
            if candidate.raw_path is None:
                raise RuntimeError(
                    "Verified RAW path is missing"
                )

            raw_quarantine_path = (
                quarantine_root
                / candidate.raw_path.name
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

        manifest.files = (
            remaining_manifest_entries
        )
        certificate_index.entries = (
            remaining_index_entries
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
        manifest.files = (
            original_manifest_files
        )
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

        return _result_failure(
            candidate,
            (
                "Culling transaction failed "
                "and was rolled back"
            ),
        )

    if (
        candidate.status
        == CullingCandidateStatus.CULL_CANDIDATE
    ):
        message = (
            "Culling candidate quarantined successfully"
        )
    else:
        message = (
            "Deleted JPG provenance cleaned up successfully"
        )

    raw_item_count = (
        1
        if raw_quarantine_path is not None
        else 0
    )

    return CullingExecutionResult(
        success=True,
        stem=candidate.stem,
        raw_quarantine_path=raw_quarantine_path,
        removed_manifest_entries=len(
            removed_manifest_entries
        ),
        removed_index_entries=len(
            removed_index_entries
        ),
        quarantined_provenance_items=(
            len(quarantined_items)
            - raw_item_count
        ),
        message=message,
    )
