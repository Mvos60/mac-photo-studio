from __future__ import annotations

import argparse
import json
import sys

from mps.config import load_settings
from mps.exceptions import MacPhotoStudioError
from mps.gui.app import run_gui
from mps.logger import configure_logging
from mps.services.card_scanner import scan_cards
from mps.services.health import run_health_checks
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
        size_gb = card.total_size_bytes / (1024 ** 3)
        print(f"Card {idx}")
        print(f"  Root:   {card.root}")
        print(f"  DCIM:   {card.dcim_path or 'not found'}")
        print(f"  RAW:    {card.raw_count}")
        print(f"  JPEG:   {card.jpeg_count}")
        print(f"  Other:  {card.other_count}")
        print(f"  Size:   {size_gb:.2f} GB")
        print()

    print("Read-only scan complete. No files were modified.")
    return 0


def show_config() -> int:
    settings = load_settings()
    print(json.dumps(settings.data, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mac-photo-studio")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--scan-cards", action="store_true")
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
