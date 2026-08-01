import inspect
from pathlib import Path

from mps.gui import import_destination_selector as selector_module
from mps.gui.import_destination_selector import ImportDestinationSelector
from mps.models.import_destination_selection import ImportDestinationSelection


class FakeVariable:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class FakeDialog:
    def __init__(self) -> None:
        self.window = object()
        self.closed = False

    def close(self) -> None:
        self.closed = True


def selector(photos_root: Path) -> ImportDestinationSelector:
    instance = ImportDestinationSelector.__new__(ImportDestinationSelector)
    instance._photos_root = photos_root
    instance._result = None
    instance._dialog = FakeDialog()
    instance._year_var = FakeVariable("2026")
    instance._month_day_var = FakeVariable("08-01")
    instance._project_var = FakeVariable("Adriatic")
    instance._description_var = FakeVariable("Ljubljana")
    instance._destination_var = FakeVariable()
    return instance


def test_selector_uses_mps_dialog_and_contains_visible_labels() -> None:
    source = inspect.getsource(selector_module)

    assert "MpsDialog(" in source
    assert 'size="wide"' in source
    for label in (
        "Year",
        "Date (MM-DD)",
        "Project",
        "Description / session name (optional)",
        "Destination",
    ):
        assert f'"{label}"' in source


def test_selector_receives_photos_root() -> None:
    signature = inspect.signature(ImportDestinationSelector)

    assert "photos_root" in signature.parameters


def test_selector_shows_calendar_first_preview(tmp_path: Path) -> None:
    instance = selector(tmp_path / "Pictures")

    instance._update_preview()

    assert instance._destination_var.get() == str(
        tmp_path
        / "Pictures"
        / "2026"
        / "08"
        / "01_Ljubljana"
        / "Adriatic"
    )


def test_preview_updates_for_every_input_field(tmp_path: Path) -> None:
    instance = selector(tmp_path / "Pictures")

    changes = (
        (instance._year_var, "2027", "2027/08/01_Ljubljana/Adriatic"),
        (instance._month_day_var, "09-02", "2027/09/02_Ljubljana/Adriatic"),
        (instance._project_var, "Baltic", "2027/09/02_Ljubljana/Baltic"),
        (instance._description_var, "Riga", "2027/09/02_Riga/Baltic"),
    )

    for variable, value, suffix in changes:
        variable.set(value)
        instance._update_preview()
        assert instance._destination_var.get().endswith(suffix)


def test_valid_confirmation_returns_exact_model(tmp_path: Path) -> None:
    instance = selector(tmp_path / "Pictures")

    instance._confirm()

    assert instance.result == ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
        description="Ljubljana",
    )
    assert instance._dialog.closed is True


def test_invalid_confirmation_shows_error_and_keeps_dialog_open(
    monkeypatch,
    tmp_path: Path,
) -> None:
    instance = selector(tmp_path / "Pictures")
    instance._month_day_var.set("02-30")
    errors = []

    monkeypatch.setattr(
        selector_module.messagebox,
        "showerror",
        lambda title, message, **kwargs: errors.append((title, message, kwargs)),
    )

    instance._confirm()

    assert instance.result is None
    assert instance._dialog.closed is False
    assert errors[0][0] == "Invalid Import Destination"


def test_cancel_returns_none(tmp_path: Path) -> None:
    instance = selector(tmp_path / "Pictures")
    instance._result = ImportDestinationSelection(
        year=2026,
        month_day="08-01",
        project="Adriatic",
    )

    instance._cancel()

    assert instance.result is None
    assert instance._dialog.closed is True


def test_selector_has_no_writes_or_import_action(tmp_path: Path) -> None:
    source = inspect.getsource(selector_module)
    instance = selector(tmp_path / "Pictures")

    instance._update_preview()

    assert ".mkdir(" not in source
    assert ".write_" not in source
    assert "run_import" not in source
    assert "launch_cli" not in source
    assert not (tmp_path / "Pictures").exists()
