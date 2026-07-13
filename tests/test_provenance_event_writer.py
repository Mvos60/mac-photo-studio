import json

from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.provenance_event_writer import (
    load_event,
    write_event,
    write_event_for_import,
)


def _event() -> ProvenanceEvent:
    return ProvenanceEvent(
        event_id="MPS-EVENT-001",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=ProvenanceEventType.EDIT,
        created_at="2026-07-13T10:00:00Z",
        input_sha256="raw-hash",
        output_sha256="master-hash",
        application="darktable",
        application_version="5.6.0",
        description="RAW development",
        metadata={
            "workflow": "RAW-first",
        },
    )


def test_write_event(tmp_path):
    output = tmp_path / "event.json"

    written = write_event(
        _event(),
        output,
    )

    assert written == output
    assert written.exists()

    data = json.loads(
        written.read_text(
            encoding="utf-8",
        )
    )

    assert data["event_id"] == "MPS-EVENT-001"
    assert data["provenance_id"] == "MPS-PROV-001"
    assert data["event_type"] == "edit"
    assert data["output_sha256"] == "master-hash"


def test_write_event_for_import_uses_event_tree(tmp_path):
    written = write_event_for_import(
        _event(),
        tmp_path,
    )

    assert written.name == "MPS-EVENT-001.json"
    assert written.parent.name == "MPS-PROV-001"
    assert written.parent.parent.name == "events"
    assert written.parent.parent.parent.name == "provenance"
    assert written.exists()


def test_load_event_restores_event(tmp_path):
    written = write_event_for_import(
        _event(),
        tmp_path,
    )

    loaded = load_event(written)

    assert loaded == _event()
    assert loaded.event_type is ProvenanceEventType.EDIT
    assert loaded.metadata == {
        "workflow": "RAW-first",
    }


def test_event_json_round_trip_preserves_context(tmp_path):
    original = _event()

    written = write_event_for_import(
        original,
        tmp_path,
    )

    loaded = load_event(written)

    assert loaded.event_id == original.event_id
    assert loaded.provenance_id == original.provenance_id
    assert loaded.session_id == original.session_id
    assert loaded.input_sha256 == original.input_sha256
    assert loaded.output_sha256 == original.output_sha256
    assert loaded.application == original.application
    assert (
        loaded.application_version
        == original.application_version
    )
    assert loaded.description == original.description
    assert loaded.metadata == original.metadata
