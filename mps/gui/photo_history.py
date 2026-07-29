from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from mps.gui.dialogs import (
    BODY_ITALIC_FONT,
    MpsDialog,
)


@dataclass(frozen=True, slots=True)
class HistoryTimelineEntry:
    number: int
    event_type: str
    created_at: str = ""
    application: str = ""
    camera: str = ""
    description: str = ""
    output_path: str = ""


_EVENT_HEADER = re.compile(
    r"^\s*(?P<number>\d+)\.\s+(?P<event>[A-Za-z0-9_-]+)\s*$"
)
_EVENT_FIELD = re.compile(
    r"^\s+(?P<label>Time|Application|Camera|Output):\s*(?P<value>.*)$"
)


def run_photo_history(photo: Path) -> tuple[int, str]:
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "mps.main",
            "photo-history",
            str(photo),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    output = "\n".join(
        part.strip()
        for part in (
            process.stdout,
            process.stderr,
        )
        if part.strip()
    )
    return process.returncode, output


def history_state(
    returncode: int,
    output: str,
) -> tuple[str, str]:
    normalized = output.upper()

    if any(
        marker in normalized
        for marker in (
            "NOT INSIDE A MANAGED PROVENANCE IMPORT",
            "NOT MANAGED",
            "NO CERTIFICATE",
        )
    ):
        return (
            "NOT MANAGED BY MPS",
            (
                "This photograph was found, but MPS could not link "
                "it to a verified MPS import. This does not mean "
                "that the photograph was altered or is AI-generated."
            ),
        )

    if any(
        marker in normalized
        for marker in (
            "HASH MISMATCH",
            "SHA-256 DOES NOT MATCH",
            "DOES NOT MATCH RECORDED IDENTITY",
            "HASH CONTINUITY MISMATCH",
            "INVALID",
        )
    ):
        return (
            "CHANGED OR INVALID HISTORY",
            (
                "MPS found provenance information, but the current "
                "file or its recorded event chain does not fully match."
            ),
        )

    if returncode == 0 and (
        "STATUS:        TRUSTED" in normalized
        or "STATUS: TRUSTED" in normalized
    ):
        return (
            "TRUSTED HISTORY",
            (
                "MPS found a valid recorded history for this "
                "photograph. The timeline below shows the events "
                "that MPS has recorded."
            ),
        )

    if returncode == 0:
        return (
            "HISTORY AVAILABLE",
            (
                "MPS found recorded history information. "
                "Review the timeline below."
            ),
        )

    return (
        "HISTORY UNAVAILABLE",
        (
            "MPS could not display a complete recorded history. "
            "Review the raw history details."
        ),
    )


def event_label(event_type: str) -> str:
    labels = {
        "capture": "Captured",
        "ingest": "Imported",
        "edit": "Edited",
        "derivative": "Derivative created",
        "export": "Exported",
    }
    normalized = event_type.strip().casefold()

    if normalized in labels:
        return labels[normalized]

    return normalized.replace("_", " ").replace("-", " ").title()


def readable_event_time(value: str) -> str:
    cleaned = value.strip()

    if not cleaned:
        return "Time not recorded"

    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + " UTC"

    return cleaned.replace("T", " ", 1)


def parse_history_timeline(
    output: str,
) -> tuple[HistoryTimelineEntry, ...]:
    entries: list[HistoryTimelineEntry] = []
    current: dict[str, str | int] | None = None
    description_lines: list[str] = []

    def finish_current() -> None:
        nonlocal current, description_lines

        if current is None:
            return

        current["description"] = " ".join(
            part.strip()
            for part in description_lines
            if part.strip()
        )
        entries.append(
            HistoryTimelineEntry(
                number=int(current["number"]),
                event_type=str(current["event_type"]),
                created_at=str(current.get("created_at", "")),
                application=str(current.get("application", "")),
                camera=str(current.get("camera", "")),
                description=str(current.get("description", "")),
                output_path=str(current.get("output_path", "")),
            )
        )
        current = None
        description_lines = []

    for line in output.splitlines():
        header = _EVENT_HEADER.match(line)

        if header is not None:
            finish_current()
            current = {
                "number": int(header.group("number")),
                "event_type": header.group("event"),
            }
            continue

        if current is None:
            continue

        field = _EVENT_FIELD.match(line)

        if field is not None:
            label = field.group("label")
            value = field.group("value").strip()
            keys = {
                "Time": "created_at",
                "Application": "application",
                "Camera": "camera",
                "Output": "output_path",
            }
            current[keys[label]] = value
            continue

        stripped = line.strip()

        if stripped:
            description_lines.append(stripped)

    finish_current()
    return tuple(entries)


def timeline_summary(
    entries: tuple[HistoryTimelineEntry, ...],
) -> str:
    count = len(entries)

    if count == 0:
        return "No recorded provenance events"

    noun = "event" if count == 1 else "events"
    journey = "  →  ".join(
        event_label(entry.event_type)
        for entry in entries
    )
    return f"{count} recorded {noun}\n{journey}"


def build_timeline_text(
    entries: tuple[HistoryTimelineEntry, ...],
) -> str:
    if not entries:
        return (
            "No recorded provenance events are available for this "
            "photograph.\n\nOpen Raw History Details for the exact "
            "technical result returned by MPS."
        )

    lines = [
        timeline_summary(entries),
        "",
    ]

    for entry in entries:
        lines.append(
            f"{entry.number}. {event_label(entry.event_type)}"
        )
        lines.append(
            f"   When: {readable_event_time(entry.created_at)}"
        )

        if entry.application:
            lines.append(
                f"   Application: {entry.application}"
            )

        if entry.camera:
            lines.append(
                f"   Camera: {entry.camera}"
            )

        if entry.description:
            lines.append(
                f"   Details: {entry.description}"
            )

        if entry.output_path:
            lines.append(
                f"   Output: {entry.output_path}"
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _readonly_text(
    parent: tk.Misc,
    content: str,
    *,
    font: tuple[str, int] | tuple[str, int, str] = (
        "Sans",
        11,
    ),
) -> tk.Text:
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)

    text = tk.Text(
        parent,
        wrap="word",
        padx=16,
        pady=14,
        font=font,
    )
    scrollbar = ttk.Scrollbar(
        parent,
        orient="vertical",
        command=text.yview,
    )
    text.configure(
        yscrollcommand=scrollbar.set,
    )

    text.grid(
        row=0,
        column=0,
        sticky="nsew",
    )
    scrollbar.grid(
        row=0,
        column=1,
        sticky="ns",
    )

    text.insert(
        "1.0",
        content,
    )
    text.configure(state="disabled")
    return text


class PhotoHistoryDialog:
    def __init__(
        self,
        parent: tk.Misc,
        photo: Path,
    ) -> None:
        self._choose_another = False

        self._dialog = MpsDialog(
            parent,
            title="Photo History",
            size="medium",
        )
        self._window = self._dialog.window

        self._window.geometry("1180x940")
        self._window.minsize(980, 800)

        self._dialog.add_header(
            "Photo History",
            (
                "This shows the provenance events that MPS has "
                "recorded for the selected photograph. It does not "
                "change the photograph or its history."
            ),
            wraplength=760,
        )

        ttk.Label(
            self._dialog.header,
            text=str(photo),
            font=BODY_ITALIC_FONT,
            justify="left",
            wraplength=760,
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

        content = self._dialog.content
        content.rowconfigure(1, weight=1)

        returncode, output = run_photo_history(photo)
        state, explanation = history_state(
            returncode,
            output,
        )
        entries = parse_history_timeline(output)

        status_box = self._dialog.create_section(
            content,
            title="MPS Status",
            padding=(14, 12),
        )
        status_box.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )

        ttk.Label(
            status_box,
            text=state,
            font=("Sans", 14, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            status_box,
            text=explanation,
            justify="left",
            wraplength=720,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        history_box = self._dialog.create_section(
            content,
            title="Photograph Journey",
            padding=(10, 10),
        )
        history_box.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        history_box.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(history_box)
        notebook.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        timeline_tab = ttk.Frame(
            notebook,
            padding=(8, 8),
        )
        raw_tab = ttk.Frame(
            notebook,
            padding=(8, 8),
        )

        notebook.add(
            timeline_tab,
            text="Readable Timeline",
        )
        notebook.add(
            raw_tab,
            text="Raw History Details",
        )

        _readonly_text(
            timeline_tab,
            build_timeline_text(entries),
            font=("Sans", 12),
        )
        _readonly_text(
            raw_tab,
            output or "No raw history details were returned.",
            font=("Monospace", 10),
        )

        self._dialog.add_footer_button(
            text="Choose another photograph",
            command=self._choose_another_photo,
            column=0,
        )
        self._dialog.add_close_button()
        self._dialog.show()
        self._window.update_idletasks()
        self._window.lift()
        self._window.focus_force()
        self._window.wait_window()

    @property
    def choose_another(self) -> bool:
        return self._choose_another

    def _choose_another_photo(self) -> None:
        self._choose_another = True
        self._dialog.close()


def show_photo_history(
    parent: tk.Misc,
    photo: Path,
) -> bool:
    try:
        dialog = PhotoHistoryDialog(
            parent,
            photo,
        )
        return dialog.choose_another
    except OSError as exc:
        messagebox.showerror(
            "Photo History unavailable",
            (
                "MPS could not open the photograph history.\n\n"
                f"{exc}"
            ),
            parent=parent,
        )
        return False
