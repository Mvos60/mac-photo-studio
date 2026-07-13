from __future__ import annotations

import json
from pathlib import Path

from mps.models.provenance_event import ProvenanceEvent
from mps.services.provenance_event_paths import event_path


def write_event(
    event: ProvenanceEvent,
    output_path: str | Path,
) -> Path:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            event.to_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output


def write_event_for_import(
    event: ProvenanceEvent,
    import_root: str | Path,
) -> Path:
    output = event_path(
        import_root,
        event.provenance_id,
        event.event_id,
    )

    return write_event(
        event,
        output,
    )


def load_event(
    input_path: str | Path,
) -> ProvenanceEvent:
    data = json.loads(
        Path(input_path).read_text(
            encoding="utf-8",
        )
    )

    return ProvenanceEvent.from_dict(data)
