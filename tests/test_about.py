from mps.gui import about


def test_about_uses_camera_authoritative_version_and_slogan(monkeypatch):
    labels = []
    requested_sizes = []

    class Window:
        def __init__(self):
            self.waited = False
            self.geometry_value = None
            self.minimum = None

        def geometry(self, value):
            self.geometry_value = value

        def minsize(self, width, height):
            self.minimum = (width, height)

        def wait_window(self):
            self.waited = True

    class Content:
        def __init__(self):
            self.rows = {}

        def columnconfigure(self, *args, **kwargs):
            pass

        def rowconfigure(self, row, **kwargs):
            self.rows[row] = kwargs

    class Dialog:
        def __init__(self, *args, **kwargs):
            self.window = Window()
            self.content = Content()
            self.shown = False

        def add_close_button(self):
            pass

        def show(self):
            self.shown = True

    class Label:
        def __init__(self, _parent, **kwargs):
            self.image = None
            labels.append(kwargs)

        def grid(self, **kwargs):
            return self

    camera = object()
    monkeypatch.setattr(about, "MpsDialog", Dialog)
    monkeypatch.setattr(about.ttk, "Label", Label)
    monkeypatch.setattr(
        about,
        "load_camera_image",
        lambda parent, size: requested_sizes.append(size) or camera,
    )
    monkeypatch.setattr(about, "get_version", lambda: "9.8.7-test")

    dialog = about.AboutDialog(object())

    assert labels[0]["image"] is camera
    assert requested_sizes == [144]
    assert "background" not in labels[0]
    assert dialog._dialog.content.rows[0] == {"weight": 0, "minsize": 154}
    assert dialog._dialog.window.geometry_value == "660x540"
    assert dialog._dialog.window.minimum == (620, 500)
    texts = [label.get("text") for label in labels]
    assert "Mac Photo Studio" in texts
    assert "Version 9.8.7-test" in texts
    assert "Real Photography. Proven." in texts
    assert any(
        "Observe first. Decide second. Act last. Verify before trust."
        in (text or "")
        for text in texts
    )
    assert dialog._dialog.window._mps_about_camera_image is camera
    assert dialog._camera_label.image is camera


def test_about_loads_dark_144_through_active_show_route(monkeypatch):
    shown = []

    class Dialog:
        def __init__(self, parent):
            shown.append(("created", parent))

        def show(self):
            shown.append(("shown", None))

    monkeypatch.setattr(about, "AboutDialog", Dialog)
    parent = object()
    about.show_about(parent)
    assert shown == [("created", parent), ("shown", None)]
