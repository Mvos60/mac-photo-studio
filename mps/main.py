from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mps.config import load_settings
from mps.exceptions import MacPhotoStudioError
from mps.gui.app import run_gui
from mps.logger import configure_logging
from mps.services.card_scanner import format_bytes, scan_cards, scan_path
from mps.services.cli_output import print_card_summary, print_decision_preview
from mps.services.health import run_health_checks
from mps.services.import_engine import run_import
from mps.services.import_planner import create_import_decision, create_import_plan
from mps.services.pairing import pair_paths
from mps.services.safe_copy import copy_one_file
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
    settings = load_settings()
    plan = create_import_plan(
        year=year,
        project=project,
        day=day,
        raw_folder=Path(raw_folder),
        jpeg_folder=Path(jpeg_folder),
        settings=settings,
    )
    decision = create_import_decision(plan)
    return plan, decision


def print_import_plan(year: int, project: str, day: str, raw_folder: str, jpeg_folder: str) -> int:
    plan, decision = build_import_decision(year, project, day, raw_folder, jpeg_folder)

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


def print_dry_run_import(year: int, project: str, day: str, raw_folder: str, jpeg_folder: str) -> int:
    plan, decision = build_import_decision(year, project, day, raw_folder, jpeg_folder)

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


def run_real_import(year: int, project: str, day: str, raw_folder: str, jpeg_folder: str) -> int:
    plan, decision = build_import_decision(year, project, day, raw_folder, jpeg_folder)
    log_path = decision.destination / "mps_import.log"

    print("Mac Photo Studio Import")
    print("=" * 23)
    print(f"Year:         {plan.year}")
    print(f"Project:      {plan.project}")
    print(f"Day/session:  {plan.day}")
    print(f"Destination:  {decision.destination}")
    print()
    print("Starting verified copy...")

    result = run_import(
        decision,
        dry_run=False,
        log_path=log_path,
        write_provenance=True,
        camera_model="Unknown camera",
        manifest_path=decision.destination / "import_manifest.json",
    )

    print()
    print("Import Summary")
    print("--------------")
    print(f"Copied:       {result.copied}")
    print(f"Failed:       {result.failed}")
    print(f"Skipped:      {result.skipped}")
    print(f"Success:      {result.success}")
    print(f"Log:          {result.log_path}")

    return 0 if result.success else 1


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


def show_config() -> int:
    settings = load_settings()
    print(json.dumps(settings.data, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mac-photo-studio")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--scan-cards", action="store_true")
    parser.add_argument("--scan-path")
    parser.add_argument("--pair-paths", nargs=2, metavar=("RAW_FOLDER", "JPEG_FOLDER"))
    parser.add_argument("--plan-import", nargs=5, metavar=("YEAR", "PROJECT", "DAY", "RAW_FOLDER", "JPEG_FOLDER"))
    parser.add_argument("--dry-run-import", nargs=5, metavar=("YEAR", "PROJECT", "DAY", "RAW_FOLDER", "JPEG_FOLDER"))
    parser.add_argument("--import", dest="real_import", nargs=5, metavar=("YEAR", "PROJECT", "DAY", "RAW_FOLDER", "JPEG_FOLDER"))
    parser.add_argument("--copy-one", nargs=2, metavar=("SOURCE", "DESTINATION"))
    parser.add_argument("--show-config", action="store_true")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args(argv)

    logger = configure_logging()
    logger.info("Mac Photo Studio starting")

    try:
        if args.version:
            print(get_version())
            return 0
        if args.health:
            return print_health()
        if args.scan_cards:
            return print_scan_cards()
        if args.scan_path:
            return print_scan_path(args.scan_path)
        if args.pair_paths:
            return print_pair_paths(args.pair_paths[0], args.pair_paths[1])
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
            return print_copy_one(args.copy_one[0], args.copy_one[1])
        if args.show_config:
            return show_config()
        if args.gui:
            run_gui()
            return 0

        print(f"Mac Photo Studio {get_version()}")
        print("Environment-aware foundation installed.")
        print()
        print("Useful commands:")
        print("  mac-photo-studio --health")
        print("  mac-photo-studio --scan-cards")
        print("  mac-photo-studio --scan-path <folder>")
        print("  mac-photo-studio --pair-paths <raw-folder> <jpeg-folder>")
        print("  mac-photo-studio --plan-import <year> <project> <day> <raw-folder> <jpeg-folder>")
        print("  mac-photo-studio --dry-run-import <year> <project> <day> <raw-folder> <jpeg-folder>")
        print("  mac-photo-studio --import <year> <project> <day> <raw-folder> <jpeg-folder>")
        print("  mac-photo-studio --copy-one <source> <destination>")
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
