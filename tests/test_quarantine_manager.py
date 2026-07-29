from datetime import datetime
import json
from pathlib import Path

from mps.services.quarantine_manager import (
    QuarantineItem,
    permanently_delete_quarantine_item,
    scan_quarantine,
    total_quarantine_size,
)


def test_scan_empty_quarantine(tmp_path: Path) -> None:
    assert scan_quarantine(tmp_path) == ()


def test_scan_legacy_item(tmp_path: Path) -> None:
    directory = tmp_path / ".mps_quarantine" / "culling" / "DSC0001"
    directory.mkdir(parents=True)
    (directory / "DSC0001.ARW").write_bytes(b"raw")

    items = scan_quarantine(tmp_path)

    assert len(items) == 1
    assert items[0].stem == "DSC0001"
    assert items[0].restorable is False


def test_scan_metadata_item(tmp_path: Path) -> None:
    directory = tmp_path / ".mps_quarantine" / "culling" / "DSC0002"
    directory.mkdir(parents=True)
    raw = directory / "DSC0002.ARW"
    raw.write_bytes(b"raw-data")
    manifest = directory / "manifest.before.json"
    manifest.write_text("{}", encoding="utf-8")
    index = directory / "certificate_index.before.json"
    index.write_text("{}", encoding="utf-8")

    metadata = {
        "version": 1,
        "created_at": "2026-07-25T12:00:00+00:00",
        "import_root": str(tmp_path),
        "raw": {
            "original": str(tmp_path / "DSC0002.ARW"),
            "quarantine": str(raw),
        },
        "manifest_snapshot": str(manifest),
        "index_snapshot": str(index),
    }
    (directory / "quarantine.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    items = scan_quarantine(tmp_path)

    assert len(items) == 1
    assert items[0].restorable is True
    assert items[0].raw_quarantine_path == raw


def test_total_quarantine_size() -> None:
    now = datetime.now()
    items = (
        QuarantineItem(
            "A",
            Path("/tmp/A"),
            now,
            100,
            None,
            None,
            None,
            False,
            "",
        ),
        QuarantineItem(
            "B",
            Path("/tmp/B"),
            now,
            250,
            None,
            None,
            None,
            False,
            "",
        ),
    )

    assert total_quarantine_size(items) == 350


def test_permanent_delete_removes_item(tmp_path: Path) -> None:
    directory = tmp_path / ".mps_quarantine" / "culling" / "DSC0003"
    directory.mkdir(parents=True)
    (directory / "DSC0003.ARW").write_bytes(b"123456")
    item = scan_quarantine(tmp_path)[0]

    result = permanently_delete_quarantine_item(tmp_path, item)

    assert result.success is True
    assert result.released_bytes == 6
    assert not directory.exists()


def test_permanent_delete_refuses_external_path(tmp_path: Path) -> None:
    external = tmp_path / "outside"
    external.mkdir()
    item = QuarantineItem(
        "outside",
        external,
        datetime.now(),
        0,
        None,
        None,
        None,
        False,
        "",
    )

    result = permanently_delete_quarantine_item(tmp_path, item)

    assert result.success is False
    assert external.exists()
