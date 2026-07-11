from __future__ import annotations

import hashlib
from pathlib import Path

from mps.models.card import CardScanResult


_CHUNK_SIZE = 65536


def _scan_root(card: CardScanResult) -> Path:
    return card.dcim_path or card.root


def media_source_fingerprint(
    card: CardScanResult,
) -> str:
    """Build a deterministic read-only fingerprint of photo media contents."""

    scan_root = _scan_root(card)
    digest = hashlib.sha256()

    try:
        files = sorted(
            path
            for path in scan_root.rglob("*")
            if path.is_file()
        )
    except PermissionError:
        files = []

    for path in files:
        try:
            relative_path = path.relative_to(scan_root)
            size_bytes = path.stat().st_size
        except OSError:
            continue

        record = (
            f"{relative_path.as_posix()}\0"
            f"{size_bytes}\n"
        )

        digest.update(
            record.encode("utf-8")
        )

    return digest.hexdigest()
