from mps.services.import_prompts import (
    prompt_day,
    prompt_project,
    prompt_year,
)


def test_prompt_project(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "Adriatic")
    assert prompt_project() == "Adriatic"


def test_prompt_day(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "03_Slovenia")
    assert prompt_day() == "03_Slovenia"


def test_prompt_year_default(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert prompt_year(2026) == 2026


def test_prompt_year_override(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2027")
    assert prompt_year(2026) == 2027
