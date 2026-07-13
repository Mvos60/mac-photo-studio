from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_chain import ProvenanceEventChain
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_writer import (
    write_event_chain_for_import,
)
from mps.services.provenance_history import (
    read_provenance_history,
)


def _event(
    *,
    event_id: str,
    created_at: str,
    event_type: ProvenanceEventType,
    input_sha256: str,
    output_sha256: str,
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


def test_read_provenance_history_returns_ordered_events(
    tmp_path,
):
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    edit = _event(
        event_id="MPS-EVENT-002",
        created_at="2020-01-01T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="raw-hash",
        output_sha256="master-hash",
    )

    ingest = _event(
        event_id="MPS-EVENT-001",
        created_at="2020-01-01T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    chain.add_event(edit)
    chain.add_event(ingest)

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = read_provenance_history(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
    )

    assert result.valid is True
    assert [
        event.event_type
        for event in result.events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
    ]
    assert result.errors == []


def test_read_provenance_history_preserves_event_context(
    tmp_path,
):
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        ProvenanceEvent(
            event_id="MPS-EVENT-001",
            provenance_id="MPS-PROV-001",
            session_id="MPS-SESSION-001",
            event_type=ProvenanceEventType.INGEST,
            created_at="2020-01-01T10:00:00Z",
            input_sha256="raw-hash",
            output_sha256="raw-hash",
            application="Mac Photo Studio",
            application_version="0.2.0-dev",
            description="Verified camera media ingest",
            metadata={
                "camera_model": "ILCE-7M3",
            },
        )
    )

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = read_provenance_history(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
    )

    event = result.events[0]

    assert event.application == "Mac Photo Studio"
    assert event.description == "Verified camera media ingest"
    assert event.metadata["camera_model"] == "ILCE-7M3"


def test_read_provenance_history_reports_broken_chain(
    tmp_path,
):
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-001",
            created_at="2020-01-01T10:00:00Z",
            event_type=ProvenanceEventType.INGEST,
            input_sha256="raw-hash",
            output_sha256="raw-hash",
        )
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-002",
            created_at="2020-01-01T11:00:00Z",
            event_type=ProvenanceEventType.EDIT,
            input_sha256="wrong-hash",
            output_sha256="master-hash",
        )
    )

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = read_provenance_history(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
    )

    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].startswith(
        "Hash continuity mismatch between "
    )


def test_read_provenance_history_reports_empty_chain(
    tmp_path,
):
    result = read_provenance_history(
        import_root=tmp_path,
        provenance_id="MPS-PROV-MISSING",
    )

    assert result.valid is False
    assert result.events == ()
    assert result.errors == [
        "Provenance event chain is empty"
    ]
