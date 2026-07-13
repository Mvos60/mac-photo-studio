from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_chain_writer import (
    load_event_chain,
)
from mps.services.provenance_event_service import (
    append_provenance_event,
)
from mps.services.provenance_event_writer import (
    write_event_for_import,
)


def _write_ingest_event(tmp_path) -> ProvenanceEvent:
    event = ProvenanceEvent(
        event_id="MPS-EVENT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=ProvenanceEventType.INGEST,
        created_at="2020-01-01T10:00:00Z",
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    write_event_for_import(
        event,
        tmp_path,
    )

    return event


def test_append_event_uses_chain_tip_as_input_hash(tmp_path):
    _write_ingest_event(tmp_path)

    result = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is True
    assert result.event is not None
    assert result.event.input_sha256 == "raw-hash"
    assert result.event.output_sha256 == "master-hash"


def test_append_event_records_application_context(tmp_path):
    _write_ingest_event(tmp_path)

    result = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
        application="darktable",
        application_version="5.6.0",
        description="RAW development",
        metadata={
            "workflow": "RAW-first",
        },
    )

    assert result.recorded is True
    assert result.event is not None
    assert result.event.application == "darktable"
    assert result.event.application_version == "5.6.0"
    assert result.event.description == "RAW development"
    assert result.event.metadata == {
        "workflow": "RAW-first",
    }


def test_append_event_persists_extended_history(tmp_path):
    _write_ingest_event(tmp_path)

    result = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is True

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert chain.event_count == 2

    ingest, edit = chain.ordered_events

    assert ingest.output_sha256 == edit.input_sha256
    assert edit.output_sha256 == "master-hash"


def test_append_event_requires_existing_history(tmp_path):
    result = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-MISSING",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is False
    assert result.event is None
    assert result.recording is None
    assert result.errors == [
        "Existing provenance event history is required"
    ]


def test_append_event_rejects_chain_tip_without_output_hash(
    tmp_path,
):
    event = ProvenanceEvent(
        event_id="MPS-EVENT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=ProvenanceEventType.INGEST,
        created_at="2020-01-01T10:00:00Z",
        input_sha256="raw-hash",
        output_sha256=None,
    )

    write_event_for_import(
        event,
        tmp_path,
    )

    result = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert result.recorded is False
    assert result.event is None
    assert result.errors == [
        "Event MPS-EVENT-001 has no output SHA-256"
    ]


def test_append_event_rejects_invalid_existing_chain(tmp_path):
    first = ProvenanceEvent(
        event_id="MPS-EVENT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=ProvenanceEventType.INGEST,
        created_at="2020-01-01T10:00:00Z",
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    second = ProvenanceEvent(
        event_id="MPS-EVENT-002",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        created_at="2020-01-01T11:00:00Z",
        input_sha256="wrong-hash",
        output_sha256="master-hash",
    )

    write_event_for_import(first, tmp_path)
    write_event_for_import(second, tmp_path)

    result = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-003",
        event_type=ProvenanceEventType.EXPORT,
        output_sha256="jpeg-hash",
    )

    assert result.recorded is False
    assert result.event is None
    assert result.recording is None
    assert result.errors == [
        "Existing provenance event chain is invalid",
        "Hash continuity mismatch between "
        "MPS-EVENT-001 and MPS-EVENT-002",
    ]


def test_append_multiple_events_follows_chain_tip(tmp_path):
    _write_ingest_event(tmp_path)

    edit = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-002",
        event_type=ProvenanceEventType.EDIT,
        output_sha256="master-hash",
    )

    assert edit.recorded is True

    export = append_provenance_event(
        import_root=tmp_path,
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-003",
        event_type=ProvenanceEventType.EXPORT,
        output_sha256="jpeg-hash",
    )

    assert export.recorded is True
    assert export.event is not None
    assert export.event.input_sha256 == "master-hash"
    assert export.event.output_sha256 == "jpeg-hash"

    chain = load_event_chain(
        tmp_path,
        "MPS-PROV-001",
    )

    assert [
        event.event_type
        for event in chain.ordered_events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
        ProvenanceEventType.EXPORT,
    ]
