from __future__ import annotations

from pathlib import Path


def event_directory(
    import_root: str | Path,
    provenance_id: str,
) -> Path:
    return (
        Path(import_root)
        / "provenance"
        / "events"
        / provenance_id
    )


def event_path(
    import_root: str | Path,
    provenance_id: str,
    event_id: str,
) -> Path:
    return (
        event_directory(
            import_root,
            provenance_id,
        )
        / f"{event_id}.json"
    )
