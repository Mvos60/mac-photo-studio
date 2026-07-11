from __future__ import annotations

from mps.models.import_session_request import ImportSessionRequest
from mps.models.post_import_verification import PostImportVerification
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


def build_post_import_verification_summary(
    result: PostImportVerification,
) -> str:
    lines = [
        "Post-Import Verification",
        "========================",
        "",
        f"Files expected       : {result.expected_files}",
        f"Files verified       : {result.verified_files}",
        f"Certificates expected: {result.expected_certificates}",
        f"Certificates verified: {result.verified_certificates}",
        f"Card status          : {result.card_status}",
    ]

    if result.missing_files:
        lines.extend(["", "Missing files"])

        for path in result.missing_files:
            lines.append(f"- {path}")

    if result.checksum_mismatches:
        lines.extend(["", "Checksum mismatches"])

        for path in result.checksum_mismatches:
            lines.append(f"- {path}")

    if result.incomplete_entries:
        lines.extend(
            [
                "",
                f"Incomplete manifest entries: "
                f"{result.incomplete_entries}",
            ]
        )

    if result.provenance_errors:
        lines.extend(["", "Provenance errors"])

        for error in result.provenance_errors:
            lines.append(f"- {error}")

    return "\n".join(lines)
