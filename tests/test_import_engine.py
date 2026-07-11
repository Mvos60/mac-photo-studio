import json
from pathlib import Path

from mps.models.import_decision import CopyOperation, ImportDecision
from mps.services.import_engine import run_import


def _decision(tmp_path: Path) -> ImportDecision:
    source1 = tmp_path / "source1.ARW"
    source2 = tmp_path / "source1.JPG"

    source1.write_bytes(b"raw-photo-data")
    source2.write_bytes(b"jpeg-photo-data")

    destination = tmp_path / "Photos"

    return ImportDecision(
        destination=destination,
        total_files=2,
        estimated_size_bytes=source1.stat().st_size + source2.stat().st_size,
        copy_operations=[
            CopyOperation(
                source=source1,
                destination=destination / source1.name,
            ),
            CopyOperation(
                source=source2,
                destination=destination / source2.name,
            ),
        ],
        warnings=[],
    )


def test_import_engine_dry_run(tmp_path):
    decision = _decision(tmp_path)
    log_path = tmp_path / "import.log"

    result = run_import(decision, dry_run=True, log_path=log_path)

    assert result.dry_run
    assert result.copied == 0
    assert result.failed == 0
    assert result.skipped == 2
    assert result.log_path is None
    assert not decision.destination.exists()
    assert not log_path.exists()


def test_import_engine_copies_all_files(tmp_path):
    decision = _decision(tmp_path)

    result = run_import(decision, dry_run=False)

    copied_raw = decision.destination / "source1.ARW"
    copied_jpg = decision.destination / "source1.JPG"

    assert copied_raw.exists()
    assert copied_jpg.exists()

    assert copied_raw.read_bytes() == b"raw-photo-data"
    assert copied_jpg.read_bytes() == b"jpeg-photo-data"

    assert result.copied == 2
    assert result.failed == 0
    assert result.skipped == 0
    assert result.success


def test_import_engine_reports_progress(tmp_path):
    decision = _decision(tmp_path)
    seen: list[tuple[int, int, str]] = []

    def collect(progress):
        seen.append(
            (
                progress.current,
                progress.total,
                progress.source.name,
            )
        )

    result = run_import(
        decision,
        dry_run=False,
        progress_callback=collect,
    )

    assert result.success
    assert seen == [
        (1, 2, "source1.ARW"),
        (2, 2, "source1.JPG"),
    ]


def test_import_engine_writes_log(tmp_path):
    decision = _decision(tmp_path)
    log_path = tmp_path / "logs" / "import.log"

    result = run_import(
        decision,
        dry_run=False,
        log_path=log_path,
    )

    assert result.success
    assert result.log_path == log_path
    assert log_path.exists()

    text = log_path.read_text(encoding="utf-8")

    assert "Mac Photo Studio Import Log" in text
    assert "source1.ARW" in text
    assert "source1.JPG" in text
    assert "Copied: 2" in text
    assert "Failed: 0" in text
    assert "Success: True" in text


def test_import_engine_writes_provenance_certificates_and_index(
    tmp_path,
):
    decision = _decision(tmp_path)

    result = run_import(
        decision,
        dry_run=False,
        write_provenance=True,
        camera_model="Sony A7 III",
        manifest_path=decision.destination / "import_manifest.json",
        project="Adriatic",
        day_session="03_Slovenia",
    )

    provenance_dir = decision.destination / "provenance"
    index_file = provenance_dir / "certificate_index.json"

    assert result.success
    assert provenance_dir.exists()
    assert index_file.exists()

    certificate_files = sorted(
        path
        for path in provenance_dir.glob("MPS-CERT-*.json")
    )

    assert len(certificate_files) == 2

    index_text = index_file.read_text(encoding="utf-8")

    assert "Sony A7 III" in index_text
    assert "source1.ARW" in index_text
    assert "source1.JPG" in index_text


def test_import_engine_writes_requested_manifest(tmp_path):
    decision = _decision(tmp_path)
    manifest_path = decision.destination / "import_manifest.json"

    result = run_import(
        decision,
        dry_run=False,
        write_provenance=True,
        camera_model="Sony A7 III",
        manifest_path=manifest_path,
        project="Adriatic",
        day_session="03_Slovenia",
    )

    assert result.success
    assert manifest_path.exists()

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    assert manifest["project"] == "Adriatic"
    assert manifest["day_session"] == "03_Slovenia"
    assert manifest["file_count"] == 2
    assert manifest["files"][0]["status"] == "verified"
    assert manifest["files"][1]["status"] == "verified"


def test_manifest_and_certificates_share_session_id(tmp_path):
    decision = _decision(tmp_path)
    manifest_path = decision.destination / "import_manifest.json"

    result = run_import(
        decision,
        dry_run=False,
        write_provenance=True,
        camera_model="Sony A7 III",
        manifest_path=manifest_path,
        project="Adriatic",
        day_session="03_Slovenia",
    )

    assert result.success

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    certificate_files = sorted(
        (
            decision.destination / "provenance"
        ).glob("MPS-CERT-*.json")
    )

    certificates = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in certificate_files
    ]

    assert len(certificates) == 2

    for certificate in certificates:
        assert certificate["session_id"] == manifest["session_id"]
        assert certificate["manifest_path"] == str(manifest_path)
