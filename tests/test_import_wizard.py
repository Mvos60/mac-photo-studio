from pathlib import Path

from mps.services.import_wizard import collect_import_session, prompt_folder


def test_prompt_folder(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "~/Photos")

    assert prompt_folder("Folder") == Path("~/Photos").expanduser()


def test_collect_import_session(monkeypatch):
    answers = iter(
        [
            "",
            "Adriatic",
            "03_Slovenia",
            "~/raw",
            "~/jpg",
        ]
    )

    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    session = collect_import_session(default_year=2026)

    assert session.year == 2026
    assert session.project == "Adriatic"
    assert session.day == "03_Slovenia"
    assert session.raw_folder == Path("~/raw").expanduser()
    assert session.jpeg_folder == Path("~/jpg").expanduser()
