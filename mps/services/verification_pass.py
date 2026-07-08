import hashlib
from pathlib import Path
from typing import Any

from mps.models.verification_result import VerificationResult


_CHUNK_SIZE = 65536


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _entries_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    entries = manifest.get("entries")
    if entries is None:
        entries = manifest.get("files")
    if entries is None:
        return []
    return list(entries)


def _destination_from_entry(entry: dict[str, Any]) -> Path | None:
    for key in ("destination", "destination_path", "dst", "path"):
        value = entry.get(key)
        if value:
            return Path(value)
    return None


def _sha_from_entry(entry: dict[str, Any]) -> str | None:
    for key in ("sha256", "checksum", "destination_sha256", "hash"):
        value = entry.get(key)
        if value:
            return str(value)
    return None


def verify_manifest(manifest: dict[str, Any]) -> VerificationResult:
    entries = _entries_from_manifest(manifest)
    missing_files: list[Path] = []
    checksum_mismatches: list[Path] = []
    incomplete_entries = 0
    verified_count = 0

    for entry in entries:
        destination = _destination_from_entry(entry)
        expected_sha256 = _sha_from_entry(entry)

        if destination is None or expected_sha256 is None:
            incomplete_entries += 1
            continue

        if not destination.exists():
            missing_files.append(destination)
            continue

        actual_sha256 = _sha256(destination)
        if actual_sha256 != expected_sha256:
            checksum_mismatches.append(destination)
            continue

        verified_count += 1

    return VerificationResult(
        expected_count=len(entries),
        verified_count=verified_count,
        missing_files=missing_files,
        checksum_mismatches=checksum_mismatches,
        incomplete_entries=incomplete_entries,
    )
