from pathlib import Path

from mps.config import Settings
from mps.services.photo_provenance_verification import (
    verify_managed_photo,
)
from mps.services.provenance_file_verifier import (
    ProvenanceFileVerification,
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


def test_verify_managed_photo_finds_import_root(
    tmp_path,
    monkeypatch,
):
    photo = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
        / "DSC0001.ARW"
    )
    photo.parent.mkdir(parents=True)
    photo.write_bytes(b"raw photograph")

    provenance = photo.parent / "provenance"
    provenance.mkdir()
    (
        provenance / "certificate_index.json"
    ).write_text(
        '{"entries": []}\n',
        encoding="utf-8",
    )

    called = []

    def verify_file(*, import_root, photo_path):
        called.append(
            (
                Path(import_root),
                Path(photo_path),
            )
        )

        return ProvenanceFileVerification(
            trusted=True,
            path=Path(photo_path),
            actual_sha256="abc123",
        )

    monkeypatch.setattr(
        "mps.services.photo_provenance_verification."
        "verify_provenance_file",
        verify_file,
    )

    result = verify_managed_photo(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is True
    assert result.import_root == photo.parent
    assert called == [
        (
            photo.parent,
            photo,
        )
    ]


def test_verify_managed_photo_accepts_nested_derived_file(
    tmp_path,
    monkeypatch,
):
    import_root = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    photo = (
        import_root
        / "exports"
        / "print"
        / "DSC0001.jpg"
    )
    photo.parent.mkdir(parents=True)
    photo.write_bytes(b"exported photograph")

    provenance = import_root / "provenance"
    provenance.mkdir()
    (
        provenance / "certificate_index.json"
    ).write_text(
        '{"entries": []}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "mps.services.photo_provenance_verification."
        "verify_provenance_file",
        lambda *, import_root, photo_path: (
            ProvenanceFileVerification(
                trusted=True,
                path=Path(photo_path),
            )
        ),
    )

    result = verify_managed_photo(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is True
    assert result.import_root == import_root


def test_verify_managed_photo_reports_untrusted_result(
    tmp_path,
    monkeypatch,
):
    photo = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
        / "DSC0001.ARW"
    )
    photo.parent.mkdir(parents=True)
    photo.write_bytes(b"changed photograph")

    provenance = photo.parent / "provenance"
    provenance.mkdir()
    (
        provenance / "certificate_index.json"
    ).write_text(
        '{"entries": []}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "mps.services.photo_provenance_verification."
        "verify_provenance_file",
        lambda *, import_root, photo_path: (
            ProvenanceFileVerification(
                trusted=False,
                path=Path(photo_path),
                actual_sha256="changed-hash",
                errors=[
                    "Actual file SHA-256 does not match "
                    "recorded identity"
                ],
            )
        ),
    )

    result = verify_managed_photo(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert result.verification is not None
    assert result.errors == [
        "Actual file SHA-256 does not match recorded identity"
    ]


def test_verify_managed_photo_rejects_external_file(
    tmp_path,
):
    photo = tmp_path / "external" / "photo.jpg"
    photo.parent.mkdir()
    photo.write_bytes(b"external photograph")

    result = verify_managed_photo(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert result.import_root is None
    assert result.verification is None
    assert result.errors == [
        "Photo is not inside a managed provenance import"
    ]


def test_verify_managed_photo_rejects_missing_file(
    tmp_path,
):
    photo = tmp_path / "missing.ARW"

    result = verify_managed_photo(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert result.errors == [
        "Photo file does not exist"
    ]


def test_verify_managed_photo_rejects_directory(
    tmp_path,
):
    photo = tmp_path / "Photos_Master"
    photo.mkdir()

    result = verify_managed_photo(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.trusted is False
    assert result.errors == [
        "Photo path is not a file"
    ]
