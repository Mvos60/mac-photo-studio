from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_chain import ProvenanceEventChain
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
    write_event_chain_for_import,
)


def _event(
    *,
    event_id: str,
    created_at: str,
    event_type: ProvenanceEventType,
    input_sha256: str,
    output_sha256: str | None,
) -> ProvenanceEvent:
    return ProvenanceEvent(
        event_id=event_id,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=event_type,
        created_at=created_at,
        input_sha256=input_sha256,
        output_sha256=output_sha256,
    )


def _chain() -> ProvenanceEventChain:
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-002",
            created_at="2026-07-13T11:00:00Z",
            event_type=ProvenanceEventType.EDIT,
            input_sha256="raw-hash",
            output_sha256="master-hash",
        )
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-001",
            created_at="2026-07-13T10:00:00Z",
            event_type=ProvenanceEventType.INGEST,
            input_sha256="raw-hash",
            output_sha256="raw-hash",
        )
    )

    return chain


def test_write_event_chain_for_import(tmp_path):
    written = write_event_chain_for_import(
        _chain(),
        tmp_path,
    )

    assert len(written) == 2
    assert [
        path.name
        for path in written
    ] == [
        "MPS-EVENT-001.json",
        "MPS-EVENT-002.json",
    ]

    assert all(
        path.exists()
        for path in written
    )


def test_load_event_chain_restores_events(tmp_path):
    write_event_chain_for_import(
        _chain(),
        tmp_path,
    )

    loaded = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert loaded.provenance_id == "MPS-PROV-001"
    assert loaded.event_count == 2

    assert [
        event.event_id
        for event in loaded.ordered_events
    ] == [
        "MPS-EVENT-001",
        "MPS-EVENT-002",
    ]


def test_loaded_chain_preserves_hash_continuity(tmp_path):
    write_event_chain_for_import(
        _chain(),
        tmp_path,
    )

    loaded = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    ingest, edit = loaded.ordered_events

    assert ingest.output_sha256 == edit.input_sha256


def test_load_missing_event_chain_returns_empty_chain(
    tmp_path,
):
    loaded = load_event_chain(
        tmp_path,
        "MPS-PROV-MISSING",
    )

    assert loaded.provenance_id == "MPS-PROV-MISSING"
    assert loaded.event_count == 0
    assert loaded.events == []


def test_event_chain_round_trip_preserves_history(tmp_path):
    original = _chain()

    write_event_chain_for_import(
        original,
        tmp_path,
    )

    loaded = load_event_chain(
        tmp_path,
        original.provenance_id,
    )

    assert loaded.to_dict() == original.to_dict()
