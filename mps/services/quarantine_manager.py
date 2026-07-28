from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
from typing import Any

from mps.services.manifest_writer import load_manifest, write_manifest_to_path
from mps.services.provenance_index_paths import index_path
from mps.services.provenance_index_writer import load_index, write_index


@dataclass(frozen=True, slots=True)
class QuarantineItem:
    stem: str
    quarantine_root: Path
    created_at: datetime
    total_size: int
    raw_quarantine_path: Path | None
    original_raw_path: Path | None
    metadata_path: Path | None
    restorable: bool
    message: str


@dataclass(frozen=True, slots=True)
class RestoreResult:
    success: bool
    stem: str
    restored_raw: bool
    restored_provenance_items: int
    restored_manifest_entries: int
    restored_index_entries: int
    message: str


@dataclass(frozen=True, slots=True)
class DeleteResult:
    success: bool
    stem: str
    released_bytes: int
    message: str


def _directory_size(path: Path) -> int:
    total = 0
    try:
        children = path.rglob("*")
    except OSError:
        return 0

    for child in children:
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def _read_metadata(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("Quarantine metadata is not an object")
    return value


def _created_at(directory: Path, metadata: dict[str, Any] | None) -> datetime:
    if metadata is not None:
        value = metadata.get("created_at")
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
    try:
        return datetime.fromtimestamp(directory.stat().st_mtime)
    except OSError:
        return datetime.fromtimestamp(0)


def scan_quarantine(import_root: str | Path) -> tuple[QuarantineItem, ...]:
    root = Path(import_root).expanduser()
    culling_root = root / ".mps_quarantine" / "culling"
    if not culling_root.exists():
        return ()

    items: list[QuarantineItem] = []
    for directory in sorted(
        (entry for entry in culling_root.iterdir() if entry.is_dir()),
        key=lambda entry: entry.name.casefold(),
    ):
        metadata_path = directory / "quarantine.json"
        metadata: dict[str, Any] | None = None
        raw_quarantine_path: Path | None = None
        original_raw_path: Path | None = None
        restorable = False
        message = "Legacy quarantine item — permanent delete only"

        if metadata_path.exists():
            try:
                metadata = _read_metadata(metadata_path)
                raw = metadata.get("raw")
                if isinstance(raw, dict):
                    quarantined = raw.get("quarantine")
                    original = raw.get("original")
                    if isinstance(quarantined, str):
                        raw_quarantine_path = Path(quarantined).expanduser()
                    if isinstance(original, str):
                        original_raw_path = Path(original).expanduser()

                restorable = (
                    metadata.get("version") == 1
                    and isinstance(metadata.get("manifest_snapshot"), str)
                    and isinstance(metadata.get("index_snapshot"), str)
                    and isinstance(metadata.get("import_root"), str)
                )
                message = "Ready to restore" if restorable else "Metadata incomplete"
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                message = f"Metadata unreadable: {exc}"
        else:
            files = [entry for entry in directory.iterdir() if entry.is_file()]
            raw_candidates = [
                entry for entry in files
                if entry.suffix.casefold() in {".arw", ".raw", ".dng", ".nef", ".cr2", ".cr3"}
            ]
            if len(raw_candidates) == 1:
                raw_quarantine_path = raw_candidates[0]

        items.append(
            QuarantineItem(
                stem=directory.name,
                quarantine_root=directory,
                created_at=_created_at(directory, metadata),
                total_size=_directory_size(directory),
                raw_quarantine_path=raw_quarantine_path,
                original_raw_path=original_raw_path,
                metadata_path=metadata_path if metadata_path.exists() else None,
                restorable=restorable,
                message=message,
            )
        )

    return tuple(items)


def total_quarantine_size(items: tuple[QuarantineItem, ...]) -> int:
    return sum(item.total_size for item in items)


def _restore_failure(stem: str, message: str) -> RestoreResult:
    return RestoreResult(False, stem, False, 0, 0, 0, message)


def restore_quarantine_item(
    import_root: str | Path,
    item: QuarantineItem,
) -> RestoreResult:
    root = Path(import_root).expanduser()
    if not item.restorable or item.metadata_path is None:
        return _restore_failure(item.stem, "No safe restore metadata is available")

    try:
        metadata = _read_metadata(item.metadata_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _restore_failure(item.stem, f"Restore metadata unreadable: {exc}")

    metadata_root = Path(str(metadata.get("import_root", ""))).expanduser()
    if metadata_root != root:
        return _restore_failure(item.stem, "Metadata belongs to another import root")

    manifest_path = root / "import_manifest.json"
    certificate_index_path = index_path(root)
    manifest_snapshot = Path(str(metadata.get("manifest_snapshot", ""))).expanduser()
    index_snapshot = Path(str(metadata.get("index_snapshot", ""))).expanduser()

    for required in (manifest_path, certificate_index_path, manifest_snapshot, index_snapshot):
        if not required.exists():
            return _restore_failure(item.stem, f"Required restore file is missing: {required}")

    destination_paths = {
        Path(value).expanduser()
        for value in metadata.get("manifest_destination_paths", [])
        if isinstance(value, str)
    }
    provenance_ids = {
        value for value in metadata.get("provenance_ids", []) if isinstance(value, str)
    }

    move_pairs: list[tuple[Path, Path]] = []
    restored_raw = False
    raw = metadata.get("raw")
    if isinstance(raw, dict):
        original = raw.get("original")
        quarantined = raw.get("quarantine")
        if isinstance(original, str) and isinstance(quarantined, str):
            move_pairs.append((Path(quarantined).expanduser(), Path(original).expanduser()))
            restored_raw = True

    provenance_items = metadata.get("provenance_items", [])
    if isinstance(provenance_items, list):
        for value in provenance_items:
            if not isinstance(value, dict):
                continue
            original = value.get("original")
            quarantined = value.get("quarantine")
            if isinstance(original, str) and isinstance(quarantined, str):
                move_pairs.append((Path(quarantined).expanduser(), Path(original).expanduser()))

    for quarantined, original in move_pairs:
        if not quarantined.exists():
            return _restore_failure(item.stem, f"Quarantined item is missing: {quarantined}")
        if original.exists():
            return _restore_failure(item.stem, f"Original destination already exists: {original}")

    current_manifest = load_manifest(manifest_path)
    current_index = load_index(certificate_index_path)
    snapshot_manifest = load_manifest(manifest_snapshot)
    snapshot_index = load_index(index_snapshot)

    manifest_entries = [
        entry for entry in snapshot_manifest.files
        if Path(entry.destination_path).expanduser() in destination_paths
    ]
    index_entries = [
        entry for entry in snapshot_index.entries
        if entry.provenance_id in provenance_ids
    ]

    if len(manifest_entries) != len(destination_paths):
        return _restore_failure(item.stem, "Manifest snapshot is incomplete")
    if len(index_entries) != len(provenance_ids):
        return _restore_failure(item.stem, "Certificate index snapshot is incomplete")

    current_manifest_paths = {
        Path(entry.destination_path).expanduser() for entry in current_manifest.files
    }
    if current_manifest_paths.intersection(destination_paths):
        return _restore_failure(item.stem, "Manifest already contains a restored destination")

    current_ids = {entry.provenance_id for entry in current_index.entries}
    if current_ids.intersection(provenance_ids):
        return _restore_failure(item.stem, "Certificate index already contains restored provenance")

    original_manifest_files = list(current_manifest.files)
    original_index_entries = list(current_index.entries)
    completed_moves: list[tuple[Path, Path]] = []

    try:
        for quarantined, original in move_pairs:
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(quarantined), str(original))
            completed_moves.append((original, quarantined))

        current_manifest.files = [*current_manifest.files, *manifest_entries]
        current_index.entries = [*current_index.entries, *index_entries]
        write_manifest_to_path(current_manifest, manifest_path)
        write_index(current_index, certificate_index_path)
    except Exception:
        current_manifest.files = original_manifest_files
        current_index.entries = original_index_entries
        try:
            write_manifest_to_path(current_manifest, manifest_path)
            write_index(current_index, certificate_index_path)
        except Exception:
            pass

        for restored, quarantined in reversed(completed_moves):
            if restored.exists():
                quarantined.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(restored), str(quarantined))

        return _restore_failure(item.stem, "Restore transaction failed and was rolled back")

    shutil.rmtree(item.quarantine_root, ignore_errors=True)
    _remove_empty_parents(item.quarantine_root.parent, root / ".mps_quarantine")

    return RestoreResult(
        True,
        item.stem,
        restored_raw,
        len(move_pairs) - (1 if restored_raw else 0),
        len(manifest_entries),
        len(index_entries),
        "Quarantine item restored successfully",
    )


def _remove_empty_parents(start: Path, stop: Path) -> None:
    current = start
    while current != stop.parent and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        if current == stop:
            break
        current = current.parent


def permanently_delete_quarantine_item(
    import_root: str | Path,
    item: QuarantineItem,
) -> DeleteResult:
    root = Path(import_root).expanduser().resolve()
    allowed_root = (root / ".mps_quarantine" / "culling").resolve()

    try:
        item_root = item.quarantine_root.resolve()
    except OSError as exc:
        return DeleteResult(False, item.stem, 0, f"Quarantine path unreadable: {exc}")

    if item_root.parent != allowed_root:
        return DeleteResult(False, item.stem, 0, "Refusing to delete outside culling quarantine")
    if not item_root.exists() or not item_root.is_dir():
        return DeleteResult(False, item.stem, 0, "Quarantine item no longer exists")

    released = _directory_size(item_root)
    try:
        shutil.rmtree(item_root)
    except OSError as exc:
        return DeleteResult(False, item.stem, 0, f"Permanent delete failed: {exc}")

    _remove_empty_parents(allowed_root, root / ".mps_quarantine")
    return DeleteResult(True, item.stem, released, "Quarantine item permanently deleted")
