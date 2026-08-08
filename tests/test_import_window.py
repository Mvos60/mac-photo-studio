from pathlib import Path

from mps.gui.import_window import (
    EMPTY_VALUE,
    IMPORT_WINDOW_GEOMETRY,
    IMPORT_WINDOW_MINIMUM,
    IMPORT_WINDOW_VERTICAL_RESERVE,
    RESULT_DETAILS_MIN_HEIGHT,
    RESULT_DETAIL_LINE_MIN_HEIGHT,
    RESULT_MESSAGE_LINE_MIN_HEIGHT,
    RESULT_MESSAGES_MIN_HEIGHT,
    RESULT_TOTALS_MIN_HEIGHT,
    RESULTS_ROW_MIN_HEIGHT,
    RESULTS_TREE_MIN_HEIGHT,
    RESULTS_TREE_VISIBLE_ROWS,
    SUMMARY_ROW_MIN_HEIGHT,
    SUMMARY_LEFT_LABEL_MIN_WIDTH,
    SUMMARY_RIGHT_LABEL_MIN_WIDTH,
    SUMMARY_VALUE_MIN_WIDTH,
    SUMMARY_VALUE_WRAP_LENGTH,
    WAITING_DIALOG_ACTION_LABELS,
    WAITING_DIALOG_CONTENT_MIN_WIDTH,
    WAITING_DIALOG_MINIMUM,
    ImportWindow,
    WaitingForMediaDialog,
    humanize_import_code,
    humanize_import_phase,
    humanize_import_status,
)
from mps.models.import_file_result import (
    ImportFileMediaType,
    ImportFileResult,
    ImportFileResultStatus,
)
from mps.models.card import CardScanResult
from mps.models.import_media_selection import ImportMediaSelection
from mps.models.import_photo_selection import (
    ImportPhotoCandidate,
    ImportPhotoSelectionResponse,
)
from mps.models.import_progress import ImportProgress
from mps.models.import_workflow import ImportEvent, ImportEventType
from mps.models.import_workflow import (
    ImportRequest,
    ImportRequestType,
    ImportResponse,
    ImportWaitingReason,
)
from mps.gui.import_interaction_adapter import PendingImportInteraction
from mps.services.import_controller import ImportControllerStatus


class FakeVariable:
    def __init__(self, value=EMPTY_VALUE, **_kwargs):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def trace_add(self, mode, callback):
        return None


class FakeProgressbar:
    def __init__(self):
        self.value = 0

    def configure(self, **kwargs):
        self.value = kwargs["value"]


class FakeLayoutWidget:
    created = []

    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.kwargs = kwargs
        self.grid_options = None
        self.row_options = {}
        self.column_options = {}
        self.created.append(self)

    def grid(self, **kwargs):
        self.grid_options = kwargs
        return self

    def rowconfigure(self, row, **kwargs):
        self.row_options[row] = kwargs

    def columnconfigure(self, column, **kwargs):
        self.column_options[column] = kwargs

    def heading(self, column, **kwargs):
        return None

    def column(self, column, **kwargs):
        return None

    def configure(self, **kwargs):
        return None

    def bind(self, event, callback):
        return None

    def yview(self, *args):
        return None

    def set(self, *args):
        return None


class FakeTreeview:
    def __init__(self):
        self.rows = {}
        self.selected = ()

    def insert(self, parent, index, *, iid, values):
        self.rows[iid] = values

    def item(self, iid, *, values):
        self.rows[iid] = values

    def selection(self):
        return self.selected


class FakeWindow:
    def __init__(self):
        self.callbacks = {}
        self.after_calls = 0
        self.cancelled = []
        self.exists = True
        self.geometry_value = None
        self.minimum = None
        self.protocols = {}

    def geometry(self, value):
        self.geometry_value = value

    def minsize(self, width, height):
        self.minimum = (width, height)

    def protocol(self, name, callback):
        self.protocols[name] = callback

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
        self.worker_alive = False
        self.cancel_requested = False

    def drain_events(self):
        events, self.events = self.events, []
        return events

    def request_cancel(self):
        self.cancel_requested = True


def window():
    instance = ImportWindow.__new__(ImportWindow)
    instance._controller = FakeController()
    instance._poll_interval_ms = 75
    instance._after_id = None
    instance._destroyed = False
    instance._on_terminal = None
    instance._terminal_notified = False
    instance._file_results = {}
    instance._result_rows = {}
    instance._last_warning_code = None
    instance._last_terminal_code = None
    instance._status_code = ImportControllerStatus.IDLE.value
    instance._current_progress = None
    instance._window = FakeWindow()
    instance._dialog = FakeDialog()
    instance._variables = {
        key: FakeVariable("0%" if key == "percentage" else EMPTY_VALUE)
        for key in (
            "status", "session_id", "destination", "action", "source_card",
            "raw", "jpeg", "pairs", "phase", "current_file", "source",
            "progress_destination", "current_total", "percentage",
            "result_counts", "selected_source", "selected_destination",
            "selected_detail", "warning", "final_result",
        )
    }
    instance._variables["status"].set("Idle")
    instance._variables["result_counts"].set(
        "Verified: 0    Skipped: 0    Failed: 0"
    )
    instance._progressbar = FakeProgressbar()
    instance._results_tree = FakeTreeview()
    return instance


def test_window_initial_values_are_safe_and_poll_starts_once():
    instance = window()
    assert instance._variables["session_id"].get() == EMPTY_VALUE
    instance._schedule_poll()
    instance._schedule_poll()
    assert instance._window.after_calls == 1


def test_window_builds_one_treeview_for_all_file_results():
    import inspect

    source = inspect.getsource(ImportWindow._build_content)
    assert source.count("ttk.Treeview(") == 1


def test_results_layout_has_reliable_space_and_visible_support_widgets():
    import inspect

    source = inspect.getsource(ImportWindow._build_content)
    assert IMPORT_WINDOW_GEOMETRY == "1180x900"
    assert IMPORT_WINDOW_MINIMUM == (980, 820)
    assert 7 <= RESULTS_TREE_VISIBLE_ROWS <= 8
    assert RESULTS_ROW_MIN_HEIGHT >= 220
    assert RESULTS_TREE_MIN_HEIGHT >= 180
    assert RESULT_TOTALS_MIN_HEIGHT >= 30
    assert RESULT_DETAILS_MIN_HEIGHT >= 72
    assert RESULT_MESSAGES_MIN_HEIGHT >= 56
    guaranteed_content_height = sum((
        SUMMARY_ROW_MIN_HEIGHT,
        RESULTS_ROW_MIN_HEIGHT,
        RESULT_TOTALS_MIN_HEIGHT,
        RESULT_DETAILS_MIN_HEIGHT,
        RESULT_MESSAGES_MIN_HEIGHT,
    ))
    available_content_height = (
        IMPORT_WINDOW_MINIMUM[1] - IMPORT_WINDOW_VERTICAL_RESERVE
    )
    assert guaranteed_content_height <= available_content_height
    assert "minsize=RESULTS_ROW_MIN_HEIGHT" in source
    assert "minsize=RESULTS_TREE_MIN_HEIGHT" in source
    assert 'scrollbar.grid(row=0, column=1, sticky="ns")' in source
    assert 'textvariable=self._variables["result_counts"]' in source
    assert 'self._result_totals_frame.grid(row=2, column=0, sticky="ew")' in source
    assert 'self._details_frame.grid(row=3, column=0, sticky="ew")' in source
    assert "self._messages_frame = ttk.Frame(self._dialog.footer)" in source


def test_totals_details_and_messages_are_really_gridded(monkeypatch):
    instance = window()
    FakeLayoutWidget.created = []
    instance._dialog.content = FakeLayoutWidget()
    instance._dialog.footer = FakeLayoutWidget()
    monkeypatch.setattr("mps.gui.import_window.tk.StringVar", FakeVariable)
    for widget_name in (
        "Frame", "LabelFrame", "Label", "Progressbar", "Treeview", "Scrollbar"
    ):
        monkeypatch.setattr(
            f"mps.gui.import_window.ttk.{widget_name}",
            FakeLayoutWidget,
        )

    instance._build_content()

    assert instance._result_totals_frame.grid_options == {
        "row": 2, "column": 0, "sticky": "ew"
    }
    assert instance._result_counts_label.grid_options["row"] == 0
    assert instance._details_frame.grid_options == {
        "row": 3, "column": 0, "sticky": "ew"
    }
    assert instance._detail_value_labels["selected_detail"].parent is (
        instance._details_frame
    )
    assert instance._detail_value_labels["selected_detail"].grid_options == {
        "row": 2, "column": 1, "sticky": "ew", "pady": 0
    }
    assert instance._details_frame.row_options[2] == {
        "weight": 0,
        "minsize": RESULT_DETAIL_LINE_MIN_HEIGHT,
    }
    assert instance._messages_frame.grid_options == {
        "row": 0,
        "column": 0,
        "sticky": "ew",
        "padx": (0, 18),
    }
    assert instance._messages_frame.parent is instance._dialog.footer
    assert instance._warning_label.grid_options["row"] == 0
    assert instance._final_result_label.grid_options["row"] == 1
    assert instance._messages_frame.row_options == {
        0: {"weight": 0, "minsize": RESULT_MESSAGE_LINE_MIN_HEIGHT},
        1: {"weight": 0, "minsize": RESULT_MESSAGE_LINE_MIN_HEIGHT},
    }


def test_summary_labels_and_values_share_top_alignment(monkeypatch):
    instance = window()
    FakeLayoutWidget.created = []
    instance._dialog.content = FakeLayoutWidget()
    instance._dialog.footer = FakeLayoutWidget()
    monkeypatch.setattr("mps.gui.import_window.tk.StringVar", FakeVariable)
    for widget_name in (
        "Frame", "LabelFrame", "Label", "Progressbar", "Treeview", "Scrollbar"
    ):
        monkeypatch.setattr(
            f"mps.gui.import_window.ttk.{widget_name}",
            FakeLayoutWidget,
        )

    instance._build_content()

    for key in (
        "status",
        "session_id",
        "action",
        "source_card",
        "media_counts",
        "destination",
        "current_file",
        "phase",
        "current_total",
    ):
        label = instance._summary_labels[key]
        value = instance._summary_values[key]
        assert label.grid_options["sticky"] == "nw"
        assert value.grid_options["sticky"] == "nw"
        assert label.grid_options["pady"] == value.grid_options["pady"] == 2
        assert value.kwargs["justify"] == "left"
        assert value.kwargs["wraplength"] == SUMMARY_VALUE_WRAP_LENGTH

    assert instance._summary_frame.column_options == {
        0: {"weight": 0, "minsize": SUMMARY_LEFT_LABEL_MIN_WIDTH},
        1: {
            "weight": 1,
            "minsize": SUMMARY_VALUE_MIN_WIDTH,
            "uniform": "summary-values",
        },
        2: {"weight": 0, "minsize": SUMMARY_RIGHT_LABEL_MIN_WIDTH},
        3: {
            "weight": 1,
            "minsize": SUMMARY_VALUE_MIN_WIDTH,
            "uniform": "summary-values",
        },
    }
    assert SUMMARY_VALUE_WRAP_LENGTH < SUMMARY_VALUE_MIN_WIDTH
    assert instance._summary_values["session_id"].kwargs["wraplength"] == (
        SUMMARY_VALUE_WRAP_LENGTH
    )
    assert instance._summary_values["destination"].kwargs["wraplength"] == (
        SUMMARY_VALUE_WRAP_LENGTH
    )


def test_dialog_footer_uses_a_separate_root_row_from_content():
    import inspect

    from mps.gui.dialogs import MpsDialog

    source = inspect.getsource(MpsDialog.__init__)
    assert 'self.content.grid(row=1, column=0, sticky="nsew")' in source
    assert 'self.footer.grid(row=2, column=0, sticky="ew")' in source


def test_waiting_dialog_has_safe_width_and_three_action_columns(monkeypatch):
    class Dialog:
        def __init__(self):
            self.window = FakeWindow()
            self.content = FakeLayoutWidget()
            self.footer = FakeLayoutWidget()
            self.buttons = []

        def add_header(self, *args, **kwargs):
            return None

        def add_footer_button(self, **kwargs):
            self.buttons.append(kwargs)
            return FakeLayoutWidget(self.footer)

    dialog = Dialog()
    monkeypatch.setattr(
        "mps.gui.import_window.MpsDialog",
        lambda *args, **kwargs: dialog,
    )
    monkeypatch.setattr("mps.gui.import_window.ttk.Label", FakeLayoutWidget)
    measured_column_width = 240
    monkeypatch.setattr(
        "mps.gui.import_window.measure_action_button_column_width",
        lambda window, labels: measured_column_width,
    )

    WaitingForMediaDialog(
        object(),
        ImportWaitingReason.BATCH_COMPLETED,
    )

    required_width = measured_column_width * 3 + 60
    assert dialog.window.geometry_value == f"{required_width}x440"
    assert dialog.window.minimum == (required_width, WAITING_DIALOG_MINIMUM[1])
    assert dialog.content.column_options[0] == {
        "weight": 1,
        "minsize": WAITING_DIALOG_CONTENT_MIN_WIDTH,
    }
    assert [button["text"] for button in dialog.buttons] == list(
        WAITING_DIALOG_ACTION_LABELS
    )
    assert [button["column"] for button in dialog.buttons] == [1, 2, 3]
    for column in (1, 2, 3):
        assert dialog.footer.column_options[column] == {
            "weight": 1,
            "minsize": measured_column_width,
            "uniform": "dialog-actions",
        }
    assert required_width >= measured_column_width * 3 + 60


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
    assert instance._variables["final_result"].get() == (
        "Import completed successfully."
    )
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
    assert instance._variables["phase"].get() == "Copying files"
    assert instance._variables["current_file"].get() == "A.ARW"
    assert instance._variables["current_total"].get() == "1 / 4"
    assert instance._variables["percentage"].get() == "25%"
    assert instance._progressbar.value == 25
    assert instance._current_progress is progress

    instance.apply_event(ImportEvent(
        ImportEventType.WARNING, {"message": "Check media"}
    ))
    assert instance._variables["warning"].get() == "Check media"
    assert instance._variables["status"].get() != "Failed"
    instance.apply_event(ImportEvent(
        ImportEventType.FAILED,
        {"exception_type": "RuntimeError", "message": "copy failed"},
    ))
    assert instance._variables["status"].get() == "Failed"
    assert instance._variables["final_result"].get() == (
        "Import failed. copy failed"
    )
    instance.apply_event(ImportEvent(ImportEventType.COMPLETED))
    assert instance._variables["final_result"].get() == (
        "Import completed successfully."
    )


def test_close_lifecycle_and_destroyed_polling(monkeypatch):
    instance = window()
    notices = []
    monkeypatch.setattr(
        "mps.gui.import_window.messagebox.askyesno",
        lambda *args, **kwargs: notices.append((args, kwargs)) or False,
    )
    instance._controller.status = ImportControllerStatus.RUNNING
    instance._controller.worker_alive = True
    instance.close()
    assert notices
    assert instance._dialog.closed is False

    instance._controller.status = ImportControllerStatus.COMPLETED
    instance._controller.worker_alive = False
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


def test_interaction_request_is_resolved_on_window_poll_thread(monkeypatch):
    instance = window()
    pending = PendingImportInteraction(ImportRequest(
        ImportRequestType.NEXT_MEDIA_ACTION,
        ImportWaitingReason.BATCH_COMPLETED,
    ))
    monkeypatch.setattr(
        "mps.gui.import_window.choose_waiting_for_media_action",
        lambda *args, **kwargs: ImportResponse.RESCAN_MEDIA,
    )
    instance.apply_event(ImportEvent(
        ImportEventType.INTERACTION_REQUESTED,
        {"interaction": pending},
    ))
    assert pending.wait(__import__("threading").Event()) is (
        ImportResponse.RESCAN_MEDIA
    )


def test_photo_selection_request_is_resolved_on_window_poll_thread(monkeypatch):
    instance = window()
    candidates = (
        ImportPhotoCandidate(
            "dsc0001", "DSC0001", raw_paths=(Path("DSC0001.ARW"),)
        ),
    )
    pending = PendingImportInteraction(ImportRequest(
        ImportRequestType.SELECT_PHOTOS,
        candidates=candidates,
    ))
    expected = ImportPhotoSelectionResponse(frozenset({"dsc0001"}))
    monkeypatch.setattr(
        "mps.gui.import_window.choose_import_photos",
        lambda *args, **kwargs: expected,
    )

    instance.apply_event(ImportEvent(
        ImportEventType.INTERACTION_REQUESTED,
        {"interaction": pending},
    ))

    assert pending.wait(__import__("threading").Event()) is expected


def test_photo_selection_counts_only_cross_source_raw_jpeg_pairs(monkeypatch):
    instance = window()
    candidates = tuple(
        ImportPhotoCandidate(
            f"pair-{index}",
            f"PAIR{index}",
            raw_paths=(Path(f"raw-card/PAIR{index}.ARW"),),
            jpeg_paths=(Path(f"jpg-card/PAIR{index}.JPG"),),
        )
        for index in range(4)
    ) + (
        ImportPhotoCandidate(
            "raw-only",
            "RAWONLY",
            raw_paths=(Path("raw-card/RAWONLY.ARW"),),
        ),
        ImportPhotoCandidate(
            "jpg-only",
            "JPGONLY",
            jpeg_paths=(Path("jpg-card/JPGONLY.JPG"),),
        ),
    )
    pending = PendingImportInteraction(ImportRequest(
        ImportRequestType.SELECT_PHOTOS,
        candidates=candidates,
    ))
    expected = ImportPhotoSelectionResponse(frozenset(
        candidate.key for candidate in candidates
    ))
    monkeypatch.setattr(
        "mps.gui.import_window.choose_import_photos",
        lambda *args, **kwargs: expected,
    )

    instance.apply_event(ImportEvent(
        ImportEventType.INTERACTION_REQUESTED,
        {"interaction": pending},
    ))

    assert instance._variables["pairs"].get() == "4"
    assert pending.wait(__import__("threading").Event()) is expected


def test_terminal_events_refresh_status_once():
    instance = window()
    refreshes = []
    instance._on_terminal = lambda: refreshes.append(True)
    instance.apply_event(ImportEvent(ImportEventType.FAILED))
    instance.apply_event(ImportEvent(ImportEventType.COMPLETED))
    assert refreshes == [True]


def test_stopped_event_is_terminal_and_refreshes_status():
    instance = window()
    refreshes = []
    instance._on_terminal = lambda: refreshes.append(True)
    instance.apply_event(ImportEvent(
        ImportEventType.STOPPED,
        {"code": "cancelled_preserve_state"},
    ))
    assert instance._variables["status"].get() == "Stopped"
    assert instance._variables["final_result"].get() == (
        "Import stopped. The session can be resumed later."
    )
    assert refreshes == [True]


def test_unreconciled_failure_is_shown_as_failure_and_refreshes_status():
    instance = window()
    refreshes = []
    instance._on_terminal = lambda: refreshes.append(True)
    instance.apply_event(ImportEvent(
        ImportEventType.FAILED,
        {"code": "session_not_reconciled"},
    ))
    assert instance._variables["status"].get() == "Failed"
    assert instance._variables["final_result"].get() == (
        "Import failed. The import session could not be reconciled."
    )
    assert refreshes == [True]


def test_dead_worker_with_stale_running_status_can_close():
    instance = window()
    instance._controller.status = ImportControllerStatus.RUNNING
    instance._controller.worker_alive = False
    instance.close()
    assert instance._dialog.closed is True


def test_close_active_worker_can_request_safe_stop(monkeypatch):
    instance = window()
    instance._controller.status = ImportControllerStatus.WAITING_FOR_MEDIA
    instance._controller.worker_alive = True
    monkeypatch.setattr(
        "mps.gui.import_window.messagebox.askyesno",
        lambda *args, **kwargs: True,
    )
    instance.close()
    assert instance._dialog.closed is False
    assert instance._controller.cancel_requested is True


def test_waiting_dialog_has_three_explicit_actions():
    import inspect
    source = inspect.getsource(__import__(
        "mps.gui.import_window", fromlist=["WaitingForMediaDialog"]
    ).WaitingForMediaDialog)
    assert WAITING_DIALOG_ACTION_LABELS == (
        "Stop and Resume Later",
        "All Cards Ready",
        "Scan Again",
    )
    assert "ImportResponse.CANCEL_PRESERVE_STATE" in source
    assert "ImportResponse.ALL_MEDIA_READY" in source
    assert "ImportResponse.RESCAN_MEDIA" in source


def _file_result(tmp_path: Path, name: str, status) -> ImportFileResult:
    media_type = (
        ImportFileMediaType.RAW
        if name.endswith(".ARW")
        else ImportFileMediaType.JPEG
    )
    return ImportFileResult(
        source=tmp_path / "card" / name,
        destination=(
            None
            if status is ImportFileResultStatus.SKIPPED
            else tmp_path / "Photos" / name
        ),
        media_type=media_type,
        status=status,
        reason_code=(
            "already_imported"
            if status is ImportFileResultStatus.SKIPPED
            else None
        ),
        detail="Copy failed." if status is ImportFileResultStatus.FAILED else None,
    )


def test_file_results_are_listed_once_and_counted(tmp_path: Path):
    instance = window()
    results = [
        _file_result(tmp_path, "A.ARW", ImportFileResultStatus.VERIFIED),
        _file_result(tmp_path, "B.JPG", ImportFileResultStatus.SKIPPED),
        _file_result(tmp_path, "C.ARW", ImportFileResultStatus.FAILED),
    ]
    for result in results:
        event = ImportEvent(ImportEventType.FILE_RESULT, {"result": result})
        instance.apply_event(event)
        instance.apply_event(event)

    assert list(instance._results_tree.rows.values()) == [
        ("A.ARW", "RAW", "Verified"),
        ("B.JPG", "JPEG", "Skipped"),
        ("C.ARW", "RAW", "Failed"),
    ]
    assert instance._variables["result_counts"].get() == (
        "Verified: 1    Skipped: 1    Failed: 1"
    )


def test_eight_round_results_remain_visible_while_waiting(tmp_path: Path):
    instance = window()
    for extension, media_type in (("ARW", "RAW"), ("JPG", "JPEG")):
        for index in range(4):
            result = _file_result(
                tmp_path,
                f"ROUND5-{index}.{extension}",
                ImportFileResultStatus.VERIFIED,
            )
            instance.apply_event(ImportEvent(
                ImportEventType.FILE_RESULT, {"result": result}
            ))
    instance.apply_event(ImportEvent(ImportEventType.WAITING_FOR_MEDIA))
    instance.apply_event(ImportEvent(
        ImportEventType.STOPPED,
        {"code": "cancelled_preserve_state"},
    ))

    assert len(instance._results_tree.rows) == 8
    assert sum(row[1] == "RAW" for row in instance._results_tree.rows.values()) == 4
    assert sum(row[1] == "JPEG" for row in instance._results_tree.rows.values()) == 4
    assert instance._variables["result_counts"].get() == (
        "Verified: 8    Skipped: 0    Failed: 0"
    )
    assert instance._variables["status"].get() == "Stopped"
    assert instance._variables["final_result"].get() == (
        "Import stopped. The session can be resumed later."
    )


def test_statuses_and_unknown_values_are_humanized_without_controller_change():
    assert humanize_import_status("waiting_for_media") == "Waiting for media"
    assert humanize_import_status("unknown_future_status") == (
        "Unknown future status"
    )
    assert {
        status.value: humanize_import_status(status.value)
        for status in ImportControllerStatus
    } == {
        "idle": "Idle",
        "starting": "Starting",
        "running": "Running",
        "waiting_for_media": "Waiting for media",
        "cancelling": "Stopping safely",
        "failed": "Failed",
        "stopped": "Stopped",
        "completed": "Completed",
    }
    assert ImportControllerStatus.WAITING_FOR_MEDIA.value == "waiting_for_media"


def test_session_verification_does_not_show_import_root_as_file(tmp_path: Path):
    instance = window()
    import_root = tmp_path / "Photos" / "test5"
    progress = ImportProgress(
        current=0,
        total=1,
        source=import_root,
        destination=import_root,
        phase="verifying",
    )
    instance._apply_progress(progress)

    assert instance._variables["current_file"].get() == EMPTY_VALUE
    assert instance._variables["phase"].get() == "Verifying import session"
    assert instance._current_progress.source == import_root
    assert instance._current_progress.destination == import_root
    assert humanize_import_phase("future_phase") == "Future phase"


def test_selection_shows_paths_and_humanized_details(tmp_path: Path):
    instance = window()
    result = _file_result(
        tmp_path, "B.JPG", ImportFileResultStatus.SKIPPED
    )
    instance.apply_event(ImportEvent(
        ImportEventType.FILE_RESULT, {"result": result}
    ))
    instance._results_tree.selected = ("file-result-0",)
    instance._on_result_selected()

    assert instance._variables["selected_source"].get() == str(result.source)
    assert instance._variables["selected_destination"].get() == EMPTY_VALUE
    assert instance._variables["selected_detail"].get() == "Already imported."


def test_many_results_use_one_tree_and_preserve_terminal_state(tmp_path: Path):
    instance = window()
    for index in range(500):
        result = _file_result(
            tmp_path,
            f"A{index:04}.ARW",
            ImportFileResultStatus.VERIFIED,
        )
        instance.apply_event(ImportEvent(
            ImportEventType.FILE_RESULT, {"result": result}
        ))
    instance.apply_event(ImportEvent(ImportEventType.COMPLETED))

    assert len(instance._results_tree.rows) == 500
    assert instance._variables["result_counts"].get().startswith(
        "Verified: 500"
    )
    assert instance._variables["final_result"].get() == (
        "Import completed successfully."
    )


def test_codes_stay_internal_and_messages_are_readable():
    instance = window()
    instance.apply_event(ImportEvent(
        ImportEventType.WARNING, {"code": "no_new_media"}
    ))
    assert instance._last_warning_code == "no_new_media"
    assert instance._variables["warning"].get() == "No new media found."
    assert humanize_import_code("unknown_code") == (
        "The import reported an additional status."
    )
