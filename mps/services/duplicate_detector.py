import hashlib
from pathlib import Path

from mps.models.duplicate_result import DuplicateResult

_CHUNK_SIZE = 65536


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()


def check_duplicate(source_path: str | Path, destination_path: str | Path) -> DuplicateResult:
    source = Path(source_path)
    destination = Path(destination_path)

    if not destination.exists():
        return DuplicateResult(
            exists=False,
            identical=False,
            conflict=False,
        )

    source_hash = _sha256(source)
    destination_hash = _sha256(destination)

    if source_hash == destination_hash:
        return DuplicateResult(
            exists=True,
            identical=True,
            conflict=False,
        )

    return DuplicateResult(
        exists=True,
        identical=False,
        conflict=True,
    )
