from threading import Event, current_thread

import pytest

from mps.models.import_workflow import ImportEvent, ImportEventType
from mps.services.import_controller import (
    ImportAlreadyActiveError,
    ImportController,
    ImportControllerStatus,
)


def test_controller_starts_idle():
    controller = ImportController()
    assert controller.status is ImportControllerStatus.IDLE
    assert controller.is_active is False
    assert controller.worker_alive is False


def test_start_creates_one_non_daemon_worker_and_rejects_second():
    controller = ImportController()
    entered = Event()
    release = Event()

    def runner(event_sink, cancel_event):
        entered.set()
        release.wait()

    controller.start(runner)
    assert entered.wait(1)
    assert controller.worker_alive
    assert controller._worker is not None
    assert controller._worker.daemon is False
    with pytest.raises(ImportAlreadyActiveError):
        controller.start(runner)
    release.set()
    controller.join(1)


def test_events_preserve_order_and_drive_typed_statuses():
    controller = ImportController()
    emitted = [
        ImportEvent(ImportEventType.SESSION_STARTED),
        ImportEvent(ImportEventType.WAITING_FOR_MEDIA),
        ImportEvent(ImportEventType.RECONCILIATION_COMPLETED),
        ImportEvent(ImportEventType.COMPLETED),
    ]

    controller.start(
        lambda sink, cancel_event: [sink(event) for event in emitted]
    )
    controller.join(1)

    assert controller.status is ImportControllerStatus.STARTING
    assert controller.drain_events() == emitted
    assert controller.status is ImportControllerStatus.COMPLETED


def test_reconciliation_completed_does_not_complete_controller():
    controller = ImportController()
    controller.start(lambda sink, token: sink(ImportEvent(
        ImportEventType.RECONCILIATION_COMPLETED
    )))
    controller.join(1)
    controller.drain_events()
    assert controller.status is ImportControllerStatus.STOPPED


@pytest.mark.parametrize(
    ("event_type", "expected"),
    [
        (ImportEventType.SESSION_STARTED, ImportControllerStatus.RUNNING),
        (
            ImportEventType.WAITING_FOR_MEDIA,
            ImportControllerStatus.WAITING_FOR_MEDIA,
        ),
        (ImportEventType.FAILED, ImportControllerStatus.FAILED),
        (ImportEventType.COMPLETED, ImportControllerStatus.COMPLETED),
    ],
)
def test_event_status_transition(event_type, expected):
    controller = ImportController()
    controller._apply_event_status(ImportEvent(event_type))
    assert controller.status is expected


def test_worker_exception_publishes_one_failed_event():
    controller = ImportController()

    def runner(sink, token):
        raise RuntimeError("boom")

    controller.start(runner)
    controller.join(1)
    events = controller.drain_events()
    assert [event.type for event in events] == [ImportEventType.FAILED]
    assert events[0].payload["exception_type"] == "RuntimeError"
    assert controller.status is ImportControllerStatus.FAILED


def test_runner_failed_event_is_not_duplicated_after_exception():
    controller = ImportController()

    def runner(sink, token):
        sink(ImportEvent(ImportEventType.FAILED, {"code": "runner"}))
        raise RuntimeError("already reported")

    controller.start(runner)
    controller.join(1)
    assert [event.type for event in controller.drain_events()] == [
        ImportEventType.FAILED
    ]


def test_cancel_token_and_cancelling_status_are_foundation_only():
    controller = ImportController()
    entered = Event()
    release = Event()
    received = []

    def runner(sink, token):
        received.append(token)
        entered.set()
        release.wait()

    controller.start(runner)
    assert entered.wait(1)
    controller.request_cancel()
    assert received[0].is_set()
    assert controller.status is ImportControllerStatus.CANCELLING
    assert controller.worker_alive
    release.set()
    controller.join(1)


def test_worker_has_no_tk_callback_and_new_run_can_start():
    controller = ImportController()
    threads = []

    def runner(sink, token):
        threads.append(current_thread().name)
        sink(ImportEvent(ImportEventType.COMPLETED))

    controller.start(runner)
    controller.join(1)
    controller.drain_events()
    controller.start(runner)
    controller.join(1)
    controller.drain_events()
    assert threads == ["mps-import-worker", "mps-import-worker"]


def test_worker_return_without_terminal_emits_one_stopped_event():
    controller = ImportController()
    controller.start(lambda sink, token: sink(ImportEvent(
        ImportEventType.SESSION_STARTED
    )))
    controller.join(1)
    events = controller.drain_events()
    assert [event.type for event in events] == [
        ImportEventType.SESSION_STARTED,
        ImportEventType.STOPPED,
    ]
    assert controller.status is ImportControllerStatus.STOPPED


def test_explicit_stopped_event_is_not_duplicated():
    controller = ImportController()
    controller.start(lambda sink, token: sink(ImportEvent(
        ImportEventType.STOPPED
    )))
    controller.join(1)
    assert [event.type for event in controller.drain_events()] == [
        ImportEventType.STOPPED
    ]


def test_request_cancel_unblocks_pending_interaction_with_preserve_response():
    from mps.gui.import_interaction_adapter import GuiImportInteractionAdapter
    from mps.models.import_workflow import (
        ImportRequest,
        ImportRequestType,
        ImportResponse,
        ImportWaitingReason,
    )

    controller = ImportController()
    requested = Event()
    responses = []

    def runner(event_sink, cancellation):
        def forwarding_sink(event):
            event_sink(event)
            if event.type is ImportEventType.INTERACTION_REQUESTED:
                requested.set()

        adapter = GuiImportInteractionAdapter(
            forwarding_sink,
            cancellation,
        )
        responses.append(adapter.request(ImportRequest(
            ImportRequestType.NEXT_MEDIA_ACTION,
            ImportWaitingReason.NO_MEDIA_MOUNTED,
        )))

    controller.start(runner)
    assert requested.wait(1)
    controller.request_cancel()
    controller.join(1)
    assert not controller.worker_alive
    assert responses == [ImportResponse.CANCEL_PRESERVE_STATE]
    assert [event.type for event in controller.drain_events()] == [
        ImportEventType.INTERACTION_REQUESTED,
        ImportEventType.STOPPED,
    ]
