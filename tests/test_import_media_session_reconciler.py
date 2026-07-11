import json
from pathlib import Path

from mps.config import Settings
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_media_session import ImportMediaSession
from mps.services.import_media_batch_processor import (
    process_import_media_batch,
)
from mps.services.import_media_session_reconciler import (
    reconcile_import_media_session,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )


def _write_photo(
    root: Path,
    name: str,
    content: bytes,
) -> None:
    directory = root / "DCIM" / "100MSDCF"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(content)


def _card(
    root: Path,
    *,
    raw: int = 0,
    jpeg: int = 0,
) -> CardScanResult:
    return CardScanResult(
        root=root,
        dcim_path=root / "DCIM",
        raw_count=raw,
        jpeg_count=jpeg,
        heif_count=0,
        video_count=0,
        pair_count=min(raw, jpeg),
        orphan_raw_count=max(raw - jpeg, 0),
        orphan_jpeg_count=max(jpeg - raw, 0),
        other_count=0,
        total_size_bytes=0,
    )


def _sequential_import(tmp_path: Path):
    reader = tmp_path / "reader"
    session = ImportMediaSession()
    settings = _settings(tmp_path)
    session_id = "MPS-SESSION-SEQUENTIAL"

    _write_photo(
        reader,
        "DSC0001.ARW",
        b"raw-data",
    )

    first = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(reader, raw=1),
            ]
        ),
        session,
        settings,
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id=session_id,
    )

    raw_file = (
        reader
        / "DCIM"
        / "100MSDCF"
        / "DSC0001.ARW"
    )
    raw_file.unlink()

    _write_photo(
        reader,
        "DSC0001.JPG",
        b"jpeg-data",
    )

    second = process_import_media_batch(
        ImportMediaSelection(
            sources=[
                _card(reader, jpeg=1),
            ]
        ),
        session,
        settings,
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        session_id=session_id,
    )

    assert first.success
    assert second.success

    import_root = (
        tmp_path
        / "Photos_Master"
        / "2026"
        / "Adriatic"
        / "03_Slovenia"
    )

    return session, import_root, session_id


def test_sequential_session_reconciles(tmp_path: Path):
    session, import_root, session_id = _sequential_import(
        tmp_path
    )

    result = reconcile_import_media_session(
        session,
        import_root,
        session_id=session_id,
    )

    assert result.session_id_matches is True
    assert result.source_reconciliation.expected_sources == 2
    assert result.source_reconciliation.reconciled_sources == 2
    assert result.source_reconciliation.reconciled is True
    assert result.verification.safe_to_release is True
    assert result.reconciled is True
    assert result.status == "IMPORT SESSION RECONCILED"


def test_session_id_mismatch_blocks_reconciliation(
    tmp_path: Path,
):
    session, import_root, session_id = _sequential_import(
        tmp_path
    )

    result = reconcile_import_media_session(
        session,
        import_root,
        session_id="MPS-SESSION-WRONG",
    )

    assert result.session_id_matches is False
    assert result.reconciled is False
    assert result.status == "IMPORT SESSION NOT RECONCILED"


def test_missing_processed_source_blocks_reconciliation(
    tmp_path: Path,
):
    session, import_root, session_id = _sequential_import(
        tmp_path
    )

    session.processed_source_files.append(
        Path("/media/missing/DSC9999.ARW")
    )

    result = reconcile_import_media_session(
        session,
        import_root,
        session_id=session_id,
    )

    assert result.source_reconciliation.reconciled is False
    assert result.reconciled is False


def test_tampered_destination_blocks_reconciliation(
    tmp_path: Path,
):
    session, import_root, session_id = _sequential_import(
        tmp_path
    )

    destination = import_root / "DSC0001.JPG"
    destination.write_bytes(b"tampered")

    result = reconcile_import_media_session(
        session,
        import_root,
        session_id=session_id,
    )

    assert result.source_reconciliation.reconciled is False
    assert result.verification.safe_to_release is False
    assert result.reconciled is False


def test_manifest_session_tampering_blocks_reconciliation(
    tmp_path: Path,
):
    session, import_root, session_id = _sequential_import(
        tmp_path
    )

    manifest_path = import_root / "import_manifest.json"
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    manifest["session_id"] = "MPS-SESSION-TAMPERED"
    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    result = reconcile_import_media_session(
        session,
        import_root,
        session_id=session_id,
    )

    assert result.session_id_matches is False
    assert result.verification.safe_to_release is False
    assert result.reconciled is False
