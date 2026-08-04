import inspect

from mps.gui.dialogs import (
    ACTION_BUTTON_WIDTH_ALLOWANCE,
    ACTION_FOOTER_WIDTH_ALLOWANCE,
    MpsDialog,
    configure_three_action_footer,
    measure_action_button_column_width,
    minimum_three_action_dialog_width,
)


def test_shared_toplevel_applies_camera_icon():
    source = inspect.getsource(MpsDialog.__init__)
    assert "apply_window_icon(self.window)" in source


def test_three_action_footer_reserves_even_columns():
    class Footer:
        def __init__(self):
            self.columns = {}

        def columnconfigure(self, column, **kwargs):
            self.columns[column] = kwargs

    dialog = type("Dialog", (), {"footer": Footer()})()
    configure_three_action_footer(dialog, minimum_button_width=180)

    assert dialog.footer.columns[0] == {"weight": 0}
    assert dialog.footer.columns[1] == dialog.footer.columns[2]
    assert dialog.footer.columns[2] == dialog.footer.columns[3]
    assert dialog.footer.columns[3] == {
        "weight": 1,
        "minsize": 180,
        "uniform": "dialog-actions",
    }


def test_longest_label_drives_measured_action_column(monkeypatch):
    measurements = {
        "Stop and Resume Later": 210,
        "All Cards Ready": 140,
        "Scan Again": 90,
    }

    class Font:
        def __init__(self, **kwargs):
            pass

        def measure(self, label):
            return measurements[label]

    monkeypatch.setattr("mps.gui.dialogs.tkfont.Font", Font)
    width = measure_action_button_column_width(
        object(), tuple(measurements)
    )

    assert width == 210 + ACTION_BUTTON_WIDTH_ALLOWANCE
    assert minimum_three_action_dialog_width(width) == (
        width * 3 + ACTION_FOOTER_WIDTH_ALLOWANCE
    )
