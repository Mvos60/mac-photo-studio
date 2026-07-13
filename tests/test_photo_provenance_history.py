from pathlib import Path

from mps.config import Settings
from mps.models.provenance_event import ProvenanceEvent
from mps.models.provenance_event_type import ProvenanceEventType
from mps.services.photo_provenance_history import (
    read_managed_photo_history,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
)
from mps.services.provenance_file_verifier import (
    ProvenanceFileVerification,
)
from mps.services.provenance_history import ProvenanceHistory
from mps.services.provenance_identity_resolver import (
    ProvenanceIdentityResolution,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
        }
    )


def _event(
    event_type: ProvenanceEventType,
) -> ProvenanceEvent:
    return ProvenanceEvent(
        event_id=f"MPS-EVENT-{event_type.value}",
        provenance_id="MPS-PROV-001",
        session_id="MPS-SESSION-001",
        event_type=event_type,
        created_at="2020-01-01T10:00:00Z",
        input_sha256="input-hash",
        output_sha256="output-hash",
    )


def _verification(photo: Path, trusted: bool = True):
    return PhotoProvenanceVerification(
        photo_path=photo,
        trusted=trusted,
        import_root=photo.parent,
        verification=ProvenanceFileVerification(
            trusted=trusted,
            path=photo,
            identity=ProvenanceIdentityResolution(
                resolved=True,
                provenance_id="MPS-PROV-001",
            ),
        ),
    )


def test_read_managed_photo_history_returns_events(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "verify_managed_photo",
        lambda *, settings, photo_path: (
            _verification(Path(photo_path))
        ),
    )

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "read_provenance_history",
        lambda *, import_root, provenance_id: (
            ProvenanceHistory(
                provenance_id=provenance_id,
                valid=True,
                events=(
                    _event(ProvenanceEventType.INGEST),
                    _event(ProvenanceEventType.EDIT),
                ),
            )
        ),
    )

    result = read_managed_photo_history(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is True
    assert [
        event.event_type
        for event in result.events
    ] == [
        ProvenanceEventType.INGEST,
        ProvenanceEventType.EDIT,
    ]


def test_read_managed_photo_history_keeps_untrusted_status(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "verify_managed_photo",
        lambda *, settings, photo_path: (
            _verification(
                Path(photo_path),
                trusted=False,
            )
        ),
    )

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "read_provenance_history",
        lambda *, import_root, provenance_id: (
            ProvenanceHistory(
                provenance_id=provenance_id,
                valid=True,
                events=(
                    _event(ProvenanceEventType.INGEST),
                ),
            )
        ),
    )

    result = read_managed_photo_history(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert len(result.events) == 1


def test_read_managed_photo_history_reports_invalid_history(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "verify_managed_photo",
        lambda *, settings, photo_path: (
            _verification(Path(photo_path))
        ),
    )

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "read_provenance_history",
        lambda *, import_root, provenance_id: (
            ProvenanceHistory(
                provenance_id=provenance_id,
                valid=False,
                errors=[
                    "Hash continuity mismatch"
                ],
            )
        ),
    )

    result = read_managed_photo_history(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert result.errors == [
        "Hash continuity mismatch"
    ]


def test_read_managed_photo_history_returns_verification_errors(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "UNKNOWN.JPG"

    monkeypatch.setattr(
        "mps.services.photo_provenance_history."
        "verify_managed_photo",
        lambda *, settings, photo_path: (
            PhotoProvenanceVerification(
                photo_path=Path(photo_path),
                trusted=False,
                errors=[
                    "Photo is not inside a managed provenance import"
                ],
            )
        ),
    )

    result = read_managed_photo_history(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert result.events == ()
    assert result.history is None
    assert result.errors == [
        "Photo is not inside a managed provenance import"
    ]
