from __future__ import annotations

from mps.services.card_scanner import format_bytes


def print_card_summary(card, indent: str = "") -> None:
    print(f"{indent}Root:          {card.root}")
    print(f"{indent}DCIM:          {card.dcim_path or 'not found'}")
    print(f"{indent}RAW:           {card.raw_count}")
    print(f"{indent}JPEG:          {card.jpeg_count}")
    print(f"{indent}HEIF:          {card.heif_count}")
    print(f"{indent}Video:         {card.video_count}")
    print()
    print(f"{indent}Pairs:         {card.pair_count}")
    print(f"{indent}RAW orphans:   {card.orphan_raw_count}")
    print(f"{indent}JPEG orphans:  {card.orphan_jpeg_count}")
    print()
    print(f"{indent}Other:         {card.other_count}")
    print(f"{indent}Size:          {format_bytes(card.total_size_bytes)}")


def print_decision_preview(decision) -> None:
    print("Decision")
    print(f"  Files:      {decision.total_files}")
    print(f"  Size:       {format_bytes(decision.estimated_size_bytes)}")
    print(f"  Operations: {len(decision.copy_operations)}")
    print()

    print("Copy preview")
    if decision.copy_operations:
        for operation in decision.copy_operations[:10]:
            print(f"  {operation.source}")
            print(f"    -> {operation.destination}")
        if len(decision.copy_operations) > 10:
            print(f"  ... and {len(decision.copy_operations) - 10} more")
    else:
        print("  None")
    print()

    print("Warnings")
    if decision.warnings:
        for warning in decision.warnings:
            print(f"  - {warning}")
    else:
        print("  None")
    print()
