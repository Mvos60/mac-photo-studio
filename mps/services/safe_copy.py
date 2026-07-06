from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CopyResult:
    """Result of one safe file copy operation."""

    success: bool
    source: Path
    destination: Path
    size_bytes: int
    checksum: str | None
    message: str


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def copy_one_file(source: Path, destination: Path) -> CopyResult:
    """Copy one file safely and verify size and checksum.

    The source file is never modified.
    Existing destination files are never overwritten.
    """

    source = source.expanduser()
    destination = destination.expanduser()

    if not source.exists():
        return CopyResult(False, source, destination, 0, None, "Source file does not exist.")

    if not source.is_file():
        return CopyResult(False, source, destination, 0, None, "Source is not a file.")

    if destination.exists():
        return CopyResult(False, source, destination, 0, None, "Destination already exists; refusing to overwrite.")

    destination.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source, destination)

    source_size = source.stat().st_size
    destination_size = destination.stat().st_size

    if source_size != destination_size:
        return CopyResult(False, source, destination, destination_size, None, "Size verification failed.")

    source_checksum = sha256_file(source)
    destination_checksum = sha256_file(destination)

    if source_checksum != destination_checksum:
        return CopyResult(False, source, destination, destination_size, destination_checksum, "Checksum verification failed.")

    return CopyResult(True, source, destination, destination_size, destination_checksum, "Copy verified.")
