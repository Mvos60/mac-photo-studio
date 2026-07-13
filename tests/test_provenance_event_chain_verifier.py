from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_chain import ProvenanceEventChain
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_verifier import (
    verify_stored_event_chain,
)
from mps.services.provenance_event_chain_writer import (
    write_event_chain_for_import,
)


def _event(
    *,
    event_id: str,
    created_at: str,
    input_sha256: str,
    output_sha256: str | None,
) -> ProvenanceEvent:
    return ProvenanceEvent(
        event_id=event_id,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=ProvenanceEventType.EDIT,
        created_at=created_at,
        input_sha256=input_sha256,
        output_sha256=output_sha256,
    )


def test_verify_missing_stored_chain_is_valid_and_empty(
    tmp_path,
):
    result = verify_stored_event_chain(
        tmp_path,
        "MPS-PROV-MISSING",
    )

    assert result.provenance_id == "MPS-PROV-MISSING"
    assert result.valid is True
    assert result.event_count == 0
    assert result.errors == []


def test_verify_continuous_stored_chain(tmp_path):
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-001",
            created_at="2026-07-13T10:00:00Z",
            input_sha256="raw-hash",
            output_sha256="raw-hash",
        )
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-002",
            created_at="2026-07-13T11:00:00Z",
            input_sha256="raw-hash",
            output_sha256="master-hash",
        )
    )

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = verify_stored_event_chain(
        tmp_path,
        chain.provenance_id,
    )

    assert result.valid is True
    assert result.event_count == 2
    assert result.errors == []


def test_verify_broken_stored_chain(tmp_path):
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-001",
            created_at="2026-07-13T10:00:00Z",
            input_sha256="raw-hash",
            output_sha256="raw-hash",
        )
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-002",
            created_at="2026-07-13T11:00:00Z",
            input_sha256="wrong-hash",
            output_sha256="master-hash",
        )
    )

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = verify_stored_event_chain(
        tmp_path,
        chain.provenance_id,
    )

    assert result.valid is False
    assert result.event_count == 2
    assert result.errors == [
        "Hash continuity mismatch between "
        "MPS-EVENT-001 and MPS-EVENT-002"
    ]


def test_verification_result_is_detached_from_validator_errors(
    tmp_path,
):
    chain = ProvenanceEventChain(
        provenance_id="MPS-PROV-001",
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-001",
            created_at="2026-07-13T10:00:00Z",
            input_sha256="raw-hash",
            output_sha256=None,
        )
    )

    chain.add_event(
        _event(
            event_id="MPS-EVENT-002",
            created_at="2026-07-13T11:00:00Z",
            input_sha256="raw-hash",
            output_sha256="master-hash",
        )
    )

    write_event_chain_for_import(
        chain,
        tmp_path,
    )

    result = verify_stored_event_chain(
        tmp_path,
        chain.provenance_id,
    )

    assert result.valid is False
    assert result.errors == [
        "Event MPS-EVENT-001 has no output SHA-256"
    ]
