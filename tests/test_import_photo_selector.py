from pathlib import Path

from mps.gui.import_photo_selector import ImportPhotoSelector
from mps.models.import_photo_selection import ImportPhotoCandidate


class Variable:
    def __init__(self, value: bool):
        self.value = value

    def get(self) -> bool:
        return self.value

    def set(self, value: bool) -> None:
        self.value = value


class Dialog:
    def __init__(self):
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _selector() -> ImportPhotoSelector:
    selector = ImportPhotoSelector.__new__(ImportPhotoSelector)
    selector._candidates = (
        ImportPhotoCandidate("one", "ONE", raw_paths=(Path("ONE.ARW"),)),
        ImportPhotoCandidate("two", "TWO", jpeg_paths=(Path("TWO.JPG"),)),
    )
    selector._variables = {"one": Variable(True), "two": Variable(True)}
    selector._result = None
    selector._dialog = Dialog()
    selector._window = object()
    return selector


def test_selector_defaults_all_candidates_to_selected():
    selector = _selector()

    assert all(variable.get() for variable in selector._variables.values())


def test_select_all_and_none_update_every_candidate():
    selector = _selector()

    selector.select_none()
    assert not any(variable.get() for variable in selector._variables.values())

    selector.select_all()
    assert all(variable.get() for variable in selector._variables.values())


def test_confirm_returns_only_selected_candidate_paths():
    selector = _selector()
    selector._variables["two"].set(False)

    selector.confirm()

    assert selector._result is not None
    assert selector._result.selected_keys == frozenset({"one"})
    assert selector._result.selected_paths(selector._candidates) == (
        Path("ONE.ARW"),
    )
    assert selector._dialog.closed


def test_empty_selection_stays_open(monkeypatch):
    selector = _selector()
    selector.select_none()
    warnings = []
    monkeypatch.setattr(
        "mps.gui.import_photo_selector.messagebox.showwarning",
        lambda *args, **kwargs: warnings.append((args, kwargs)),
    )

    selector.confirm()

    assert selector._result is None
    assert not selector._dialog.closed
    assert warnings


def test_cancel_returns_no_selection_and_closes():
    selector = _selector()

    selector.cancel()

    assert selector._result is None
    assert selector._dialog.closed
