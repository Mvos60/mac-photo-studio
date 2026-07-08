from __future__ import annotations

from pathlib import Path
from typing import Any

from mps.models.import_session import ImportSession
from mps.models.resume_plan import ResumePlan
from mps.services.manifest_writer import file_sha256


def is_incomplete_session(session: ImportSession) -> bool:
    return session.status != "completed" or session.ended_at is None


def _entry_value(entry: Any, key: str) -> Any:
    if isinstance(entry, dict):
        return entry[key]
    return getattr(entry, key)


def build_resume_plan(session: ImportSession, manifest: dict[str, Any]) -> ResumePlan:
    if not is_incomplete_session(session):
        return ResumePlan(session_id=session.session_id, resumable=False)

    plan = ResumePlan(session_id=session.session_id, resumable=True)

    for entry in manifest.get("files", []):
        destination = Path(_entry_value(entry, "destination_path"))
        expected_hash = _entry_value(entry, "sha256")

        if not destination.exists():
            plan.missing_destinations.append(str(destination))
            continue

        actual_hash = file_sha256(destination)
        if actual_hash == expected_hash:
            plan.verified_destinations.append(str(destination))
        else:
            plan.conflict_destinations.append(str(destination))

    return plan


def can_resume(plan: ResumePlan) -> bool:
    return plan.resumable and plan.conflict_count == 0
