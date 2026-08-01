import hashlib
import json
from pathlib import Path

from mps.services.imported_photo_registry import (
    file_sha256,
    load_imported_photo_registry,
)


def _write_index(
    import_root: Path,
    *,
    sha256: str,
    destination_path: str,
    certificate_path: str,
    session_id: str,
) -> None:
    provenance = import_root / "provenance"
    provenance.mkdir(parents=True, exist_ok=True)

    data = {
        "entries": [
            {
                "camera_model": "ILCE-7M3",
                "certificate_id": "MPS-CERT-1",
                "certificate_path": certificate_path,
                "created_at": "2026-07-15T08:00:00+00:00",
                "destination_path": destination_path,
                "provenance_id": "MPS-PROV-1",
                "session_id": session_id,
                "sha256": sha256,
            }
        ]
    }

    (
        provenance / "certificate_index.json"
    ).write_text(
        json.dumps(data),
        encoding="utf-8",
    )


def test_file_sha256_returns_content_hash(
    tmp_path: Path,
):
    photo = tmp_path / "DSC0001.ARW"
    photo.write_bytes(b"raw-data")

    assert file_sha256(photo) == hashlib.sha256(
        b"raw-data"
    ).hexdigest()


def test_empty_photos_root_has_empty_registry(
    tmp_path: Path,
):
    registry = load_imported_photo_registry(
        tmp_path / "Photos_Master"
    )

    assert registry.records == []
    assert registry.hashes == set()


def test_registry_loads_certificate_index_entries(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"
    known_hash = hashlib.sha256(
        b"raw-data"
    ).hexdigest()

    _write_index(
        photos_root / "2026" / "Adriatic" / "03_Slovenia",
        sha256=known_hash,
        destination_path=(
            "/photos/2026/Adriatic/03_Slovenia/DSC0001.ARW"
        ),
        certificate_path=(
            "/photos/2026/Adriatic/03_Slovenia/"
            "provenance/MPS-CERT-1.json"
        ),
        session_id="MPS-SESSION-1",
    )

    registry = load_imported_photo_registry(
        photos_root
    )

    assert len(registry.records) == 1
    assert registry.contains_hash(known_hash)

    record = registry.find_by_hash(known_hash)

    assert record is not None
    assert record.session_id == "MPS-SESSION-1"
    assert record.destination_path.endswith(
        "DSC0001.ARW"
    )


def test_registry_combines_multiple_import_libraries(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"

    first_hash = hashlib.sha256(
        b"first"
    ).hexdigest()
    second_hash = hashlib.sha256(
        b"second"
    ).hexdigest()

    _write_index(
        photos_root / "2026" / "ProjectA" / "Session1",
        sha256=first_hash,
        destination_path="/photos/DSC0001.ARW",
        certificate_path="/certs/CERT-1.json",
        session_id="MPS-SESSION-1",
    )

    _write_index(
        photos_root / "2026" / "ProjectB" / "Session2",
        sha256=second_hash,
        destination_path="/photos/DSC0002.ARW",
        certificate_path="/certs/CERT-2.json",
        session_id="MPS-SESSION-2",
    )

    registry = load_imported_photo_registry(
        photos_root
    )

    assert len(registry.records) == 2
    assert registry.hashes == {
        first_hash,
        second_hash,
    }


def test_invalid_certificate_index_is_ignored(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"
    provenance = (
        photos_root
        / "2026"
        / "Broken"
        / "Session"
        / "provenance"
    )
    provenance.mkdir(parents=True)

    (
        provenance / "certificate_index.json"
    ).write_text(
        "not-json",
        encoding="utf-8",
    )

    registry = load_imported_photo_registry(
        photos_root
    )

    assert registry.records == []

def test_registry_loads_culling_snapshot_entries(
    tmp_path: Path,
):
    photos_root = tmp_path / "Photos_Master"
    import_root = (
        photos_root
        / "2026"
        / "Existing"
        / "Session"
    )
    quarantine = (
        import_root
        / ".mps_quarantine"
        / "culling"
        / "DSC0001"
    )
    quarantine.mkdir(parents=True)

    known_hash = hashlib.sha256(
        b"quarantined-photo"
    ).hexdigest()

    snapshot = {
        "entries": [
            {
                "camera_model": "ILCE-7M3",
                "certificate_id": "MPS-CERT-1",
                "certificate_path": (
                    "/photos/provenance/MPS-CERT-1.json"
                ),
                "created_at": "2026-07-15T08:00:00+00:00",
                "destination_path": (
                    "/photos/2026/Existing/Session/DSC0001.ARW"
                ),
                "provenance_id": "MPS-PROV-1",
                "session_id": "MPS-SESSION-1",
                "sha256": known_hash,
            }
        ]
    }

    (
        quarantine
        / "certificate_index.before.json"
    ).write_text(
        json.dumps(snapshot),
        encoding="utf-8",
    )

    registry = load_imported_photo_registry(
        photos_root
    )

    assert len(registry.records) == 1
    assert registry.contains_hash(known_hash)
    assert (
        registry.find_by_hash(known_hash)
        is not None
    )
