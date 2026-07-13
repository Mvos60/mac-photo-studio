from mps.models.provenance_event import ProvenanceEvent


def test_create_provenance_event():
    event = ProvenanceEvent.create(
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type="ingest",
        input_sha256="abc123",
    )

    assert event.event_id.startswith("MPS-EVENT-")
    assert event.provenance_id == "MPS-PROV-001"
    assert event.session_id == "MPS-SESSION-001"
    assert event.event_type == "ingest"
    assert event.input_sha256 == "abc123"
    assert event.output_sha256 is None


def test_event_keeps_application_context():
    event = ProvenanceEvent.create(
        provenance_id="MPS-PROV-002",
        session_id="MPS-SESSION-002",
        event_type="edit",
        input_sha256="input-hash",
        output_sha256="output-hash",
        application="darktable",
        application_version="5.6.0",
        description="RAW development",
    )

    assert event.application == "darktable"
    assert event.application_version == "5.6.0"
    assert event.description == "RAW development"
    assert event.output_sha256 == "output-hash"


def test_event_keeps_metadata():
    event = ProvenanceEvent.create(
        provenance_id="MPS-PROV-003",
        session_id="MPS-SESSION-003",
        event_type="export",
        input_sha256="input-hash",
        output_sha256="output-hash",
        metadata={
            "format": "JPEG",
            "purpose": "print",
        },
    )

    assert event.metadata == {
        "format": "JPEG",
        "purpose": "print",
    }


def test_event_to_dict():
    event = ProvenanceEvent.create(
        provenance_id="MPS-PROV-004",
        session_id="MPS-SESSION-004",
        event_type="verify",
        input_sha256="abc123",
    )

    data = event.to_dict()

    assert data["event_id"] == event.event_id
    assert data["provenance_id"] == "MPS-PROV-004"
    assert data["event_type"] == "verify"
    assert data["input_sha256"] == "abc123"


def test_event_from_dict_restores_event():
    event = ProvenanceEvent.from_dict(
        {
            "event_id": "MPS-EVENT-001",
            "provenance_id": "MPS-PROV-001",
            "session_id": "MPS-SESSION-001",
            "event_type": "edit",
            "created_at": "2026-07-13T10:00:00Z",
            "input_sha256": "input-hash",
            "output_sha256": "output-hash",
            "application": "darktable",
            "application_version": "5.6.0",
            "description": "RAW development",
            "metadata": {
                "profile": "scene-referred",
            },
        }
    )

    assert event.event_id == "MPS-EVENT-001"
    assert event.event_type == "edit"
    assert event.application == "darktable"
    assert event.output_sha256 == "output-hash"
    assert event.metadata == {
        "profile": "scene-referred",
    }


def test_event_from_dict_uses_empty_metadata():
    event = ProvenanceEvent.from_dict(
        {
            "event_id": "MPS-EVENT-002",
            "provenance_id": "MPS-PROV-002",
            "session_id": "MPS-SESSION-002",
            "event_type": "verify",
            "created_at": "2026-07-13T10:00:00Z",
            "input_sha256": "abc123",
        }
    )

    assert event.metadata == {}
    assert event.output_sha256 is None


def test_event_requires_provenance_id():
    try:
        ProvenanceEvent.create(
            provenance_id="",
            session_id="MPS-SESSION-005",
            event_type="ingest",
            input_sha256="abc123",
        )
    except ValueError as error:
        assert str(error) == "provenance_id is required"
    else:
        raise AssertionError("ValueError was not raised")


def test_event_requires_session_id():
    try:
        ProvenanceEvent.create(
            provenance_id="MPS-PROV-006",
            session_id="",
            event_type="ingest",
            input_sha256="abc123",
        )
    except ValueError as error:
        assert str(error) == "session_id is required"
    else:
        raise AssertionError("ValueError was not raised")


def test_event_requires_event_type():
    try:
        ProvenanceEvent.create(
            provenance_id="MPS-PROV-007",
            session_id="MPS-SESSION-007",
            event_type="",
            input_sha256="abc123",
        )
    except ValueError as error:
        assert str(error) == "event_type is required"
    else:
        raise AssertionError("ValueError was not raised")


def test_event_requires_input_sha256():
    try:
        ProvenanceEvent.create(
            provenance_id="MPS-PROV-008",
            session_id="MPS-SESSION-008",
            event_type="ingest",
            input_sha256="",
        )
    except ValueError as error:
        assert str(error) == "input_sha256 is required"
    else:
        raise AssertionError("ValueError was not raised")


def test_event_accepts_controlled_event_type():
    from mps.models.provenance_event_type import ProvenanceEventType

    event = ProvenanceEvent.create(
        provenance_id="MPS-PROV-009",
        session_id="MPS-SESSION-009",
        event_type=ProvenanceEventType.EDIT,
        input_sha256="abc123",
    )

    assert event.event_type is ProvenanceEventType.EDIT
    assert event.to_dict()["event_type"] == "edit"


def test_event_rejects_unknown_event_type():
    try:
        ProvenanceEvent.create(
            provenance_id="MPS-PROV-010",
            session_id="MPS-SESSION-010",
            event_type="banana",
            input_sha256="abc123",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError was not raised")
