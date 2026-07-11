from __future__ import annotations

import hashlib
import json
from pathlib import Path

from mps.models.import_manifest import (
    ImportManifest,
    ManifestFileEntry,
    manifest_path,
    new_session_id,
    utc_now_iso,
)

_CHUNK_SIZE = 65536


def file_sha256(path: str | Path) -> str:
    source = Path(path)
    digest = hashlib.sha256()

    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()


def create_manifest(
    project: str,
    day_session: str,
    mps_version: str,
    session_id: str | None = None,
) -> ImportManifest:
    return ImportManifest(
        session_id=session_id or new_session_id(),
        created_at=utc_now_iso(),
        project=project,
        day_session=day_session,
        mps_version=mps_version,
    )


def add_file_entry(
    manifest: ImportManifest,
    source_path: str | Path,
    destination_path: str | Path,
    action: str,
    status: str,
) -> ManifestFileEntry:
    source = Path(source_path)
    destination = Path(destination_path)

    entry = ManifestFileEntry(
        source_path=str(source),
        destination_path=str(destination),
        sha256=file_sha256(destination),
        action=action,
        status=status,
        bytes=destination.stat().st_size,
    )
    manifest.files.append(entry)
    return entry


def _write_manifest_json(
    manifest: ImportManifest,
    path: Path,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_manifest(
    manifest: ImportManifest,
    destination_root: str | Path,
) -> Path:
    path = manifest_path(destination_root, manifest.session_id)
    return _write_manifest_json(manifest, path)


def write_manifest_to_path(
    manifest: ImportManifest,
    path: str | Path,
) -> Path:
    return _write_manifest_json(manifest, Path(path))


def read_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_manifest(path: str | Path) -> ImportManifest:
    data = read_manifest(path)

    manifest = ImportManifest(
        session_id=data["session_id"],
        created_at=data["created_at"],
        project=data["project"],
        day_session=data["day_session"],
        mps_version=data["mps_version"],
    )

    for item in data.get("files", []):
        manifest.files.append(
            ManifestFileEntry(
                source_path=item["source_path"],
                destination_path=item["destination_path"],
                sha256=item["sha256"],
                action=item["action"],
                status=item["status"],
                bytes=item["bytes"],
            )
        )

    return manifest


def load_or_create_manifest(
    path: str | Path,
    *,
    project: str,
    day_session: str,
    mps_version: str,
    session_id: str,
) -> ImportManifest:
    manifest_file = Path(path)

    if manifest_file.exists():
        manifest = load_manifest(manifest_file)

        if manifest.session_id != session_id:
            raise ValueError(
                "Existing manifest belongs to a different import session"
            )

        return manifest

    return create_manifest(
        project=project,
        day_session=day_session,
        mps_version=mps_version,
        session_id=session_id,
    )
