from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mps.models.source_card_reconciliation import (
    SourceCardReconciliation,
)
from mps.services.import_planner import ImportPlan
from mps.services.manifest_writer import file_sha256, read_manifest
from mps.services.provenance_index_paths import index_path


def _planned_sources(plan: ImportPlan) -> set[Path]:
    sources: set[Path] = set()

    for pair in plan.pairing.pairs:
        sources.add(pair.raw_path)
        sources.add(pair.jpeg_path)

    sources.update(plan.pairing.raw_only)
    sources.update(plan.pairing.jpeg_only)

    return sources


def _manifest_entries(
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    return list(manifest.get("files", []))


def _manifest_sources(
    manifest: dict[str, Any],
) -> set[Path]:
    return {
        Path(entry["source_path"])
        for entry in _manifest_entries(manifest)
        if entry.get("source_path")
    }


def _manifest_by_source(
    manifest: dict[str, Any],
) -> dict[Path, dict[str, Any]]:
    return {
        Path(entry["source_path"]): entry
        for entry in _manifest_entries(manifest)
        if entry.get("source_path")
    }


def _unverified_destinations(
    expected_sources: set[Path],
    manifest: dict[str, Any],
) -> list[Path]:
    entries = _manifest_by_source(manifest)
    failures: list[Path] = []

    for source in expected_sources:
        entry = entries.get(source)

        if entry is None:
            continue

        destination_value = entry.get("destination_path")
        expected_sha256 = entry.get("sha256")

        if not destination_value or not expected_sha256:
            if destination_value:
                failures.append(Path(destination_value))
            else:
                failures.append(source)
            continue

        destination = Path(destination_value)

        if not destination.exists():
            failures.append(destination)
            continue

        if file_sha256(destination) != expected_sha256:
            failures.append(destination)

    return sorted(failures)


def _provenance_failures(
    plan: ImportPlan,
    expected_sources: set[Path],
    manifest: dict[str, Any],
) -> list[Path]:
    entries = _manifest_by_source(manifest)
    certificate_index_path = index_path(plan.destination)

    if not certificate_index_path.exists():
        return sorted(
            Path(entry["destination_path"])
            for source, entry in entries.items()
            if source in expected_sources
            and entry.get("destination_path")
        )

    certificate_index = json.loads(
        certificate_index_path.read_text(encoding="utf-8")
    )

    indexed_by_destination = {
        str(entry["destination_path"]): entry
        for entry in certificate_index.get("entries", [])
        if entry.get("destination_path")
    }

    failures: list[Path] = []

    for source in expected_sources:
        manifest_entry = entries.get(source)

        if manifest_entry is None:
            continue

        destination_value = manifest_entry.get("destination_path")
        manifest_sha256 = manifest_entry.get("sha256")

        if not destination_value:
            continue

        destination = Path(destination_value)
        index_entry = indexed_by_destination.get(destination_value)

        if index_entry is None:
            failures.append(destination)
            continue

        certificate_path_value = index_entry.get("certificate_path")

        if not certificate_path_value:
            failures.append(destination)
            continue

        certificate_path = Path(certificate_path_value)

        if not certificate_path.exists():
            failures.append(destination)
            continue

        certificate = json.loads(
            certificate_path.read_text(encoding="utf-8")
        )

        if certificate.get("destination_path") != destination_value:
            failures.append(destination)
            continue

        if certificate.get("sha256") != manifest_sha256:
            failures.append(destination)
            continue

        if index_entry.get("sha256") != manifest_sha256:
            failures.append(destination)

    return sorted(failures)


def reconcile_source_cards(
    plan: ImportPlan,
) -> SourceCardReconciliation:
    manifest_path = plan.destination / "import_manifest.json"
    manifest = read_manifest(manifest_path)

    expected_sources = _planned_sources(plan)
    manifest_sources = _manifest_sources(manifest)

    missing_from_manifest = sorted(
        expected_sources - manifest_sources
    )
    unexpected_manifest_sources = sorted(
        manifest_sources - expected_sources
    )
    unverified_destinations = _unverified_destinations(
        expected_sources,
        manifest,
    )
    provenance_failures = _provenance_failures(
        plan,
        expected_sources,
        manifest,
    )

    failed_sources = {
        path
        for path in unverified_destinations + provenance_failures
    }

    reconciled_sources = len(
        expected_sources & manifest_sources
    ) - len(failed_sources)

    return SourceCardReconciliation(
        expected_sources=len(expected_sources),
        reconciled_sources=reconciled_sources,
        missing_from_manifest=missing_from_manifest,
        unexpected_manifest_sources=unexpected_manifest_sources,
        unverified_destinations=unverified_destinations,
        provenance_failures=provenance_failures,
    )
