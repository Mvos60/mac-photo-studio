from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mps.models.import_destination_selection import ImportDestinationSelection


def selection(**overrides) -> ImportDestinationSelection:
    values = {
        "year": 2026,
        "month_day": "08-01",
        "project": "Adriatic",
        "description": "Ljubljana",
    }
    values.update(overrides)
    return ImportDestinationSelection(**values)


def test_valid_selection_is_immutable() -> None:
    result = selection()

    assert result.year == 2026
    assert result.month_day == "08-01"
    assert result.project == "Adriatic"
    assert result.description == "Ljubljana"

    with pytest.raises(FrozenInstanceError):
        result.project = "Other"


def test_month_day_and_directory_values() -> None:
    result = selection()

    assert result.month == "08"
    assert result.day == "01"
    assert result.day_directory == "01_Ljubljana"
    assert result.day_session == "08-01_Ljubljana"


def test_empty_description_uses_day_only() -> None:
    result = selection(description="")

    assert result.day_directory == "01"
    assert result.day_session == "08-01"


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        (
            "Ljubljana",
            Path("/home/mac/Pictures/2026/08/01_Ljubljana/Adriatic"),
        ),
        ("", Path("/home/mac/Pictures/2026/08/01/Adriatic")),
    ],
)
def test_calendar_first_destination_path(
    description: str,
    expected: Path,
) -> None:
    assert selection(description=description).destination_path(
        "/home/mac/Pictures"
    ) == expected


def test_destination_uses_alternate_photos_root(tmp_path: Path) -> None:
    root = tmp_path / "Archive"

    assert selection().destination_path(root) == (
        root / "2026" / "08" / "01_Ljubljana" / "Adriatic"
    )


def test_destination_expands_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))

    assert selection().destination_path("~/Pictures") == (
        tmp_path
        / "Pictures"
        / "2026"
        / "08"
        / "01_Ljubljana"
        / "Adriatic"
    )


def test_destination_preview_does_not_create_directory(tmp_path: Path) -> None:
    destination = selection().destination_path(tmp_path / "Pictures")

    assert not destination.exists()
    assert not (tmp_path / "Pictures").exists()


@pytest.mark.parametrize("value", ["8-01", "08-1", "0801", "08/01", " 08-01 "])
def test_invalid_month_day_format_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="MM-DD"):
        selection(month_day=value)


@pytest.mark.parametrize("value", ["00-01", "13-01", "04-31", "02-30"])
def test_impossible_date_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="not valid"):
        selection(month_day=value)


def test_leap_year_is_validated() -> None:
    assert selection(year=2028, month_day="02-29").day == "29"

    with pytest.raises(ValueError, match="not valid"):
        selection(year=2026, month_day="02-29")


@pytest.mark.parametrize("value", [True, 999, 10000, "2026"])
def test_invalid_year_is_rejected(value) -> None:
    with pytest.raises(ValueError, match="four-digit"):
        selection(year=value)


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_project_is_rejected(value: str) -> None:
    with pytest.raises(ValueError, match="required"):
        selection(project=value)


@pytest.mark.parametrize(
    "value",
    [".", "..", "A/B", "A\\B", "A\0B", "A\nB", "A\tB"],
)
def test_unsafe_project_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        selection(project=value)


@pytest.mark.parametrize(
    "value",
    [".", "..", "A/B", "A\\B", "A\0B", "A\nB", "A\tB"],
)
def test_unsafe_description_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        selection(description=value)


def test_outer_whitespace_is_trimmed_without_rewriting_text() -> None:
    result = selection(
        project="  Adriatic Journey  ",
        description="  Ljubljana Old Town  ",
    )

    assert result.project == "Adriatic Journey"
    assert result.description == "Ljubljana Old Town"
    assert result.day_directory == "01_Ljubljana Old Town"
