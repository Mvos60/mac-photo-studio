from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_chain import ProvenanceEventChain
from mps.models.provenance_event_type import ProvenanceEventType


def _event(
    *,
    event_id: str,
    provenance_id: str = "MPS-PROV-001",
    created_at: str = "2026-07-13T10:00:00Z",
    event_type: ProvenanceEventType = ProvenanceEventType.INGEST,
    input_sha256: str = "input-hash",
    output_sha256: str | None = None,
) -> ProvenanceEvent:
    return ProvenanceEvent(
        event_id=event_id,
        provenance_id=provenance_id,
        session_id="MPS-SESSION-001",
        event_type=event_type,
        created_at=created_at,
        input_sha256=input_sha256,
        output_sha256=output_sha256,
    )


def test_new_event_chain_is_empty():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    assert chain.event_count == 0
    assert chain.events == []
    assert chain.ordered_events == []


def test_add_event_to_chain():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    event = _event(
        event_id="MPS-EVENT-001",
    )

    chain.add_event(event)

    assert chain.event_count == 1
    assert chain.events == [event]


def test_chain_rejects_other_provenance_id():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    event = _event(
        event_id="MPS-EVENT-002",
        provenance_id="MPS-PROV-OTHER",
    )

    try:
        chain.add_event(event)
    except ValueError as error:
        assert str(error) == (
            "event provenance_id does not match chain"
        )
    else:
        raise AssertionError("ValueError was not raised")


def test_ordered_events_are_sorted_by_time():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    later = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
    )

    earlier = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
    )

    chain.add_event(later)
    chain.add_event(earlier)

    assert chain.ordered_events == [
        earlier,
        later,
    ]


def test_chain_serializes_ordered_events():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    ingest = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
    )

    edit = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="input-hash",
        output_sha256="output-hash",
    )

    chain.add_event(edit)
    chain.add_event(ingest)

    data = chain.to_dict()

    assert data["provenance_id"] == "MPS-PROV-001"
    assert data["event_count"] == 2
    assert [
        event["event_id"]
        for event in data["events"]
    ] == [
        "MPS-EVENT-001",
        "MPS-EVENT-002",
    ]


def test_event_chain_can_represent_ingest_edit_export_history():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
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
            event_id="MPS-EVENT-003",
            created_at="2026-07-13T12:00:00Z",
            event_type=ProvenanceEventType.EXPORT,
            input_sha256="master-hash",
            output_sha256="jpeg-hash",
        )
    )

    assert chain.event_count == 3
    assert [
        event.event_type
        for event in chain.ordered_events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
        ProvenanceEventType.EXPORT,
    ]
