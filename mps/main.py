from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mps.config import load_settings
from mps.constants import USER_STATE_DIR
from mps.exceptions import MacPhotoStudioError
from mps.gui.app import run_gui
from mps.logger import configure_logging
from mps.services.camera_identifier import identify_camera_model
from mps.services.card_scanner import format_bytes, scan_cards, scan_path
from mps.services.cli_output import print_card_summary, print_decision_preview
from mps.services.culling_analyzer import analyze_culling
from mps.services.culling_executor import execute_culling_candidate
from mps.services.culling_report import build_culling_report
from mps.services.darktable_export_completion import (
    complete_darktable_export,
)
from mps.services.digikam_darktable_handoff import (
    handoff_digikam_photo_to_darktable,
)
from mps.services.health import run_health_checks
from mps.services.import_engine import run_import
from mps.services.import_planner import create_import_decision, create_import_plan
from mps.services.import_media_batch_planner import (
    media_import_destination,
)
from mps.services.import_media_resume_validator import (
    can_resume_import_media_session,
)
from mps.services.import_media_session_store import (
    load_import_media_session,
)
from mps.services.import_media_wizard_runner import (
    run_import_media_session,
)
from mps.services.import_prompts import (
    prompt_day,
    prompt_project,
    prompt_year,
)
from mps.services.import_session_builder import build_import_session
from mps.services.import_wizard_ui import (
    build_post_import_verification_summary,
    build_source_card_reconciliation_summary,
)
from mps.services.pairing import pair_paths
from mps.services.photo_provenance_history import (
    read_managed_photo_history,
)
from mps.services.photo_provenance_verification import (
    verify_managed_photo,
)
from mps.services.photographer_workflow_commands import (
    record_darktable_workflow_command,
    record_digikam_workflow_command,
)
from mps.services.photo_workflow_integration import (
    record_photo_workflow_action,
)
from mps.services.post_import_verifier import verify_import_root
from mps.services.safe_copy import copy_one_file
from mps.services.source_card_reconciler import reconcile_source_cards
from mps.services.workflow_application_launcher import launch_digikam
from mps.version import get_version


def print_health() -> int:
    settings = load_settings()
    checks = run_health_checks(settings)

    print("Mac Photo Studio Health Check")
    print("=" * 31)

    for check in checks:
        status = "OK" if check.ok else "WARN"
        print(f"{status:5} {check.name:14} {check.message}")

    return 0


def print_scan_cards() -> int:
    settings = load_settings()
    cards = scan_cards(settings)

    print("Mac Photo Studio Card Scan")
    print("=" * 26)

    if not cards:
        print("No photo cards found.")
        print("This scan is read-only. No files were modified.")
        return 0

    for idx, card in enumerate(cards, start=1):
        print(f"Card {idx}")
        print_card_summary(card, indent="  ")
        print()

    print("Read-only scan complete. No files were modified.")
    return 0


def print_scan_path(path_text: str) -> int:
    settings = load_settings()
    card = scan_path(Path(path_text), settings)

    print("Mac Photo Studio Path Scan")
    print("=" * 26)
    print_card_summary(card)
    print()
    print("Read-only scan complete. No files were modified.")
    return 0


def print_analyze_culling(import_root: str) -> int:
    settings = load_settings()

    analysis = analyze_culling(
        Path(import_root),
        settings,
    )

    print(build_culling_report(analysis))
    return 0


def print_confirm_culling(
    import_root: str,
    stem: str,
) -> int:
    settings = load_settings()
    root = Path(import_root).expanduser()

    analysis = analyze_culling(
        root,
        settings,
    )

    candidates = [
        candidate
        for candidate in analysis.orphan_raw_candidates
        if candidate.stem == stem
    ]

    if not candidates:
        print("Mac Photo Studio Confirm Culling")
        print("=" * 32)
        print()
        print(f"Import root : {root}")
        print(f"Photo stem  : {stem}")
        print()
        print("Status      : NOT A VERIFIED CULLING CANDIDATE")
        print("No files were changed.")
        return 1

    candidate = candidates[0]

    print("Mac Photo Studio Confirm Culling")
    print("=" * 32)
    print()
    print(f"Import root : {root}")
    print(f"Photo stem  : {candidate.stem}")
    print(f"Missing JPG : {candidate.jpeg_path}")
    print(f"Verified RAW: {candidate.raw_path}")
    print()
    print(
        "The RAW and active provenance for this "
        "photographic pair will be moved to quarantine."
    )
    print()

    answer = input(
        "Type CULL to confirm: "
    ).strip()

    if answer != "CULL":
        print()
        print("Culling cancelled. No files were changed.")
        return 0

    result = execute_culling_candidate(
        root,
        candidate,
    )

    print()
    print("Culling Result")
    print("==============")
    print()
    print(
        f"Status                      : "
        f"{'QUARANTINED' if result.success else 'FAILED'}"
    )
    print(
        f"Manifest entries removed    : "
        f"{result.removed_manifest_entries}"
    )
    print(
        f"Certificate entries removed : "
        f"{result.removed_index_entries}"
    )
    print(
        f"Provenance items quarantined : "
        f"{result.quarantined_provenance_items}"
    )

    if result.raw_quarantine_path is not None:
        print(
            f"RAW quarantine path         : "
            f"{result.raw_quarantine_path}"
        )

    print(f"Message                     : {result.message}")

    return 0 if result.success else 1


def print_pair_paths(raw_folder: str, jpeg_folder: str) -> int:
    settings = load_settings()
    result = pair_paths(Path(raw_folder), Path(jpeg_folder), settings)

    print("Mac Photo Studio Pairing Preview")
    print("=" * 33)
    print(f"RAW folder:   {Path(raw_folder).expanduser()}")
    print(f"JPEG folder:  {Path(jpeg_folder).expanduser()}")
    print()
    print(f"Pairs:        {result.pair_count}")
    print(f"RAW only:     {len(result.raw_only)}")
    print(f"JPEG only:    {len(result.jpeg_only)}")
    print()

    if result.raw_only:
        print("RAW-only files:")
        for file in result.raw_only[:10]:
            print(f"  {file}")
        if len(result.raw_only) > 10:
            print(f"  ... and {len(result.raw_only) - 10} more")
        print()

    if result.jpeg_only:
        print("JPEG-only files:")
        for file in result.jpeg_only[:10]:
            print(f"  {file}")
        if len(result.jpeg_only) > 10:
            print(f"  ... and {len(result.jpeg_only) - 10} more")
        print()

    print("Read-only pairing preview complete. No files were modified.")
    return 0


def build_import_decision(
    year: int,
    project: str,
    day: str,
    raw_folder: str,
    jpeg_folder: str,
):
    session = build_import_session(
        year=year,
        project=project,
        day=day,
        raw_folder=raw_folder,
        jpeg_folder=jpeg_folder,
    )

    settings = load_settings()
    plan = create_import_plan(
        year=session.year,
        project=session.project,
        day=session.day,
        raw_folder=session.raw_folder,
        jpeg_folder=session.jpeg_folder,
        settings=settings,
    )
    decision = create_import_decision(plan)
    return plan, decision


def print_import_plan(
    year: int,
    project: str,
    day: str,
    raw_folder: str,
    jpeg_folder: str,
) -> int:
    plan, decision = build_import_decision(
        year,
        project,
        day,
        raw_folder,
        jpeg_folder,
    )

    print("Mac Photo Studio Import Plan")
    print("=" * 28)
    print(f"Year:         {plan.year}")
    print(f"Project:      {plan.project}")
    print(f"Day/session:  {plan.day}")
    print(f"Destination:  {plan.destination}")
    print()
    print("Sources")
    print(f"  RAW:        {plan.raw_folder}")
    print(f"  JPEG:       {plan.jpeg_folder}")
    print()
    print("Files")
    print(f"  Pairs:      {plan.pairing.pair_count}")
    print(f"  RAW only:   {len(plan.pairing.raw_only)}")
    print(f"  JPEG only:  {len(plan.pairing.jpeg_only)}")
    print(f"  Total:      {plan.total_source_files}")
    print(f"  Size:       {format_bytes(plan.estimated_size_bytes)}")
    print()

    print_decision_preview(decision)

    print("Plan only. No files or folders were created.")
    return 0


def print_dry_run_import(
    year: int,
    project: str,
    day: str,
    raw_folder: str,
    jpeg_folder: str,
) -> int:
    plan, decision = build_import_decision(
        year,
        project,
        day,
        raw_folder,
        jpeg_folder,
    )

    print("Mac Photo Studio Dry Run Import")
    print("=" * 31)
    print(f"Year:         {plan.year}")
    print(f"Project:      {plan.project}")
    print(f"Day/session:  {plan.day}")
    print(f"Destination:  {decision.destination}")
    print()

    print_decision_preview(decision)

    print("Dry run only. No files or folders were created.")
    return 0


def run_real_import(
    year: int,
    project: str,
    day: str,
    raw_folder: str,
    jpeg_folder: str,
) -> int:
    plan, decision = build_import_decision(
        year,
        project,
        day,
        raw_folder,
        jpeg_folder,
    )
    log_path = decision.destination / "mps_import.log"

    print("Mac Photo Studio Import")
    print("=" * 23)
    print(f"Year:         {plan.year}")
    print(f"Project:      {plan.project}")
    print(f"Day/session:  {plan.day}")
    print(f"Destination:  {decision.destination}")

    first_source = decision.copy_operations[0].source
    camera_model = identify_camera_model(first_source)

    print(f"Camera:       {camera_model}")
    print()
    print("Starting verified copy...")

    result = run_import(
        decision,
        dry_run=False,
        log_path=log_path,
        write_provenance=True,
        camera_model=camera_model,
        manifest_path=decision.destination / "import_manifest.json",
        project=plan.project,
        day_session=plan.day,
    )

    print()
    print("Import Summary")
    print("--------------")
    print(f"Copied:       {result.copied}")
    print(f"Failed:       {result.failed}")
    print(f"Skipped:      {result.skipped}")
    print(f"Success:      {result.success}")
    print(f"Log:          {result.log_path}")

    if not result.success:
        return 1

    verification = verify_import_root(decision.destination)

    print()
    print(build_post_import_verification_summary(verification))
    print()

    if not verification.safe_to_release:
        return 1

    reconciliation = reconcile_source_cards(plan)

    print(build_source_card_reconciliation_summary(reconciliation))
    print()

    return 0 if reconciliation.reconciled else 1


def run_interactive_import_command() -> int:
    from datetime import datetime

    settings = load_settings()
    state_path = (
        USER_STATE_DIR
        / "active_import_session.json"
    )

    print("Mac Photo Studio Import Wizard")
    print("==============================")
    print()

    year = prompt_year(datetime.now().year)
    project = prompt_project()
    day = prompt_day()

    import_root = media_import_destination(
        settings,
        year=year,
        project=project,
        day=day,
    )

    print()
    print("Import Session")
    print("==============")
    print()
    print(f"Year        : {year}")
    print(f"Project     : {project}")
    print(f"Day/session : {day}")
    print()

    restored_session = None

    if state_path.exists():
        restored_session = load_import_media_session(
            state_path
        )

        print(
            "An interrupted import session was found."
        )
        print(
            f"Session ID  : "
            f"{restored_session.session_id}"
        )
        print()

        answer = input(
            "Resume this import session? [Y/n]: "
        ).strip().lower()

        if answer in {"n", "no"}:
            print(
                "Saved import session left unchanged."
            )
            return 0

        if not can_resume_import_media_session(
            restored_session,
            import_root,
        ):
            print(
                "Saved import session cannot be resumed safely."
            )
            print(
                "The existing manifest or provenance "
                "evidence did not verify."
            )
            return 1

        print("Resuming verified import session.")
        print()

    else:
        answer = input(
            "Start this import session? [Y/n]: "
        ).strip().lower()

        if answer in {"n", "no"}:
            print("Import cancelled.")
            return 0

    result = run_import_media_session(
        settings,
        year=year,
        project=project,
        day=day,
        session=restored_session,
        session_state_path=state_path,
    )

    print()
    print("Import Session Summary")
    print("======================")
    print()
    print(f"Batches processed : {result.batches_processed}")
    print(f"Files copied      : {result.copied}")
    print(f"Files failed      : {result.failed}")
    print(f"Completed         : {result.completed}")
    print(f"Success           : {result.success}")

    if not result.success:
        return 1

    if settings.get(
        "gui.launch_digikam_after_import",
        False,
    ):
        launch = launch_digikam(
            settings=settings,
            import_root=import_root,
        )

        print()
        print("digiKam Handoff")
        print("================")
        print()

        if launch.launched:
            print("Status           : LAUNCHED")
            print(f"Import root      : {import_root}")
        else:
            print("Status           : NOT LAUNCHED")

            for error in launch.errors:
                print(f"Reason           : {error}")

            return 1

    return 0


def print_copy_one(source: str, destination: str) -> int:
    result = copy_one_file(Path(source), Path(destination))

    print("Mac Photo Studio Safe Copy")
    print("=" * 26)
    print(f"Source:       {result.source}")
    print(f"Destination:  {result.destination}")
    print(f"Success:      {result.success}")
    print(f"Size:         {format_bytes(result.size_bytes)}")
    print(f"Checksum:     {result.checksum or 'not available'}")
    print(f"Message:      {result.message}")

    return 0 if result.success else 1


def print_darktable_export_completion(
    *,
    source_path: str,
    output_path: str,
) -> int:
    settings = load_settings()

    result = complete_darktable_export(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
    )

    print("Mac Photo Studio darktable Export Completion")
    print("=" * 45)
    print(f"Source:        {result.source_path}")
    print(f"Output:        {result.output_path}")
    print()

    if result.completed:
        print("Status:        VERIFIED")
        print(
            "The exported photo was recorded and verified."
        )
        return 0

    print("Status:        NOT VERIFIED")

    for error in result.errors:
        print(f"Reason:        {error}")

    return 1


def print_digikam_darktable_handoff(
    photo_path: str,
) -> int:
    settings = load_settings()

    result = handoff_digikam_photo_to_darktable(
        settings=settings,
        photo_path=photo_path,
    )

    print("Mac Photo Studio digiKam → darktable Handoff")
    print("=" * 46)
    print(f"Photo:         {result.photo_path}")
    print()

    if result.handed_off:
        print("Status:        LAUNCHED")
        print(
            "The trusted photo was handed off to darktable."
        )
        return 0

    print("Status:        NOT LAUNCHED")

    for error in result.errors:
        print(f"Reason:        {error}")

    return 1


def print_application_workflow_action(
    *,
    application: str,
    action: str,
    source_path: str,
    output_path: str,
) -> int:
    settings = load_settings()

    if application == "digikam":
        result = record_digikam_workflow_command(
            settings=settings,
            action=action,
            source_path=source_path,
            output_path=output_path,
        )
        recorded = result.recorded
        errors = result.errors
    else:
        result = record_darktable_workflow_command(
            settings=settings,
            action=action,
            source_path=source_path,
            output_path=output_path,
        )
        recorded = result.recorded
        errors = result.errors

    title = (
        f"Mac Photo Studio {application} "
        f"{action.capitalize()}"
    )

    print(title)
    print("=" * len(title))
    print(f"Source:        {Path(source_path).expanduser()}")
    print(f"Output:        {Path(output_path).expanduser()}")
    print()

    if recorded:
        print("Status:        RECORDED")
        return 0

    print("Status:        NOT RECORDED")

    for error in errors:
        print(f"Reason:        {error}")

    return 1


def print_record_photo_action(
    *,
    source_path: str,
    output_path: str,
    event_type: str,
) -> int:
    settings = load_settings()

    application = None
    description = None

    if event_type == "edit":
        application = "darktable"
        description = "Photographic edit"

    if event_type == "export":
        description = "Photographic export"

    result = record_photo_workflow_action(
        settings=settings,
        source_path=source_path,
        output_path=output_path,
        action=event_type,
        application=application,
        description=description,
    )

    title = (
        "Mac Photo Studio Record Edit"
        if event_type == "edit"
        else "Mac Photo Studio Record Export"
    )

    print(title)
    print("=" * len(title))
    print(f"Source:        {result.source_path}")
    print(f"Output:        {result.output_path}")
    print()

    if result.recorded:
        print("Status:        RECORDED")

        if result.event is not None:
            print(
                f"Event:         "
                f"{result.event.event_type.value.upper()}"
            )

        print(
            "The output file now continues the "
            "recorded photographic lineage."
        )
        return 0

    print("Status:        NOT RECORDED")

    for error in result.errors:
        print(f"Reason:        {error}")

    return 1


def print_photo_history(
    photo_path: str,
) -> int:
    settings = load_settings()

    result = read_managed_photo_history(
        settings=settings,
        photo_path=photo_path,
    )

    print("Mac Photo Studio Photo Provenance History")
    print("=" * 43)
    print(f"Photo:         {result.photo_path}")
    print(
        f"Status:        "
        f"{'TRUSTED' if result.trusted else 'NOT TRUSTED'}"
    )
    print()

    for index, event in enumerate(
        result.events,
        start=1,
    ):
        print(f"{index}. {event.event_type.value.upper()}")
        print(f"   Time:        {event.created_at}")

        if event.application:
            application = event.application

            if event.application_version:
                application += (
                    f" {event.application_version}"
                )

            print(f"   Application: {application}")

        camera_model = event.metadata.get(
            "camera_model"
        )

        if camera_model:
            print(f"   Camera:      {camera_model}")

        if event.description:
            print(f"   {event.description}")

        output_path = event.metadata.get(
            "output_path"
        )

        if output_path:
            print(f"   Output:      {output_path}")

        print()

    for error in result.errors:
        print(f"Reason:        {error}")

    return 0 if result.trusted else 1


def print_verify_photo(
    photo_path: str,
) -> int:
    settings = load_settings()

    result = verify_managed_photo(
        settings=settings,
        photo_path=photo_path,
    )

    print("Mac Photo Studio Photo Verification")
    print("=" * 35)
    print(f"Photo:         {result.photo_path}")

    if result.import_root is not None:
        print(f"Import root:   {result.import_root}")

    print()

    if result.trusted:
        print("Status:        TRUSTED")
        print(
            "This exact file belongs to a valid "
            "recorded photographic lineage."
        )

        verification = result.verification

        if (
            verification is not None
            and verification.chain is not None
        ):
            print(
                f"Events:        "
                f"{verification.chain.event_count}"
            )

        return 0

    print("Status:        NOT TRUSTED")

    for error in result.errors:
        print(f"Reason:        {error}")

    return 1


def show_config() -> int:
    settings = load_settings()
    print(json.dumps(settings.data, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mac-photo-studio")
    parser.add_argument("command", nargs="?")
    parser.add_argument("command_args", nargs="*")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--scan-cards", action="store_true")
    parser.add_argument("--scan-path")
    parser.add_argument("--analyze-culling")
    parser.add_argument(
        "--confirm-culling",
        nargs=2,
        metavar=("IMPORT_SESSION_FOLDER", "PHOTO_STEM"),
    )
    parser.add_argument(
        "--pair-paths",
        nargs=2,
        metavar=("RAW_FOLDER", "JPEG_FOLDER"),
    )
    parser.add_argument(
        "--plan-import",
        nargs=5,
        metavar=("YEAR", "PROJECT", "DAY", "RAW_FOLDER", "JPEG_FOLDER"),
    )
    parser.add_argument(
        "--dry-run-import",
        nargs=5,
        metavar=("YEAR", "PROJECT", "DAY", "RAW_FOLDER", "JPEG_FOLDER"),
    )
    parser.add_argument(
        "--import",
        dest="real_import",
        nargs=5,
        metavar=("YEAR", "PROJECT", "DAY", "RAW_FOLDER", "JPEG_FOLDER"),
    )
    parser.add_argument(
        "--copy-one",
        nargs=2,
        metavar=("SOURCE", "DESTINATION"),
    )
    parser.add_argument("--show-config", action="store_true")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args(argv)

    logger = configure_logging()
    logger.info("Mac Photo Studio starting")

    try:
        if args.command == "import":
            return run_interactive_import_command()
        if args.command == "darktable-complete-export":
            if len(args.command_args) != 2:
                parser.error(
                    "darktable-complete-export requires "
                    "SOURCE and OUTPUT paths"
                )

            return print_darktable_export_completion(
                source_path=args.command_args[0],
                output_path=args.command_args[1],
            )

        if args.command == "digikam-darktable":
            if len(args.command_args) != 1:
                parser.error(
                    "digikam-darktable requires exactly one PHOTO path"
                )

            return print_digikam_darktable_handoff(
                args.command_args[0]
            )

        workflow_commands = {
            "digikam-derivative": ("digikam", "derivative"),
            "digikam-export": ("digikam", "export"),
            "darktable-edit": ("darktable", "edit"),
            "darktable-export": ("darktable", "export"),
        }

        if args.command in workflow_commands:
            if len(args.command_args) != 2:
                parser.error(
                    f"{args.command} requires SOURCE and OUTPUT paths"
                )

            application, action = workflow_commands[
                args.command
            ]

            return print_application_workflow_action(
                application=application,
                action=action,
                source_path=args.command_args[0],
                output_path=args.command_args[1],
            )

        if args.command in {
            "record-edit",
            "record-export",
        }:
            if len(args.command_args) != 2:
                parser.error(
                    f"{args.command} requires SOURCE and OUTPUT paths"
                )

            event_type = (
                "edit"
                if args.command == "record-edit"
                else "export"
            )

            return print_record_photo_action(
                source_path=args.command_args[0],
                output_path=args.command_args[1],
                event_type=event_type,
            )
        if args.command == "photo-history":
            if len(args.command_args) != 1:
                parser.error(
                    "photo-history requires exactly one PHOTO path"
                )

            return print_photo_history(
                args.command_args[0]
            )
        if args.command == "verify-photo":
            if len(args.command_args) != 1:
                parser.error(
                    "verify-photo requires exactly one PHOTO path"
                )

            return print_verify_photo(
                args.command_args[0]
            )
        if args.version:
            print(get_version())
            return 0
        if args.health:
            return print_health()
        if args.scan_cards:
            return print_scan_cards()
        if args.scan_path:
            return print_scan_path(args.scan_path)
        if args.analyze_culling:
            return print_analyze_culling(
                args.analyze_culling
            )
        if args.confirm_culling:
            return print_confirm_culling(
                args.confirm_culling[0],
                args.confirm_culling[1],
            )
        if args.pair_paths:
            return print_pair_paths(
                args.pair_paths[0],
                args.pair_paths[1],
            )
        if args.plan_import:
            return print_import_plan(
                int(args.plan_import[0]),
                args.plan_import[1],
                args.plan_import[2],
                args.plan_import[3],
                args.plan_import[4],
            )
        if args.dry_run_import:
            return print_dry_run_import(
                int(args.dry_run_import[0]),
                args.dry_run_import[1],
                args.dry_run_import[2],
                args.dry_run_import[3],
                args.dry_run_import[4],
            )
        if args.real_import:
            return run_real_import(
                int(args.real_import[0]),
                args.real_import[1],
                args.real_import[2],
                args.real_import[3],
                args.real_import[4],
            )
        if args.copy_one:
            return print_copy_one(
                args.copy_one[0],
                args.copy_one[1],
            )
        if args.show_config:
            return show_config()
        if args.gui:
            run_gui()
            return 0

        print(f"Mac Photo Studio {get_version()}")
        print("Environment-aware foundation installed.")
        print()
        print("Useful commands:")
        print("  mac-photo-studio import")
        print("  mac-photo-studio --health")
        print("  mac-photo-studio --scan-cards")
        print("  mac-photo-studio --scan-path <folder>")
        print(
            "  mac-photo-studio --analyze-culling "
            "<import-session-folder>"
        )
        print(
            "  mac-photo-studio --confirm-culling "
            "<import-session-folder> <photo-stem>"
        )
        print(
            "  mac-photo-studio --pair-paths "
            "<raw-folder> <jpeg-folder>"
        )
        print(
            "  mac-photo-studio --plan-import "
            "<year> <project> <day> <raw-folder> <jpeg-folder>"
        )
        print(
            "  mac-photo-studio --dry-run-import "
            "<year> <project> <day> <raw-folder> <jpeg-folder>"
        )
        print(
            "  mac-photo-studio --import "
            "<year> <project> <day> <raw-folder> <jpeg-folder>"
        )
        print(
            "  mac-photo-studio --copy-one "
            "<source> <destination>"
        )
        print("  mac-photo-studio --show-config")
        print("  mac-photo-studio --gui")
        print("  mac-photo-studio --version")
        return 0

    except MacPhotoStudioError as exc:
        logger.error(str(exc))
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
