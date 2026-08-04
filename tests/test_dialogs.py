import inspect

from mps.gui.dialogs import MpsDialog


def test_shared_toplevel_applies_camera_icon():
    source = inspect.getsource(MpsDialog.__init__)
    assert "apply_window_icon(self.window)" in source
