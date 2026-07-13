from mps.services.extended_photo_provenance import (
    ProvenanceFileEventAppendResult,
    ProvenanceFileVerification,
    ProvenanceHistory,
    append_file_provenance_event,
    read_provenance_history,
    verify_provenance_file,
)
from mps.services.provenance_file_event_service import (
    ProvenanceFileEventAppendResult as InternalAppendResult,
)
from mps.services.provenance_file_event_service import (
    append_file_provenance_event as internal_append,
)
from mps.services.provenance_file_verifier import (
    ProvenanceFileVerification as InternalVerification,
)
from mps.services.provenance_file_verifier import (
    verify_provenance_file as internal_verify,
)
from mps.services.provenance_history import (
    ProvenanceHistory as InternalHistory,
)
from mps.services.provenance_history import (
    read_provenance_history as internal_read_history,
)


def test_public_boundary_exports_file_event_service():
    assert append_file_provenance_event is internal_append
    assert ProvenanceFileEventAppendResult is InternalAppendResult


def test_public_boundary_exports_file_verifier():
    assert verify_provenance_file is internal_verify
    assert ProvenanceFileVerification is InternalVerification


def test_public_boundary_exports_history_reader():
    assert read_provenance_history is internal_read_history
    assert ProvenanceHistory is InternalHistory


def test_public_boundary_declares_supported_interface():
    from mps.services import extended_photo_provenance

    assert extended_photo_provenance.__all__ == [
        "ProvenanceFileEventAppendResult",
        "ProvenanceFileVerification",
        "ProvenanceHistory",
        "append_file_provenance_event",
        "read_provenance_history",
        "verify_provenance_file",
    ]
