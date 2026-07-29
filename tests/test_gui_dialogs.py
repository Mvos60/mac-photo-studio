from mps.gui.dialogs import DIALOG_SIZES, DialogSize, get_dialog_size


def test_dialog_size_geometry() -> None:
    size = DialogSize(
        width=820,
        height=560,
        minimum_width=680,
        minimum_height=460,
    )

    assert size.geometry == "820x560"


def test_standard_dialog_sizes_are_valid() -> None:
    assert set(DIALOG_SIZES) == {"small", "medium", "large", "wide"}

    for size in DIALOG_SIZES.values():
        assert size.width >= size.minimum_width
        assert size.height >= size.minimum_height
        assert size.width > 0
        assert size.height > 0


def test_get_dialog_size_returns_named_preset() -> None:
    assert get_dialog_size("medium") is DIALOG_SIZES["medium"]


def test_get_dialog_size_rejects_unknown_name() -> None:
    try:
        get_dialog_size("enormous")
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected ValueError")

    assert "Unknown MPS dialog size" in message
    assert "small" in message
    assert "medium" in message
