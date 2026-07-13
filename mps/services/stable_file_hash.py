from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mps.services.safe_copy import sha256_file


@dataclass(slots=True, frozen=True)
class StableFileHashResult:
    stable: bool
    path: Path
    sha256: str | None = None
    errors: tuple[str, ...] = ()


def stable_file_sha256(
    path: str | Path,
) -> StableFileHashResult:
    file_path = Path(path).expanduser()

    if not file_path.exists():
        return StableFileHashResult(
            stable=False,
            path=file_path,
            errors=(
                "File does not exist",
            ),
        )

    if not file_path.is_file():
        return StableFileHashResult(
            stable=False,
            path=file_path,
            errors=(
                "Path is not a file",
            ),
        )

    before = file_path.stat()
    first_sha256 = sha256_file(file_path)
    between = file_path.stat()
    second_sha256 = sha256_file(file_path)
    after = file_path.stat()

    file_state_changed = (
        before.st_size != between.st_size
        or before.st_mtime_ns != between.st_mtime_ns
        or between.st_size != after.st_size
        or between.st_mtime_ns != after.st_mtime_ns
    )

    if file_state_changed or first_sha256 != second_sha256:
        return StableFileHashResult(
            stable=False,
            path=file_path,
            errors=(
                "File changed while SHA-256 was being calculated",
            ),
        )

    return StableFileHashResult(
        stable=True,
        path=file_path,
        sha256=second_sha256,
        errors=(),
    )
