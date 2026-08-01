from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from mps.services.provenance_index_writer import load_index

_CHUNK_SIZE = 65536
_ACTIVE_INDEX_NAME = "certificate_index.json"
_CULLING_SNAPSHOT_NAME = "certificate_index.before.json"


@dataclass(frozen=True, slots=True)
class ImportedPhotoRecord:
    sha256: str
    destination_path: str
    certificate_path: str
    session_id: str


class ImportedPhotoRegistry:
    def __init__(
        self,
        records: list[ImportedPhotoRecord],
    ) -> None:
        self._records = records
        self._by_sha256 = {
            record.sha256: record
            for record in records
        }

    @property
    def records(self) -> list[ImportedPhotoRecord]:
        return list(self._records)

    @property
    def hashes(self) -> set[str]:
        return set(self._by_sha256)

    def contains_hash(
        self,
        sha256: str,
    ) -> bool:
        return sha256 in self._by_sha256

    def find_by_hash(
        self,
        sha256: str,
    ) -> ImportedPhotoRecord | None:
        return self._by_sha256.get(sha256)


def file_sha256(
    path: str | Path,
) -> str:
    digest = hashlib.sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(_CHUNK_SIZE),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _is_active_index(path: Path) -> bool:
    return (
        path.name == _ACTIVE_INDEX_NAME
        and path.parent.name == "provenance"
    )


def _is_culling_snapshot(path: Path) -> bool:
    return (
        path.name == _CULLING_SNAPSHOT_NAME
        and ".mps_quarantine" in path.parts
        and "culling" in path.parts
    )


def _certificate_index_paths(
    photos_root: Path,
) -> list[Path]:
    if not photos_root.exists():
        return []

    paths = [
        path
        for name in (
            _ACTIVE_INDEX_NAME,
            _CULLING_SNAPSHOT_NAME,
        )
        for path in photos_root.rglob(name)
        if (
            path.is_file()
            and (
                _is_active_index(path)
                or _is_culling_snapshot(path)
            )
        )
    ]

    return sorted(
        paths,
        key=lambda path: (
            not _is_active_index(path),
            str(path),
        ),
    )


def load_imported_photo_registry(
    photos_root: str | Path,
) -> ImportedPhotoRegistry:
    root = Path(photos_root)

    records_by_sha256: dict[
        str,
        ImportedPhotoRecord,
    ] = {}

    for index_path in _certificate_index_paths(root):
        try:
            index = load_index(index_path)
        except (
            OSError,
            ValueError,
            KeyError,
        ):
            continue

        for entry in index.entries:
            record = ImportedPhotoRecord(
                sha256=entry.sha256,
                destination_path=entry.destination_path,
                certificate_path=entry.certificate_path,
                session_id=entry.session_id,
            )

            records_by_sha256.setdefault(
                record.sha256,
                record,
            )

    return ImportedPhotoRegistry(
        list(records_by_sha256.values())
    )
