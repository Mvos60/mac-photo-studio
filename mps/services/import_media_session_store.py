from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from mps.models.import_destination_selection import (
    ImportDestinationSelection,
)
from mps.models.import_media_session import (
    ImportMediaSession,
    ImportMediaSessionDestination,
)


_DESTINATION_FIELDS = {
    "year",
    "month_day",
    "project",
    "description",
    "import_root",
}


def _load_destination(
    data: dict,
) -> ImportMediaSessionDestination | None:
    if "destination" not in data:
        return None

    raw = data["destination"]

    if not isinstance(raw, dict):
        raise ValueError(
            "Import session destination must be an object"
        )

    missing = _DESTINATION_FIELDS.difference(raw)

    if missing:
        fields = ", ".join(sorted(missing))
        raise ValueError(
            "Import session destination is missing: "
            f"{fields}"
        )

    import_root = raw["import_root"]

    if (
        not isinstance(import_root, str)
        or not import_root
        or "\x00" in import_root
    ):
        raise ValueError(
            "Import session destination import_root "
            "must be a non-empty path string"
        )

    try:
        selection = ImportDestinationSelection(
            year=raw["year"],
            month_day=raw["month_day"],
            project=raw["project"],
            description=raw["description"],
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid import session destination: {exc}"
        ) from exc

    return ImportMediaSessionDestination(
        selection=selection,
        import_root=Path(import_root),
    )


def save_import_media_session(
    session: ImportMediaSession,
    path: str | Path,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "session_id": session.session_id,
        "source_fingerprints": sorted(
            session.source_fingerprints
        ),
        "processed_source_files": [
            str(path)
            for path in session.processed_source_files
        ],
    }

    if session.destination is not None:
        selection = session.destination.selection
        data["destination"] = {
            "year": selection.year,
            "month_day": selection.month_day,
            "project": selection.project,
            "description": selection.description,
            "import_root": str(
                session.destination.import_root
            ),
        }

    contents = json.dumps(
        data,
        indent=2,
        sort_keys=True,
    ) + "\n"
    temporary = output.with_name(
        f".{output.name}.{uuid4().hex}.tmp"
    )

    try:
        with temporary.open(
            "x",
            encoding="utf-8",
        ) as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())

        temporary.replace(output)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return output


def load_import_media_session(
    path: str | Path,
) -> ImportMediaSession:
    data = json.loads(
        Path(path).read_text(encoding="utf-8")
    )

    return ImportMediaSession(
        session_id=data.get("session_id"),
        destination=_load_destination(data),
        sources=[],
        source_fingerprints=set(
            data.get("source_fingerprints", [])
        ),
        processed_source_files=[
            Path(value)
            for value in data.get(
                "processed_source_files",
                [],
            )
        ],
    )
