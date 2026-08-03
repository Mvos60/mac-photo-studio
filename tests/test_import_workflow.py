from dataclasses import FrozenInstanceError

import pytest

from mps.models.import_workflow import (
    ImportEvent,
    ImportEventType,
    ImportRequest,
    ImportRequestType,
    ImportResponse,
    ImportWaitingReason,
)
from mps.services.import_media_cli_adapter import (
    CliImportInteractionAdapter,
)


def test_import_event_is_typed_and_immutable():
    event = ImportEvent(
        ImportEventType.MEDIA_DISCOVERED,
        {"source_count": 2, "sources": ("raw", "jpeg")},
    )

    assert event.type is ImportEventType.MEDIA_DISCOVERED
    assert event.payload == {
        "source_count": 2,
        "sources": ("raw", "jpeg"),
    }

    with pytest.raises(FrozenInstanceError):
        event.type = ImportEventType.FAILED

    with pytest.raises(TypeError):
        event.payload["source_count"] = 3


def test_import_event_types_are_the_domain_contract():
    assert {event_type.value for event_type in ImportEventType} == {
        "session_started",
        "media_discovery_started",
        "media_discovered",
        "waiting_for_media",
        "batch_started",
        "batch_planned",
        "batch_completed",
        "progress",
        "reconciliation_started",
        "reconciliation_completed",
        "warning",
        "failed",
        "completed",
    }


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("", ImportResponse.RESCAN_MEDIA),
        ("unexpected", ImportResponse.RESCAN_MEDIA),
        ("n", ImportResponse.ALL_MEDIA_READY),
        ("NO", ImportResponse.ALL_MEDIA_READY),
    ],
)
def test_cli_adapter_preserves_prompt_default_and_answers(
    monkeypatch,
    answer,
    expected,
):
    prompts = []
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: prompts.append(prompt) or answer,
    )

    response = CliImportInteractionAdapter().request(ImportRequest(
        ImportRequestType.NEXT_MEDIA_ACTION,
        ImportWaitingReason.BATCH_COMPLETED,
    ))

    assert response is expected
    assert prompts == [
        "Press Enter to scan; type no only when all "
        "cards are imported: "
    ]


def test_cli_adapter_preserves_waiting_context_text(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr("builtins.input", lambda prompt: "no")

    response = CliImportInteractionAdapter().request(ImportRequest(
        ImportRequestType.NEXT_MEDIA_ACTION,
        ImportWaitingReason.NO_MEDIA_MOUNTED,
    ))

    output = capsys.readouterr().out
    assert response is ImportResponse.ALL_MEDIA_READY
    assert "same photo session may still need to be inserted" in output
    assert "matching RAW or JPG card" in output
