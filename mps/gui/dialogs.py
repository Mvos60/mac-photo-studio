from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable


TITLE_FONT = ("Sans", 20, "bold")
SECTION_TITLE_FONT = ("Sans", 14, "bold")
BODY_FONT = ("Sans", 13)
BODY_BOLD_FONT = ("Sans", 13, "bold")
BODY_ITALIC_FONT = ("Sans", 13, "italic")
DIALOG_TITLE_FONT = ("Sans", 18, "bold")


@dataclass(frozen=True, slots=True)
class DialogSize:
    width: int
    height: int
    minimum_width: int
    minimum_height: int

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}"


DIALOG_SIZES: dict[str, DialogSize] = {
    "small": DialogSize(620, 420, 520, 340),
    "medium": DialogSize(820, 560, 680, 460),
    "large": DialogSize(1040, 720, 860, 600),
    "wide": DialogSize(1180, 760, 980, 620),
}


def get_dialog_size(name: str) -> DialogSize:
    try:
        return DIALOG_SIZES[name]
    except KeyError as exc:
        choices = ", ".join(sorted(DIALOG_SIZES))
        raise ValueError(
            f"Unknown MPS dialog size {name!r}. Choose from: {choices}."
        ) from exc


class MpsDialog:
    """Shared foundation for consistent MPS modal dialogs."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        title: str,
        size: str = "medium",
        modal: bool = True,
        resizable: bool = True,
    ) -> None:
        dimensions = get_dialog_size(size)

        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(dimensions.geometry)
        self.window.minsize(
            dimensions.minimum_width,
            dimensions.minimum_height,
        )
        self.window.transient(parent)
        self.window.resizable(resizable, resizable)

        self._modal = modal
        self._configure_styles()

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())

        self.header = ttk.Frame(
            self.window,
            padding=(22, 18, 22, 12),
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.columnconfigure(0, weight=1)

        self.content = ttk.Frame(
            self.window,
            padding=(22, 0, 22, 0),
        )
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.footer = ttk.Frame(
            self.window,
            padding=(22, 10, 22, 18),
        )
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.columnconfigure(0, weight=1)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.window)
        style.configure(
            "Mps.TButton",
            font=BODY_FONT,
            padding=(10, 6),
        )
        style.configure(
            "Mps.TLabelframe.Label",
            font=SECTION_TITLE_FONT,
        )

    def add_header(
        self,
        title: str,
        description: str | None = None,
        *,
        wraplength: int = 940,
    ) -> None:
        ttk.Label(
            self.header,
            text=title,
            font=TITLE_FONT,
        ).grid(row=0, column=0, sticky="w")

        if description:
            ttk.Label(
                self.header,
                text=description,
                font=BODY_FONT,
                justify="left",
                wraplength=wraplength,
            ).grid(
                row=1,
                column=0,
                sticky="ew",
                pady=(6, 0),
            )

    def create_section(
        self,
        parent: tk.Misc | None = None,
        *,
        title: str,
        padding: tuple[int, int] = (12, 8),
    ) -> ttk.LabelFrame:
        section = ttk.LabelFrame(
            parent or self.content,
            text=title,
            padding=padding,
            style="Mps.TLabelframe",
        )
        section.columnconfigure(0, weight=1)
        return section

    def add_close_button(
        self,
        *,
        text: str = "Close",
        column: int = 1,
    ) -> ttk.Button:
        button = ttk.Button(
            self.footer,
            text=text,
            style="Mps.TButton",
            command=self.close,
        )
        button.grid(row=0, column=column, sticky="e")
        return button

    def add_footer_button(
        self,
        *,
        text: str,
        command: Callable[[], None],
        column: int,
        padx: tuple[int, int] = (0, 8),
    ) -> ttk.Button:
        button = ttk.Button(
            self.footer,
            text=text,
            style="Mps.TButton",
            command=command,
        )
        button.grid(
            row=0,
            column=column,
            padx=padx,
        )
        return button

    def show(self) -> None:
        if self._modal:
            self.window.grab_set()
        self.window.focus_set()

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
