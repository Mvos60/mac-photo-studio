from mps.gui import import_session_action_selector as module


class _FakeWindow:
    def __init__(self):
        self.protocols = []
        self.bindings = []

    def protocol(self, name, callback):
        self.protocols.append((name, callback))

    def bind(self, event, callback):
        self.bindings.append((event, callback))

    def wait_window(self):
        return None


class _FakeDialog:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.options = kwargs
        self.content = object()
        self.window = _FakeWindow()
        self.buttons = []
        self.closed = False
        self.shown = False

    def add_header(self, title, subtitle):
        self.header = (title, subtitle)

    def add_footer_button(self, **kwargs):
        self.buttons.append(kwargs)

    def close(self):
        self.closed = True

    def show(self):
        self.shown = True


class _FakeLabel:
    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.options = kwargs

    def grid(self, **kwargs):
        self.grid_options = kwargs


def _selector(monkeypatch, parent=object()):
    dialog = _FakeDialog(parent)
    monkeypatch.setattr(module, "MpsDialog", lambda *args, **kwargs: dialog)
    monkeypatch.setattr(module.ttk, "Label", _FakeLabel)
    selector = module.ImportSessionActionSelector(parent)
    return selector, dialog


def test_dialog_resume_action_and_explicit_labels(monkeypatch):
    selector, dialog = _selector(monkeypatch)

    assert [button["text"] for button in dialog.buttons] == [
        "Cancel",
        "Start new",
        "Resume",
    ]
    dialog.buttons[2]["command"]()

    assert selector.result == "resume"
    assert dialog.closed is True


def test_dialog_start_new_action(monkeypatch):
    selector, dialog = _selector(monkeypatch)

    dialog.buttons[1]["command"]()

    assert selector.result == "start-new"
    assert dialog.closed is True


def test_dialog_cancel_close_and_escape_return_cancel(monkeypatch):
    selector, dialog = _selector(monkeypatch)

    dialog.buttons[0]["command"]()
    assert selector.result == "cancel"
    assert dialog.closed is True

    selector, dialog = _selector(monkeypatch)
    dialog.window.protocols[0][1]()
    assert selector.result == "cancel"

    selector, dialog = _selector(monkeypatch)
    dialog.window.bindings[0][1](None)
    assert selector.result == "cancel"
