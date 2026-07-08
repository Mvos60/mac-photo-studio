from pathlib import Path

from mps.models.import_decision import ImportDecision


def test_import_decision():
    decision = ImportDecision(
        destination=Path("/tmp/photos"),
        total_files=10,
        estimated_size_bytes=12345,
        warnings=["Example warning"],
    )

    assert decision.destination == Path("/tmp/photos")
    assert decision.total_files == 10
    assert decision.estimated_size_bytes == 12345
    assert decision.warnings == ["Example warning"]
