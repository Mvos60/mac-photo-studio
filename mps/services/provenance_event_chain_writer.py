from __future__ import annotations

from pathlib import Path

from mps.models.provenance_event_chain import ProvenanceEventChain
from mps.services.provenance_event_paths import event_directory
from mps.services.provenance_event_writer import (
    load_event,
    write_event_for_import,
)


def write_event_chain_for_import(
    chain: ProvenanceEventChain,
    import_root: str | Path,
) -> list[Path]:
    return [
        write_event_for_import(
            event,
            import_root,
        )
        for event in chain.ordered_events
    ]


def load_event_chain(
    import_root: str | Path,
    provenance_id: str,
) -> ProvenanceEventChain:
    chain = ProvenanceEventChain(
        provenance_id=provenance_id,
    )

    directory = event_directory(
        import_root,
        provenance_id,
    )

    if not directory.exists():
        return chain

    for path in sorted(directory.glob("*.json")):
        chain.add_event(
            load_event(path)
        )

    return chain
