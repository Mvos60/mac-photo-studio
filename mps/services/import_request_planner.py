from __future__ import annotations

from mps.config import Settings
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_planner import ImportPlan, create_import_plan


def create_plan_from_request(
    request: ImportSessionRequest,
    settings: Settings,
) -> ImportPlan:
    """Create a read-only import plan from a wizard request."""

    return create_import_plan(
        year=request.year,
        project=request.project,
        day=request.day,
        raw_folder=request.raw_folder,
        jpeg_folder=request.jpeg_folder,
        settings=settings,
    )
