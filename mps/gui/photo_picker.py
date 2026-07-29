from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


SUPPORTED_PHOTO_EXTENSIONS = frozenset(
    {
        ".arw",
        ".cr2",
        ".cr3",
        ".dng",
        ".jpeg",
        ".jpg",
        ".nef",
        ".orf",
        ".png",
        ".raf",
        ".rw2",
        ".tif",
        ".tiff",
    }
)

_EXCLUDED_DIRECTORY_NAMES = {
    ".cache",
    ".trash",
    ".trash-1000",
    "$recycle.bin",
    "lost+found",
    "system volume information",
}


def is_supported_photo(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.casefold() in SUPPORTED_PHOTO_EXTENSIONS
    )


def visible_photo_entries(directory: Path) -> list[Path]:
    try:
        children = tuple(directory.iterdir())
    except OSError:
        return []

    entries: list[Path] = []

    for child in children:
        name = child.name.strip()

        if not name or name.startswith("."):
            continue

        if child.is_dir():
            if name.casefold() in _EXCLUDED_DIRECTORY_NAMES:
                continue

            entries.append(child)
            continue

        if is_supported_photo(child):
            entries.append(child)

    return sorted(
        entries,
        key=lambda path: (
            0 if path.is_dir() else 1,
            path.name.casefold(),
        ),
    )


class PhotoPicker:
    def __init__(
        self,
        parent: tk.Misc,
        photo_library: Path,
        title: str,
        description: str,
    ) -> None:
        self._photo_library = photo_library.expanduser()
        self._title = title
        self._description = description
        self._result: Path | None = None

        self._window = tk.Toplevel(parent)
        self._window.title(title)
        self._window.geometry("980x720")
        self._window.minsize(800, 580)
        self._window.transient(parent)

        self._window.columnconfigure(0, weight=1)
        self._window.rowconfigure(1, weight=1)

        self._build_header()
        self._build_tree()
        self._build_footer()
        self._populate_root()

        self._window.protocol(
            "WM_DELETE_WINDOW",
            self._cancel,
        )
        self._window.bind(
            "<Escape>",
            lambda _event: self._cancel(),
        )
        self._window.bind(
            "<Return>",
            lambda _event: self._select(),
        )

        self._window.grab_set()
        self._tree.focus_set()

    @property
    def result(self) -> Path | None:
        return self._result

    def wait(self) -> Path | None:
        self._window.wait_window()
        return self._result

    def _build_header(self) -> None:
        header = ttk.Frame(
            self._window,
            padding=(22, 18, 22, 12),
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=self._title,
            font=("Sans", 20, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text=self._description,
            font=("Sans", 13),
            justify="left",
            wraplength=900,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

        ttk.Label(
            header,
            text=f"Photo Library: {self._photo_library}",
            font=("Sans", 10, "italic"),
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

    def _build_tree(self) -> None:
        tree_frame = ttk.Frame(
            self._window,
            padding=(22, 0, 22, 0),
        )
        tree_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
        )
        self._tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self._tree.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )
        self._tree.configure(
            yscrollcommand=scrollbar.set,
        )

        self._tree.bind(
            "<<TreeviewOpen>>",
            self._on_open,
        )
        self._tree.bind(
            "<<TreeviewSelect>>",
            self._on_select,
        )
        self._tree.bind(
            "<Double-1>",
            self._on_double_click,
        )

    def _build_footer(self) -> None:
        footer = ttk.Frame(
            self._window,
            padding=(22, 14, 22, 20),
        )
        footer.grid(
            row=2,
            column=0,
            sticky="ew",
        )
        footer.columnconfigure(0, weight=1)

        self._selection_label = ttk.Label(
            footer,
            text="Select a photograph to continue.",
            anchor="w",
        )
        self._selection_label.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(0, 10),
        )

        self._selected_path_label = ttk.Label(
            footer,
            text=f"Photo Library: {self._photo_library}",
            anchor="w",
            font=("Sans", 9, "italic"),
        )
        self._selected_path_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 16),
        )

        ttk.Button(
            footer,
            text="Cancel",
            command=self._cancel,
        ).grid(
            row=1,
            column=1,
            padx=(0, 8),
        )

        self._select_button = ttk.Button(
            footer,
            text="Use this photograph",
            command=self._select,
            state="disabled",
        )
        self._select_button.grid(
            row=1,
            column=2,
        )

    def _populate_root(self) -> None:
        if not self._photo_library.is_dir():
            messagebox.showerror(
                "Photo library unavailable",
                (
                    "The configured photo library does not exist:\n\n"
                    f"{self._photo_library}"
                ),
                parent=self._window,
            )
            self._window.after(0, self._cancel)
            return

        root_id = self._tree.insert(
            "",
            "end",
            text=self._photo_library.name,
            values=(str(self._photo_library), "directory"),
            open=True,
        )

        self._add_children(
            root_id,
            self._photo_library,
        )

        self._tree.selection_set(root_id)
        self._tree.focus(root_id)

    def _add_children(
        self,
        parent_id: str,
        directory: Path,
    ) -> None:
        for child in visible_photo_entries(directory):
            kind = "directory" if child.is_dir() else "photo"

            child_id = self._tree.insert(
                parent_id,
                "end",
                text=child.name,
                values=(str(child), kind),
            )

            if child.is_dir() and visible_photo_entries(child):
                self._tree.insert(
                    child_id,
                    "end",
                    text="Loading…",
                    values=("", "placeholder"),
                )

    def _on_open(
        self,
        _event: tk.Event,
    ) -> None:
        item_id = self._tree.focus()

        if not item_id:
            return

        values = self._tree.item(
            item_id,
            "values",
        )

        if len(values) < 2 or values[1] != "directory":
            return

        children = self._tree.get_children(item_id)

        if (
            len(children) == 1
            and self._tree.item(children[0], "values")
            and self._tree.item(children[0], "values")[1]
            == "placeholder"
        ):
            self._tree.delete(children[0])
            self._add_children(
                item_id,
                Path(values[0]),
            )

    def _on_select(
        self,
        _event: tk.Event,
    ) -> None:
        selected = self._selected_item()

        if selected is None:
            self._selection_label.configure(
                text="Select a photograph to continue."
            )
            self._selected_path_label.configure(
                text=f"Photo Library: {self._photo_library}"
            )
            self._select_button.configure(state="disabled")
            return

        path, kind = selected

        self._selected_path_label.configure(
            text=f"Selected: {path}"
        )

        if kind == "photo" and is_supported_photo(path):
            self._selection_label.configure(
                text="✓ This photograph can be selected."
            )
            self._select_button.configure(state="normal")
            return

        self._selection_label.configure(
            text="Open this folder or select a photograph."
        )
        self._select_button.configure(state="disabled")

    def _on_double_click(
        self,
        _event: tk.Event,
    ) -> None:
        selected = self._selected_item()

        if selected is None:
            return

        path, kind = selected

        if kind == "photo" and is_supported_photo(path):
            self._select()

    def _selected_item(self) -> tuple[Path, str] | None:
        selection = self._tree.selection()

        if not selection:
            return None

        values = self._tree.item(
            selection[0],
            "values",
        )

        if len(values) < 2 or not values[0]:
            return None

        return Path(values[0]), str(values[1])

    def _select(self) -> None:
        selected = self._selected_item()

        if selected is None:
            return

        path, kind = selected

        if kind != "photo" or not is_supported_photo(path):
            return

        self._result = path
        self._window.destroy()

    def _cancel(self) -> None:
        self._result = None
        self._window.destroy()


def choose_photo(
    parent: tk.Misc,
    photo_library: Path,
    title: str = "Choose a photograph",
    description: str = "Select a photograph.",
) -> Path | None:
    picker = PhotoPicker(
        parent=parent,
        photo_library=photo_library,
        title=title,
        description=description,
    )
    return picker.wait()
