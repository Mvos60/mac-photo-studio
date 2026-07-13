from mps.models.provenance_event_type import ProvenanceEventType


def test_provenance_event_types_have_stable_values():
    assert ProvenanceEventType.INGEST == "ingest"
    assert ProvenanceEventType.EDIT == "edit"
    assert ProvenanceEventType.DERIVATIVE == "derivative"
    assert ProvenanceEventType.EXPORT == "export"
    assert ProvenanceEventType.VERIFY == "verify"
