import json

import pytest
from pathlib import Path

from mps.config import Settings
from mps.models.import_destination_selection import ImportDestinationSelection
from mps.models.import_media_session import (
    ImportMediaSession,
    ImportMediaSessionDestination,
)
from mps.services.import_media_resume_validator import (
    can_resume_import_media_session,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
        }
    )


def _structured_session(
    tmp_path: Path,
    *,
    import_root: Path | None = None,
) -> ImportMediaSession:
    selection = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )
    return ImportMediaSession(
        session_id="MPS-SESSION-1",
        destination=ImportMediaSessionDestination(
            selection=selection,
            import_root=(
                import_root
                if import_root is not None
                else selection.destination_path(
                    tmp_path / "Photos_Master"
                )
            ),
        ),
    )


def _write_import_evidence(
    root: Path,
    *,
    session_id: str,
) -> None:
    root.mkdir(parents=True)

    destination = root / "DSC0001.ARW"
    destination.write_bytes(b"raw-data")

    import hashlib

    sha256 = hashlib.sha256(b"raw-data").hexdigest()

    manifest = {
        "session_id": session_id,
        "files": [
            {
                "source_path": "/media/card/DSC0001.ARW",
                "destination_path": str(destination),
                "sha256": sha256,
                "action": "copied",
                "status": "verified",
                "bytes": 8,
            }
        ],
    }

    manifest_path = root / "import_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    provenance = root / "provenance"
    provenance.mkdir()

    certificate_path = provenance / "MPS-CERT-1.json"

    certificate = {
        "session_id": session_id,
        "manifest_path": str(manifest_path),
        "destination_path": str(destination),
        "sha256": sha256,
    }

    certificate_path.write_text(
        json.dumps(certificate),
        encoding="utf-8",
    )

    index = {
        "entries": [
            {
                "session_id": session_id,
                "destination_path": str(destination),
                "certificate_path": str(certificate_path),
                "sha256": sha256,
            }
        ]
    }

    (
        provenance / "certificate_index.json"
    ).write_text(
        json.dumps(index),
        encoding="utf-8",
    )


def test_verified_same_session_can_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is True


def test_session_id_mismatch_blocks_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    session = ImportMediaSession(
        session_id="MPS-SESSION-OTHER",
    )

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is False


def test_missing_session_id_blocks_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    session = ImportMediaSession()

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is False


def test_tampered_destination_blocks_resume(tmp_path: Path):
    root = tmp_path / "import"

    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    (root / "DSC0001.ARW").write_bytes(
        b"tampered"
    )

    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is False


def test_matching_structured_session_can_resume(tmp_path: Path):
    session = _structured_session(tmp_path)
    root = session.destination.import_root
    _write_import_evidence(
        root,
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is True


def test_reconstructed_root_mismatch_blocks_structured_resume(
    tmp_path: Path,
):
    persisted_root = tmp_path / "different-root"
    session = _structured_session(
        tmp_path,
        import_root=persisted_root,
    )

    assert can_resume_import_media_session(
        session,
        persisted_root,
        settings=_settings(tmp_path),
    ) is False
    assert not persisted_root.exists()


def test_selected_root_mismatch_blocks_structured_resume(
    tmp_path: Path,
):
    session = _structured_session(tmp_path)
    selected_root = tmp_path / "selected-elsewhere"

    assert can_resume_import_media_session(
        session,
        selected_root,
        settings=_settings(tmp_path),
    ) is False
    assert not selected_root.exists()


def test_structured_root_outside_configured_library_is_rejected(
    tmp_path: Path,
    monkeypatch,
):
    outside_root = tmp_path / "outside" / "structured"
    session = _structured_session(
        tmp_path,
        import_root=outside_root,
    )
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator."
        "media_import_destination",
        lambda *args, **kwargs: outside_root,
    )

    assert can_resume_import_media_session(
        session,
        outside_root,
        settings=_settings(tmp_path),
    ) is False
    assert not outside_root.exists()


def test_changed_photos_root_blocks_structured_resume(
    tmp_path: Path,
):
    session = _structured_session(tmp_path)
    persisted_root = session.destination.import_root
    changed_settings = Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Moved_Photos"),
            },
        }
    )

    assert can_resume_import_media_session(
        session,
        persisted_root,
        settings=changed_settings,
    ) is False
    assert not (tmp_path / "Moved_Photos").exists()


def test_missing_manifest_returns_false(tmp_path: Path):
    root = tmp_path / "missing-manifest"
    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is False
    assert not root.exists()


def test_malformed_manifest_returns_false_without_mutation(
    tmp_path: Path,
):
    root = tmp_path / "import"
    root.mkdir()
    manifest_path = root / "import_manifest.json"
    original = b"{malformed"
    manifest_path.write_bytes(original)
    session = ImportMediaSession(
        session_id="MPS-SESSION-1",
    )

    assert can_resume_import_media_session(
        session,
        root,
        settings=_settings(tmp_path),
    ) is False
    assert manifest_path.read_bytes() == original


def test_unreadable_manifest_returns_false(
    tmp_path: Path,
    monkeypatch,
):
    root = tmp_path / "import"
    root.mkdir()
    (root / "import_manifest.json").write_text(
        "{}",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator.read_manifest",
        lambda path: (_ for _ in ()).throw(
            OSError("unreadable")
        ),
    )

    assert can_resume_import_media_session(
        ImportMediaSession(session_id="MPS-SESSION-1"),
        root,
        settings=_settings(tmp_path),
    ) is False


def test_unsafe_import_root_verification_blocks_resume(
    tmp_path: Path,
    monkeypatch,
):
    from types import SimpleNamespace

    root = tmp_path / "import"
    root.mkdir()
    (root / "import_manifest.json").write_text(
        json.dumps({"session_id": "MPS-SESSION-1"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator.verify_import_root",
        lambda current_root: SimpleNamespace(
            safe_to_release=False
        ),
    )

    assert can_resume_import_media_session(
        ImportMediaSession(session_id="MPS-SESSION-1"),
        root,
        settings=_settings(tmp_path),
    ) is False


def test_expected_path_resolution_failure_returns_false(
    tmp_path: Path,
    monkeypatch,
):
    session = _structured_session(tmp_path)

    def fail_resolve(self, *, strict=False):
        raise RuntimeError("symlink loop")

    monkeypatch.setattr(Path, "resolve", fail_resolve)

    assert can_resume_import_media_session(
        session,
        session.destination.import_root,
        settings=_settings(tmp_path),
    ) is False


def test_expected_damaged_verification_evidence_returns_false(
    tmp_path: Path,
    monkeypatch,
):
    root = tmp_path / "import"
    root.mkdir()
    manifest_path = root / "import_manifest.json"
    original = json.dumps(
        {"session_id": "MPS-SESSION-1"}
    ).encode("utf-8")
    manifest_path.write_bytes(original)
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator.verify_import_root",
        lambda current_root: (_ for _ in ()).throw(
            ValueError("damaged verification evidence")
        ),
    )

    assert can_resume_import_media_session(
        ImportMediaSession(session_id="MPS-SESSION-1"),
        root,
        settings=_settings(tmp_path),
    ) is False
    assert manifest_path.read_bytes() == original


def test_unexpected_destination_helper_type_error_propagates(
    tmp_path: Path,
    monkeypatch,
):
    session = _structured_session(tmp_path)
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator."
        "media_import_destination",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            TypeError("programming error")
        ),
    )

    with pytest.raises(TypeError, match="programming error"):
        can_resume_import_media_session(
            session,
            session.destination.import_root,
            settings=_settings(tmp_path),
        )


@pytest.mark.parametrize(
    "error",
    [
        AttributeError("programming error"),
        TypeError("programming error"),
    ],
)
def test_unexpected_verifier_programming_error_propagates(
    tmp_path: Path,
    monkeypatch,
    error: Exception,
):
    root = tmp_path / "import"
    root.mkdir()
    (root / "import_manifest.json").write_text(
        json.dumps({"session_id": "MPS-SESSION-1"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator.verify_import_root",
        lambda current_root: (_ for _ in ()).throw(error),
    )

    with pytest.raises(type(error), match="programming error"):
        can_resume_import_media_session(
            ImportMediaSession(session_id="MPS-SESSION-1"),
            root,
            settings=_settings(tmp_path),
        )


def test_invalid_verification_result_type_returns_false(
    tmp_path: Path,
    monkeypatch,
):
    root = tmp_path / "import"
    root.mkdir()
    (root / "import_manifest.json").write_text(
        json.dumps({"session_id": "MPS-SESSION-1"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "mps.services.import_media_resume_validator.verify_import_root",
        lambda current_root: object(),
    )

    assert can_resume_import_media_session(
        ImportMediaSession(session_id="MPS-SESSION-1"),
        root,
        settings=_settings(tmp_path),
    ) is False
