from __future__ import annotations

from mps.services.culling_analyzer import (
    CullingAnalysis,
    CullingCandidateStatus,
)


def build_culling_report(
    analysis: CullingAnalysis,
) -> str:
    lines = [
        "Culling Analysis",
        "================",
        "",
        f"Import root                    : {analysis.import_root}",
        f"Missing imported JPGs          : {analysis.missing_jpeg_count}",
        (
            "Verified orphan RAWs           : "
            f"{analysis.orphan_raw_candidate_count}"
        ),
        (
            "Provenance cleanup candidates  : "
            f"{analysis.provenance_cleanup_candidate_count}"
        ),
        "",
    ]

    if not analysis.missing_jpegs:
        lines.extend(
            [
                "No missing imported JPG files were detected.",
                "",
                "Read-only analysis. No files were changed.",
            ]
        )

        return "\n".join(lines)

    lines.append("Detected items:")
    lines.append("")

    for item in analysis.missing_jpegs:
        if (
            item.status
            == CullingCandidateStatus.CULL_CANDIDATE
        ):
            status = "CULL CANDIDATE"
        elif (
            item.status
            == (
                CullingCandidateStatus
                .PROVENANCE_CLEANUP_CANDIDATE
            )
        ):
            status = "PROVENANCE CLEANUP CANDIDATE"
        elif (
            item.status
            == CullingCandidateStatus.RAW_HASH_MISMATCH
        ):
            status = "BLOCKED: RAW HASH MISMATCH"
        else:
            status = "NO ACTION: IMPORTED RAW IS MISSING"

        lines.extend(
            [
                f"{item.stem}",
                f"  JPG    : {item.jpeg_path}",
                (
                    "  RAW    : "
                    f"{item.raw_path or '-'}"
                ),
                f"  Status : {status}",
                "",
            ]
        )

    lines.append(
        "Read-only analysis. No files were changed."
    )

    return "\n".join(lines)
