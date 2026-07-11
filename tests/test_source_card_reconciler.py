import json
from pathlib import Path

from mps.config import Settings
from mps.services.import_planner import create_import_plan
from mps.services.manifest_writer import file_sha256
from mps.services.source_card_reconciler import reconcile_source_cards


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Photos_Master"),
            },
            "media": {
                "raw_extensions": ["ARW"],
                "jpeg_extensions": ["JPG", "JPEG"],
            },
        }
    )


def _plan(tmp_path: Path):
    raw = tmp_path / "raw"
    jpeg = tmp_path / "jpeg"

    raw.mkdir()
    jpeg.mkdir()

    raw_file = raw / "DSC0001.ARW"
    jpeg_file = jpeg / "DSC0001.JPG"

    raw_file.write_bytes(b"raw-data")
    jpeg_file.write_bytes(b"jpeg-data")

    plan = create_import_plan(
        year=2026,
        project="Adriatic",
        day="03_Slovenia",
        raw_folder=raw,
        jpeg_folder=jpeg,
        settings=_settings(tmp_path),
    )

    plan.destination.mkdir(parents=True)

    return plan, raw_file, jpeg_file


def _write_manifest(
    plan,
    source_paths: list[Path],
) -> None:
    files = []

    for source in source_paths:
        destination = plan.destination / source.name

        if source.exists():
            destination.write_bytes(source.read_bytes())
            sha256 = file_sha256(destination)
        else:
            sha256 = "0" * 64

        files.append(
            {
                "source_path": str(source),
                "destination_path": str(destination),
                "sha256": sha256,
            }
        )

    manifest = {
        "files": files,
    }

    (plan.destination / "import_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def _write_provenance(plan) -> None:
    manifest = json.loads(
        (plan.destination / "import_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    provenance = plan.destination / "provenance"
    provenance.mkdir(exist_ok=True)

    index_entries = []

    for number, entry in enumerate(manifest["files"], start=1):
        destination = entry["destination_path"]
        certificate_path = (
            provenance / f"MPS-CERT-{number}.json"
        )

        certificate = {
            "certificate_id": f"MPS-CERT-{number}",
            "destination_path": destination,
            "sha256": entry["sha256"],
        }

        certificate_path.write_text(
            json.dumps(certificate),
            encoding="utf-8",
        )

        index_entries.append(
            {
                "certificate_id": f"MPS-CERT-{number}",
                "destination_path": destination,
                "certificate_path": str(certificate_path),
                "sha256": entry["sha256"],
            }
        )

    (provenance / "certificate_index.json").write_text(
        json.dumps({"entries": index_entries}),
        encoding="utf-8",
    )


def test_reconcile_source_cards_matches_plan_and_manifest(tmp_path: Path):
    plan, raw_file, jpeg_file = _plan(tmp_path)

    _write_manifest(plan, [raw_file, jpeg_file])
    _write_provenance(plan)

    result = reconcile_source_cards(plan)

    assert result.expected_sources == 2
    assert result.reconciled_sources == 2
    assert result.missing_from_manifest == []
    assert result.unexpected_manifest_sources == []
    assert result.unverified_destinations == []
    assert result.provenance_failures == []
    assert result.reconciled is True


def test_reconcile_source_cards_reports_missing_manifest_source(
    tmp_path: Path,
):
    plan, raw_file, jpeg_file = _plan(tmp_path)

    _write_manifest(plan, [raw_file])
    _write_provenance(plan)

    result = reconcile_source_cards(plan)

    assert result.expected_sources == 2
    assert result.reconciled_sources == 1
    assert result.missing_from_manifest == [jpeg_file]
    assert result.reconciled is False


def test_reconcile_source_cards_reports_unexpected_manifest_source(
    tmp_path: Path,
):
    plan, raw_file, jpeg_file = _plan(tmp_path)
    unexpected = tmp_path / "other" / "DSC9999.ARW"

    _write_manifest(plan, [raw_file, jpeg_file, unexpected])
    _write_provenance(plan)

    result = reconcile_source_cards(plan)

    assert result.expected_sources == 2
    assert result.reconciled_sources == 2
    assert result.unexpected_manifest_sources == [unexpected]
    assert result.reconciled is False


def test_reconcile_source_cards_blocks_missing_destination(
    tmp_path: Path,
):
    plan, raw_file, jpeg_file = _plan(tmp_path)

    _write_manifest(plan, [raw_file, jpeg_file])
    _write_provenance(plan)

    destination = plan.destination / raw_file.name
    destination.unlink()

    result = reconcile_source_cards(plan)

    assert result.expected_sources == 2
    assert result.reconciled_sources == 1
    assert result.unverified_destinations == [destination]
    assert result.reconciled is False


def test_reconcile_source_cards_blocks_destination_hash_mismatch(
    tmp_path: Path,
):
    plan, raw_file, jpeg_file = _plan(tmp_path)

    _write_manifest(plan, [raw_file, jpeg_file])
    _write_provenance(plan)

    destination = plan.destination / jpeg_file.name
    destination.write_bytes(b"tampered")

    result = reconcile_source_cards(plan)

    assert result.expected_sources == 2
    assert result.reconciled_sources == 1
    assert result.unverified_destinations == [destination]
    assert result.reconciled is False


def test_reconcile_source_cards_blocks_missing_certificate_index(
    tmp_path: Path,
):
    plan, raw_file, jpeg_file = _plan(tmp_path)

    _write_manifest(plan, [raw_file, jpeg_file])

    result = reconcile_source_cards(plan)

    assert result.reconciled_sources == 0
    assert result.provenance_failures == [
        plan.destination / "DSC0001.ARW",
        plan.destination / "DSC0001.JPG",
    ]
    assert result.reconciled is False


def test_reconcile_source_cards_blocks_certificate_hash_mismatch(
    tmp_path: Path,
):
    plan, raw_file, jpeg_file = _plan(tmp_path)

    _write_manifest(plan, [raw_file, jpeg_file])
    _write_provenance(plan)

    certificate_path = (
        plan.destination / "provenance" / "MPS-CERT-1.json"
    )
    certificate = json.loads(
        certificate_path.read_text(encoding="utf-8")
    )
    certificate["sha256"] = "0" * 64
    certificate_path.write_text(
        json.dumps(certificate),
        encoding="utf-8",
    )

    result = reconcile_source_cards(plan)

    assert result.reconciled_sources == 1
    assert result.provenance_failures == [
        plan.destination / "DSC0001.ARW",
    ]
    assert result.reconciled is False
