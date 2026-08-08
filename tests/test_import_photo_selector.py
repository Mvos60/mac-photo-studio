from datetime import date, datetime
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


class TextVariable:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


def _summary_selector(candidates, selected_keys):
    selector = ImportPhotoSelector.__new__(ImportPhotoSelector)
    selector._candidates = candidates
    selector._variables = {
        candidate.key: Variable(candidate.key in selected_keys)
        for candidate in candidates
    }
    selector._session_date = date(2026, 8, 2)
    selector._summary_variables = {
        key: TextVariable()
        for key in ("selection", "exif_label", "session", "range", "status")
    }
    selector._result = None
    selector._dialog = Dialog()
    selector._window = object()
    selector._refresh_summary()
    return selector


def _candidate(key, captured_at=None, *, conflict=False):
    return ImportPhotoCandidate(
        key, key.upper(), raw_paths=(Path(f"{key}.ARW"),),
        captured_at=captured_at, captured_at_conflict=conflict,
    )


def test_zero_selected_is_explicit_and_neutral():
    candidates = tuple(_candidate(str(index)) for index in range(4))
    selector = _summary_selector(candidates, set())
    assert selector._summary_variables["selection"].get() == "0 van 4 opnamen"
    assert selector._summary_variables["exif_label"].get() == "EXIF-selectie:"
    assert selector._summary_variables["range"].get() == "—"
    assert selector._summary_variables["status"].get() == "Geen opnamen geselecteerd."


def test_one_of_four_uses_singular_label_value_and_match_status():
    candidates = (
        _candidate("one", datetime(2026, 8, 2, 16, 31)),
        _candidate("two"), _candidate("three"), _candidate("four"),
    )
    selector = _summary_selector(candidates, {"one"})
    assert selector._summary_variables["selection"].get() == "1 van 4 opnamen"
    assert selector._summary_variables["exif_label"].get() == "EXIF-opname:"
    assert selector._summary_variables["range"].get() == "02-08-2026 16:31"
    assert "→" not in selector._summary_variables["range"].get()
    assert selector._summary_variables["status"].get() == (
        "✓ De geselecteerde opname komt overeen met de sessiedatum."
    )


def test_multiple_selected_use_range_and_explicit_match_status():
    candidates = (
        _candidate("one", datetime(2026, 8, 2, 16, 31)),
        _candidate("two", datetime(2026, 8, 2, 16, 56)),
        _candidate("three"), _candidate("four"),
    )
    selector = _summary_selector(candidates, {"one", "two"})
    assert selector._summary_variables["selection"].get() == "2 van 4 opnamen"
    assert selector._summary_variables["exif_label"].get() == "EXIF-selectie:"
    assert selector._summary_variables["range"].get() == (
        "02-08-2026 16:31 → 02-08-2026 16:56"
    )
    assert selector._summary_variables["status"].get() == (
        "✓ Alle geselecteerde opnamen met een leesbare EXIF-datum "
        "komen overeen met de sessiedatum."
    )


def test_status_counts_single_and_multiple_mismatches():
    candidates = (
        _candidate("match", datetime(2026, 8, 2, 12)),
        _candidate("first", datetime(2026, 8, 3, 12)),
        _candidate("second", datetime(2026, 8, 4, 12)),
        _candidate("four", datetime(2026, 8, 2, 13)),
    )
    single = _summary_selector(candidates, {"match", "first", "four"})
    assert "⚠ 1 van de 3 geselecteerde opnamen wijkt af van de sessiedatum." in single._summary_variables["status"].get()
    multiple = _summary_selector(candidates, {candidate.key for candidate in candidates})
    assert "⚠ 2 van de 4 geselecteerde opnamen wijken af van de sessiedatum." in multiple._summary_variables["status"].get()
    assert "4 geselecteerde opnamen vallen op 3 kalenderdagen" in multiple._summary_variables["status"].get()


def test_status_counts_single_and_multiple_unknown_dates():
    candidates = (
        _candidate("known", datetime(2026, 8, 2, 12)),
        _candidate("first"), _candidate("second"), _candidate("other", datetime(2026, 8, 2, 13)),
    )
    single = _summary_selector(candidates, {"known", "first", "other"})
    assert "⚠ 1 van de 3 geselecteerde opnamen heeft geen leesbare opnamedatum." in single._summary_variables["status"].get()
    multiple = _summary_selector(candidates, {candidate.key for candidate in candidates})
    assert "⚠ 2 van de 4 geselecteerde opnamen hebben geen leesbare opnamedatum." in multiple._summary_variables["status"].get()


def test_status_counts_single_and_multiple_raw_jpeg_conflicts():
    candidates = (
        _candidate("known", datetime(2026, 8, 2, 12)),
        _candidate("first", conflict=True), _candidate("second", conflict=True),
        _candidate("other", datetime(2026, 8, 2, 13)),
    )
    single = _summary_selector(candidates, {"known", "first", "other"})
    assert "⚠ 1 van de 3 geselecteerde opnamen heeft tegenstrijdige RAW/JPG-opnamedatums." in single._summary_variables["status"].get()
    multiple = _summary_selector(candidates, {candidate.key for candidate in candidates})
    assert "⚠ 2 van de 4 geselecteerde opnamen hebben tegenstrijdige RAW/JPG-opnamedatums." in multiple._summary_variables["status"].get()


def test_summary_refreshes_after_selection_change_and_confirm_still_works():
    candidates = (
        _candidate("one", datetime(2026, 8, 2, 16, 31)),
        _candidate("two", datetime(2026, 8, 2, 16, 56)),
        _candidate("three"), _candidate("four"),
    )
    selector = _summary_selector(candidates, {candidate.key for candidate in candidates})
    selector._variables["two"].set(False)
    selector._variables["three"].set(False)
    selector._variables["four"].set(False)
    selector._refresh_summary()
    assert selector._summary_variables["selection"].get() == "1 van 4 opnamen"
    assert selector._summary_variables["exif_label"].get() == "EXIF-opname:"
    selector.confirm()
    assert selector._result is not None
    assert selector._result.selected_keys == frozenset({"one"})


def test_summary_without_session_date_is_safe():
    selector = _summary_selector((_candidate("one"),), {"one"})
    selector._session_date = None
    selector._refresh_summary()
    assert selector._summary_variables["session"].get() == "—"
