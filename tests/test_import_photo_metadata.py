from datetime import datetime
from pathlib import Path
import subprocess

import pytest

from mps.services.import_photo_metadata import (
    parse_datetime_original,
    read_datetime_original,
    resolve_candidate_captured_at,
)


def test_batch_reads_multiple_paths_in_one_exiftool_call(monkeypatch, tmp_path):
    first = tmp_path / "A.ARW"
    second = tmp_path / "A.JPG"
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout=(
            f'[{{"SourceFile": "{first}", "DateTimeOriginal": "2026:06:10 14:31:00"}},'
            f'{{"SourceFile": "{second}"}}]'
        ), stderr="")
    monkeypatch.setattr("mps.services.import_photo_metadata.subprocess.run", run)
    result = read_datetime_original([first, second, first])
    assert len(calls) == 1
    assert calls[0][0][:3] == ["exiftool", "-j", "-DateTimeOriginal"]
    assert result[first] == datetime(2026, 6, 10, 14, 31)
    assert result[second] is None
    assert result[first].tzinfo is None


@pytest.mark.parametrize("value", [None, "", "2026-06-10 14:31:00", "invalid"])
def test_invalid_or_missing_datetime_is_unknown(value):
    assert parse_datetime_original(value) is None


@pytest.mark.parametrize("failure", ["nonzero", "invalid-json", "timeout", "oserror"])
def test_exiftool_failures_are_safe(monkeypatch, tmp_path, failure):
    path = tmp_path / "A.ARW"
    def run(command, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 30)
        if failure == "oserror":
            raise OSError("missing")
        if failure == "invalid-json":
            return subprocess.CompletedProcess(command, 0, stdout="not-json", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="[]", stderr="error")
    monkeypatch.setattr("mps.services.import_photo_metadata.subprocess.run", run)
    assert read_datetime_original([path]) == {path: None}


def test_candidate_metadata_resolution_uses_only_value_or_marks_conflict():
    raw, jpg = Path("A.ARW"), Path("A.JPG")
    first = datetime(2026, 6, 10, 14, 31)
    second = datetime(2026, 6, 11, 0, 14)
    assert resolve_candidate_captured_at([raw, jpg], {raw: first, jpg: first}) == (first, False)
    assert resolve_candidate_captured_at([raw, jpg], {raw: first, jpg: None}) == (first, False)
    assert resolve_candidate_captured_at([raw, jpg], {raw: None, jpg: second}) == (second, False)
    assert resolve_candidate_captured_at([raw, jpg], {raw: None, jpg: None}) == (None, False)
    assert resolve_candidate_captured_at([raw, jpg], {raw: first, jpg: second}) == (None, True)
