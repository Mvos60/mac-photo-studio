from __future__ import annotations

from mps.models.import_media_selection import ImportMediaSelection


def build_media_report(
    selection: ImportMediaSelection,
) -> str:
    lines = [
        "Searching for photo media...",
        "",
    ]

    if selection.empty:
        lines.append("No photo media found.")
        return "\n".join(lines)

    lines.append(
        f"Photo sources found: {selection.source_count}"
    )
    lines.append("")

    for index, source in enumerate(
        selection.sources,
        start=1,
    ):
        lines.extend(
            [
                f"Source {index}",
                f"  {source.root}",
                f"  RAW files : {source.raw_count}",
                f"  JPEG files: {source.jpeg_count}",
                f"  Pairs     : {source.pair_count}",
                "",
            ]
        )

    lines.extend(
        [
            "Current media inventory",
            "-----------------------",
            f"RAW files : {selection.total_raw_files}",
            f"JPEG files: {selection.total_jpeg_files}",
        ]
    )

    return "\n".join(lines)
