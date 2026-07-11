from __future__ import annotations

from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_card_report import build_card_report
from mps.services.import_card_selector import ImportCardSelection
from mps.services.import_planner import ImportPlan


def build_wizard_intro(selection: ImportCardSelection) -> str:
    return (
        "Mac Photo Studio Import Wizard\n"
        "==============================\n\n"
        + build_card_report(selection)
    )


def build_import_summary(request: ImportSessionRequest) -> str:
    raw_folder = (
        str(request.raw_folder)
        if request.raw_folder is not None
        else "Not selected"
    )

    jpeg_folder = (
        str(request.jpeg_folder)
        if request.jpeg_folder is not None
        else "Not selected"
    )

    return (
        "Import Summary\n"
        "==============\n\n"
        f"Year        : {request.year}\n"
        f"Project     : {request.project}\n"
        f"Day/session : {request.day}\n"
        f"RAW folder  : {raw_folder}\n"
        f"JPEG folder : {jpeg_folder}"
    )


def build_import_plan_preview(plan: ImportPlan) -> str:
    lines = [
        "Import Plan Preview",
        "===================",
        "",
        f"Destination : {plan.destination}",
        f"Pairs       : {plan.pairing.pair_count}",
        f"RAW only    : {len(plan.pairing.raw_only)}",
        f"JPEG only   : {len(plan.pairing.jpeg_only)}",
        f"Total files : {plan.total_source_files}",
        f"Size bytes  : {plan.estimated_size_bytes}",
    ]

    if plan.warnings:
        lines.extend(["", "Warnings"])

        for warning in plan.warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines)
