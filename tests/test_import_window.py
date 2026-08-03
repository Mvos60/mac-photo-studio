from pathlib import Path

from mps.gui.import_window import EMPTY_VALUE, ImportWindow
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_progress import ImportProgress
from mps.models.import_workflow import ImportEvent, ImportEventType
from mps.services.import_controller import ImportControllerStatus


class FakeVariable:
    def __init__(self, value=EMPTY_VALUE):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeProgressbar:
    def __init__(self):
        self.value = 0

    def configure(self, **kwargs):
        self.value = kwargs["value"]


class FakeWindow:
    def __init__(self):
        self.callbacks = {}
        self.after_calls = 0
        self.cancelled = []
        self.exists = True

    def after(self, interval, callback):
        self.after_calls += 1
        token = f"after-{self.after_calls}"
        self.callbacks[token] = callback
        return token

    def after_cancel(self, token):
        self.cancelled.append(token)
        self.callbacks.pop(token, None)

    def winfo_exists(self):
        return self.exists


class FakeDialog:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeController:
    def __init__(self):
        self.status = ImportControllerStatus.IDLE
        self.events = []

    def drain_events(self):
        events, self.events = self.events, []
        return events


def window():
    instance = ImportWindow.__new__(ImportWindow)
    instance._controller = FakeController()
    instance._poll_interval_ms = 75
    instance._after_id = None
    instance._destroyed = False
    instance._window = FakeWindow()
    instance._dialog = FakeDialog()
    instance._variables = {
        key: FakeVariable("0%" if key == "percentage" else EMPTY_VALUE)
        for key in (
            "status", "session_id", "destination", "action", "source_card",
            "raw", "jpeg", "pairs", "phase", "current_file", "source",
            "progress_destination", "current_total", "percentage", "message",
            "final_status",
        )
    }
    instance._variables["status"].set("idle")
    instance._progressbar = FakeProgressbar()
    return instance


def test_window_initial_values_are_safe_and_poll_starts_once():
    instance = window()
    assert instance._variables["session_id"].get() == EMPTY_VALUE
    instance._schedule_poll()
    instance._schedule_poll()
    assert instance._window.after_calls == 1


def test_poll_processes_queue_in_order_and_reschedules_once():
    instance = window()
    instance._controller.events = [
        ImportEvent(ImportEventType.SESSION_STARTED, {"session_id": "S-1"}),
        ImportEvent(ImportEventType.COMPLETED),
    ]
    instance._schedule_poll()
    callback = instance._window.callbacks[instance._after_id]
    callback()
    assert instance._variables["session_id"].get() == "S-1"
    assert instance._variables["final_status"].get() == "completed"
    assert instance._window.after_calls == 2


def test_structured_session_and_media_fields_are_rendered(tmp_path: Path):
    instance = window()
    destination = tmp_path / "Photos" / "2026"
    card = CardScanResult(
        root=tmp_path / "card", dcim_path=tmp_path / "card" / "DCIM",
        raw_count=3, jpeg_count=2, heif_count=0, video_count=0,
        pair_count=2, orphan_raw_count=1, orphan_jpeg_count=0,
        other_count=0, total_size_bytes=0,
    )
    instance.apply_event(ImportEvent(
        ImportEventType.SESSION_STARTED,
        {"session_id": "S-2", "destination": destination, "action": "resume"},
    ))
    instance.apply_event(ImportEvent(
        ImportEventType.MEDIA_DISCOVERED,
        {"selection": ImportMediaSelection(sources=[card])},
    ))
    assert instance._variables["session_id"].get() == "S-2"
    assert instance._variables["destination"].get() == str(destination)
    assert instance._variables["action"].get() == "resume"
    assert instance._variables["source_card"].get() == str(card.root)
    assert instance._variables["raw"].get() == "3"
    assert instance._variables["jpeg"].get() == "2"
    assert instance._variables["pairs"].get() == "2"


def test_progress_warning_failed_and_completed_are_rendered(tmp_path: Path):
    instance = window()
    progress = ImportProgress(
        current=1, total=4, source=tmp_path / "A.ARW",
        destination=tmp_path / "Photos" / "A.ARW", phase="copying",
    )
    instance.apply_event(ImportEvent(
        ImportEventType.PROGRESS, {"progress": progress}
    ))
    assert instance._variables["phase"].get() == "copying"
    assert instance._variables["current_file"].get() == "A.ARW"
    assert instance._variables["current_total"].get() == "1 / 4"
    assert instance._variables["percentage"].get() == "25%"
    assert instance._progressbar.value == 25

    instance.apply_event(ImportEvent(
        ImportEventType.WARNING, {"message": "Check media"}
    ))
    assert instance._variables["message"].get() == "Check media"
    assert instance._variables["status"].get() != "failed"
    instance.apply_event(ImportEvent(
        ImportEventType.FAILED,
        {"exception_type": "RuntimeError", "message": "copy failed"},
    ))
    assert instance._variables["status"].get() == "failed"
    assert instance._variables["message"].get() == "copy failed"
    instance.apply_event(ImportEvent(ImportEventType.COMPLETED))
    assert instance._variables["final_status"].get() == "completed"


def test_close_lifecycle_and_destroyed_polling(monkeypatch):
    instance = window()
    notices = []
    monkeypatch.setattr(
        "mps.gui.import_window.messagebox.showinfo",
        lambda *args, **kwargs: notices.append((args, kwargs)),
    )
    instance._controller.status = ImportControllerStatus.RUNNING
    instance.close()
    assert notices
    assert instance._dialog.closed is False

    instance._controller.status = ImportControllerStatus.COMPLETED
    instance._schedule_poll()
    instance.close()
    assert instance._dialog.closed is True
    assert instance._window.cancelled
    after_calls = instance._window.after_calls
    instance._schedule_poll()
    assert instance._window.after_calls == after_calls


def test_destroyed_window_does_not_reschedule():
    instance = window()
    instance._destroyed = True
    instance._poll_events()
    assert instance._window.after_calls == 0
