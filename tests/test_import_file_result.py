from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mps.models.import_file_result import (
    ImportFileMediaType,
    ImportFileResult,
    ImportFileResultStatus,
)


def test_import_file_result_is_typed_and_immutable(tmp_path: Path):
    result = ImportFileResult(
        source=tmp_path / "A.ARW",
        destination=tmp_path / "Photos" / "A.ARW",
        media_type=ImportFileMediaType.RAW,
        status=ImportFileResultStatus.VERIFIED,
    )
    with pytest.raises(FrozenInstanceError):
        result.status = ImportFileResultStatus.FAILED


def test_skipped_result_may_omit_destination(tmp_path: Path):
    result = ImportFileResult(
        source=tmp_path / "A.JPG",
        destination=None,
        media_type=ImportFileMediaType.JPEG,
        status=ImportFileResultStatus.SKIPPED,
        reason_code="already_imported",
    )
    assert result.destination is None


@pytest.mark.parametrize("field,value", [
    ("media_type", "raw"),
    ("status", "verified"),
])
def test_result_rejects_untyped_enum_values(tmp_path: Path, field, value):
    values = {
        "source": tmp_path / "A.ARW",
        "destination": tmp_path / "B.ARW",
        "media_type": ImportFileMediaType.RAW,
        "status": ImportFileResultStatus.VERIFIED,
    }
    values[field] = value
    with pytest.raises(TypeError):
        ImportFileResult(**values)


def test_non_skipped_result_requires_destination(tmp_path: Path):
    with pytest.raises(ValueError):
        ImportFileResult(
            source=tmp_path / "A.ARW",
            destination=None,
            media_type=ImportFileMediaType.RAW,
            status=ImportFileResultStatus.FAILED,
        )
