from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_recorder import (
    record_provenance_event,
)
from mps.services.provenance_event_writer import (
    write_event_for_import,
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


def _write_ingest_event(tmp_path) -> ProvenanceEvent:
    event = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    write_event_for_import(
        event,
        tmp_path,
    )

    return event


def test_record_event_appends_valid_event(tmp_path):
    _write_ingest_event(tmp_path)

    edit = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="raw-hash",
        output_sha256="master-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=edit,
    )

    assert result.recorded is True
    assert result.provenance_id == "MPS-PROV-001"
    assert result.event_id == "MPS-EVENT-002"
    assert result.event_count == 2
    assert result.event_path is not None
    assert result.event_path.exists()
    assert result.errors == []


def test_record_event_rejects_hash_discontinuity(tmp_path):
    _write_ingest_event(tmp_path)

    edit = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="wrong-hash",
        output_sha256="master-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=edit,
    )

    assert result.recorded is False
    assert result.event_count == 2
    assert result.event_path is None
    assert result.errors == [
        "Hash continuity mismatch between "
        "MPS-EVENT-001 and MPS-EVENT-002"
    ]

    assert not (
        tmp_path
        / "provenance"
        / "events"
        / "MPS-PROV-001"
        / "MPS-EVENT-002.json"
    ).exists()


def test_record_event_refuses_invalid_existing_chain(tmp_path):
    first = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
        input_sha256="raw-hash",
        output_sha256=None,
    )

    second = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T11:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="raw-hash",
        output_sha256="master-hash",
    )

    write_event_for_import(first, tmp_path)
    write_event_for_import(second, tmp_path)

    export = _event(
        event_id="MPS-EVENT-003",
        created_at="2026-07-13T12:00:00Z",
        event_type=ProvenanceEventType.EXPORT,
        input_sha256="master-hash",
        output_sha256="jpeg-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=export,
    )

    assert result.recorded is False
    assert result.event_count == 2
    assert result.errors == [
        "Existing provenance event chain is invalid",
        "Event MPS-EVENT-001 has no output SHA-256",
    ]


def test_record_event_rejects_existing_event_id(tmp_path):
    _write_ingest_event(tmp_path)

    duplicate = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=duplicate,
    )

    assert result.recorded is False
    assert result.event_count == 1
    assert result.errors == [
        "Event MPS-EVENT-001 already exists"
    ]


def test_record_first_event_for_new_chain(tmp_path):
    ingest = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.INGEST,
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=ingest,
    )

    assert result.recorded is True
    assert result.event_count == 1
    assert result.event_path is not None
    assert result.event_path.exists()


def test_record_first_event_rejects_non_ingest(tmp_path):
    edit = _event(
        event_id="MPS-EVENT-001",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="raw-hash",
        output_sha256="master-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=edit,
    )

    assert result.recorded is False
    assert result.event_count == 0
    assert result.event_path is None
    assert result.errors == [
        "Provenance event history must begin with ingest"
    ]

    assert not (
        tmp_path
        / "provenance"
        / "events"
        / "MPS-PROV-001"
        / "MPS-EVENT-001.json"
    ).exists()


def test_record_event_rejects_backdated_history(tmp_path):
    _write_ingest_event(tmp_path)

    edit = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T09:00:00Z",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="raw-hash",
        output_sha256="master-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=edit,
    )

    assert result.recorded is False
    assert result.event_count == 1
    assert result.event_path is None
    assert result.errors == [
        "Event MPS-EVENT-002 predates existing history"
    ]

    assert not (
        tmp_path
        / "provenance"
        / "events"
        / "MPS-PROV-001"
        / "MPS-EVENT-002.json"
    ).exists()


def test_record_event_allows_same_timestamp(tmp_path):
    _write_ingest_event(tmp_path)

    verify = _event(
        event_id="MPS-EVENT-002",
        created_at="2026-07-13T10:00:00Z",
        event_type=ProvenanceEventType.VERIFY,
        input_sha256="raw-hash",
        output_sha256="raw-hash",
    )

    result = record_provenance_event(
        import_root=tmp_path,
        event=verify,
    )

    assert result.recorded is True
    assert result.event_count == 2
    assert result.errors == []
