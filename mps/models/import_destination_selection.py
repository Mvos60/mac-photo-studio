from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import unicodedata


_MONTH_DAY_PATTERN = re.compile(r"[0-9]{2}-[0-9]{2}")


def _safe_segment(value: str, *, label: str, required: bool) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")

    trimmed = value.strip()

    if not trimmed:
        if required:
            raise ValueError(f"{label} is required")
        return ""

    if trimmed in {".", ".."}:
        raise ValueError(f"{label} is not a safe path segment")

    if "/" in trimmed or "\\" in trimmed:
        raise ValueError(f"{label} must not contain path separators")

    if any(unicodedata.category(character).startswith("C") for character in trimmed):
        raise ValueError(f"{label} must not contain control characters")

    return trimmed


@dataclass(frozen=True, slots=True)
class ImportDestinationSelection:
    year: int
    month_day: str
    project: str
    description: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise ValueError("Year must be a four-digit integer")

        if self.year < 1000 or self.year > 9999:
            raise ValueError("Year must be a four-digit integer")

        if not isinstance(self.month_day, str) or not _MONTH_DAY_PATTERN.fullmatch(
            self.month_day
        ):
            raise ValueError("Date must use MM-DD format")

        month_text, day_text = self.month_day.split("-", maxsplit=1)

        try:
            date(self.year, int(month_text), int(day_text))
        except ValueError as exc:
            raise ValueError("Date is not valid for the selected year") from exc

        object.__setattr__(
            self,
            "project",
            _safe_segment(self.project, label="Project", required=True),
        )
        object.__setattr__(
            self,
            "description",
            _safe_segment(
                self.description,
                label="Description",
                required=False,
            ),
        )

    @property
    def month(self) -> str:
        return self.month_day[:2]

    @property
    def day(self) -> str:
        return self.month_day[3:]

    @property
    def day_directory(self) -> str:
        if not self.description:
            return self.day
        return f"{self.day}_{self.description}"

    @property
    def day_session(self) -> str:
        if not self.description:
            return self.month_day
        return f"{self.month_day}_{self.description}"

    def destination_path(self, photos_root: str | Path) -> Path:
        root = Path(photos_root).expanduser()
        return (
            root
            / str(self.year)
            / self.month
            / self.day_directory
            / self.project
        )
