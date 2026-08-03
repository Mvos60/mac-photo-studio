from pathlib import Path

from mps.config import Settings
from mps.gui.legacy_import_resume_dialog import (
    LegacyImportDestination,
    LegacyImportResumeDialog,
)
from mps.services.import_media_batch_planner import media_import_destination


class FakeVariable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeDialog:
    def __init__(self):
        self.closed = False
        self.window = object()

    def close(self):
        self.closed = True


def dialog(settings):
    instance = LegacyImportResumeDialog.__new__(LegacyImportResumeDialog)
    instance._settings = settings
    instance._result = None
    instance._dialog = FakeDialog()
    instance._year_var = FakeVariable("2024")
    instance._project_var = FakeVariable("Legacy Project")
    instance._day_var = FakeVariable("Day 03")
    instance._preview_var = FakeVariable()
    return instance


def test_legacy_values_use_authoritative_destination_calculation(tmp_path: Path):
    settings = Settings({"paths": {"photos_root": str(tmp_path / "Photos")}})
    instance = dialog(settings)
    instance._update_preview()
    values = instance._values()
    assert values == LegacyImportDestination(2024, "Legacy Project", "Day 03")
    assert instance._preview_var.get() == str(media_import_destination(
        settings,
        year=2024,
        project="Legacy Project",
        day="Day 03",
    ))


def test_invalid_year_does_not_confirm(monkeypatch, tmp_path: Path):
    settings = Settings({"paths": {"photos_root": str(tmp_path)}})
    instance = dialog(settings)
    instance._year_var.set("invalid")
    errors = []
    monkeypatch.setattr(
        "mps.gui.legacy_import_resume_dialog.messagebox.showerror",
        lambda *args, **kwargs: errors.append((args, kwargs)),
    )
    instance._confirm()
    assert errors
    assert instance.result is None
    assert instance._dialog.closed is False


def test_cancel_returns_none_without_writes(tmp_path: Path):
    state = tmp_path / "active_import_session.json"
    state.write_bytes(b"unchanged")
    instance = dialog(Settings({"paths": {"photos_root": str(tmp_path)}}))
    instance._cancel()
    assert instance.result is None
    assert state.read_bytes() == b"unchanged"
