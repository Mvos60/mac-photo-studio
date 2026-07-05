from pathlib import Path
from mps.models.card import CardScanResult


def test_card_scan_result_has_photos():
    result = CardScanResult(Path("/tmp/card"), None, 1, 0, 0, 10)
    assert result.has_photos
