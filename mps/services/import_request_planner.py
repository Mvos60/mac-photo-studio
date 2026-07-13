"""Compatibility planner for ImportSessionRequest.

This module serves the original two-folder import request architecture.

New flexible media-session development must use the import_media planning and
processing services.
"""

from __future__ import annotations

from mps.config import Settings
from mps.models.import_decision import ImportDecision
from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_planner import (
    ImportPlan,
    create_import_decision,
    create_import_plan,
)


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


def create_decision_from_request(
    request: ImportSessionRequest,
    settings: Settings,
) -> tuple[ImportPlan, ImportDecision]:
    """Create the planner decision used by the import pipeline."""

    plan = create_plan_from_request(request, settings)
    decision = create_import_decision(plan)

    return plan, decision
