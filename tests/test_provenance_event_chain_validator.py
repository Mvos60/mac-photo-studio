from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_chain import ProvenanceEventChain
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_validator import (
    validate_provenance_event_chain,
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


def test_empty_chain_is_valid():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    result = validate_provenance_event_chain(chain)

    assert result.valid is True
    assert result.event_count == 0
    assert result.errors == []


def test_single_event_chain_is_valid():
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

    result = validate_provenance_event_chain(chain)

    assert result.valid is True
    assert result.event_count == 1


def test_continuous_chain_is_valid():
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

    result = validate_provenance_event_chain(chain)

    assert result.valid is True
    assert result.errors == []


def test_hash_continuity_mismatch_is_invalid():
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
            input_sha256="wrong-hash",
            output_sha256="master-hash",
        )
    )

    result = validate_provenance_event_chain(chain)

    assert result.valid is False
    assert result.errors == [
        "Hash continuity mismatch between "
        "MPS-EVENT-001 and MPS-EVENT-002"
    ]


def test_missing_previous_output_hash_is_invalid():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-001",
            created_at="2026-07-13T10:00:00Z",
            event_type=ProvenanceEventType.INGEST,
            input_sha256="raw-hash",
            output_sha256=None,
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

    result = validate_provenance_event_chain(chain)

    assert result.valid is False
    assert result.errors == [
        "Event MPS-EVENT-001 has no output SHA-256"
    ]


def test_validation_uses_chronological_event_order():
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    edit = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="raw-hash",
        output_sha256="master-hash",
    )

    ingest = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    chain.add_event(edit)
    chain.add_event(ingest)

    result = validate_provenance_event_chain(chain)

    assert result.valid is True
