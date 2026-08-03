from threading import Event, Thread

from mps.gui.import_interaction_adapter import GuiImportInteractionAdapter
from mps.models.import_workflow import (
    ImportEventType,
    ImportRequest,
    ImportRequestType,
    ImportResponse,
    ImportWaitingReason,
)


def test_typed_request_and_response_cross_the_bridge():
    events = []
    cancellation = Event()
    adapter = GuiImportInteractionAdapter(events.append, cancellation)
    request = ImportRequest(
        ImportRequestType.NEXT_MEDIA_ACTION,
        ImportWaitingReason.BATCH_COMPLETED,
    )
    responses = []
    worker = Thread(target=lambda: responses.append(adapter.request(request)))
    worker.start()

    assert len(events) == 1
    assert events[0].type is ImportEventType.INTERACTION_REQUESTED
    assert events[0].payload["request"] is request
    pending = events[0].payload["interaction"]
    pending.respond(ImportResponse.RESCAN_MEDIA)
    worker.join(1)

    assert not worker.is_alive()
    assert responses == [ImportResponse.RESCAN_MEDIA]


def test_cancellation_unblocks_with_valid_typed_response():
    events = []
    cancellation = Event()
    adapter = GuiImportInteractionAdapter(events.append, cancellation)
    responses = []
    worker = Thread(target=lambda: responses.append(adapter.request(
        ImportRequest(
            ImportRequestType.NEXT_MEDIA_ACTION,
            ImportWaitingReason.NO_MEDIA_MOUNTED,
        )
    )))
    worker.start()
    cancellation.set()
    worker.join(1)
    assert not worker.is_alive()
    assert responses == [ImportResponse.CANCEL_PRESERVE_STATE]


def test_already_cancelled_adapter_does_not_publish_request():
    events = []
    cancellation = Event()
    cancellation.set()
    adapter = GuiImportInteractionAdapter(events.append, cancellation)
    response = adapter.request(ImportRequest(
        ImportRequestType.NEXT_MEDIA_ACTION,
        ImportWaitingReason.BATCH_COMPLETED,
    ))
    assert response is ImportResponse.CANCEL_PRESERVE_STATE
    assert events == []
