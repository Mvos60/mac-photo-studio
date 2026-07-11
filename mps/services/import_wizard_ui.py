from __future__ import annotations

from mps.models.import_session_request import ImportSessionRequest
from mps.services.import_card_report import build_card_report
from mps.services.import_card_selector import ImportCardSelection


def build_wizard_intro(selection: ImportCardSelection) -> str:
    return (
        "Mac Photo Studio Import Wizard\n"
        "==============================\n\n"
        + build_card_report(selection)
    )


def build_import_summary(request: ImportSessionRequest) -> str:
    raw_folder = (
        str(request.raw_folder)
        if request.raw_folder is not None
        else "Not selected"
    )

    jpeg_folder = (
        str(request.jpeg_folder)
        if request.jpeg_folder is not None
        else "Not selected"
    )

    return (
        "Import Summary\n"
        "==============\n\n"
        f"Year        : {request.year}\n"
        f"Project     : {request.project}\n"
        f"Day/session : {request.day}\n"
        f"RAW folder  : {raw_folder}\n"
        f"JPEG folder : {jpeg_folder}"
    )
