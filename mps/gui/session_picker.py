from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


_EXCLUDED_DIRECTORY_NAMES = {
    "01_originals",
    "02_working",
    "03_exports",
    "04_archive",
    "04_delivered",
    "05_backup_reports",
    "99_admin",
    "provenance",
    ".trash",
    ".trash-1000",
}


def visible_directories(directory: Path) -> list[Path]:
    """Return selectable child directories in a stable display order."""
    try:
        children = tuple(directory.iterdir())
    except OSError:
        return []

    result: list[Path] = []

    for child in children:
        if not child.is_dir():
            continue

        name = child.name.strip()

        if not name:
            continue

        if name.startswith("."):
            continue

        if name.casefold() in _EXCLUDED_DIRECTORY_NAMES:
            continue

        result.append(child)

    return sorted(
        result,
        key=lambda path: path.name.casefold(),
    )


def has_culling_content(directory: Path) -> bool:
    """Return whether a directory looks like an imported photo session."""
    originals = directory / "01_ORIGINALS"

    if originals.is_dir():
        return True

    try:
        children = tuple(directory.iterdir())
    except OSError:
        return False

    photo_extensions = {
        ".arw",
        ".cr2",
        ".cr3",
        ".dng",
        ".nef",
        ".orf",
        ".raf",
        ".rw2",
        ".jpg",
        ".jpeg",
    }

    return any(
        child.is_file()
        and child.suffix.casefold() in photo_extensions
        for child in children
    )


class ImportSessionPicker:
    def __init__(
        self,
        parent: tk.Misc,
        photo_library: Path,
        title: str,
    ) -> None:
        self._photo_library = photo_library.expanduser()
        self._result: Path | None = None

        self._window = tk.Toplevel(parent)
        self._window.title(title)
        self._window.geometry("800x620")
        self._window.minsize(680, 500)
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
            padding=(20, 18, 20, 12),
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Choose the photo shoot you want to review",
            font=("Sans", 15, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text=(
                "Open the folders in your Photo Library until you reach "
                "the folder for one photo shoot. This is normally organised "
                "as Year → Month → Photo Shoot.\n\n"
                "Example: 2026 → 07 → 15_Bird_Sanctuary"
            ),
            justify="left",
            wraplength=740,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

        ttk.Label(
            header,
            text=f"Photo library: {self._photo_library}",
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
            padding=(20, 0, 20, 0),
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
            padding=(20, 14, 20, 20),
        )
        footer.grid(
            row=2,
            column=0,
            sticky="ew",
        )
        footer.columnconfigure(0, weight=1)

        self._selection_label = ttk.Label(
            footer,
            text="Continue opening folders until you reach a photo shoot.",
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
            text="Open this photo shoot",
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
            values=(str(self._photo_library),),
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
        for child in visible_directories(directory):
            child_id = self._tree.insert(
                parent_id,
                "end",
                text=child.name,
                values=(str(child),),
            )

            if visible_directories(child):
                self._tree.insert(
                    child_id,
                    "end",
                    text="Loading…",
                    values=("",),
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

        if not values:
            return

        directory = Path(values[0])

        children = self._tree.get_children(item_id)

        if (
            len(children) == 1
            and self._tree.item(
                children[0],
                "text",
            )
            == "Loading…"
        ):
            self._tree.delete(children[0])
            self._add_children(
                item_id,
                directory,
            )

    def _on_select(
        self,
        _event: tk.Event,
    ) -> None:
        directory = self._selected_directory()

        if directory is None:
            self._selection_label.configure(
                text="Continue opening folders until you reach a photo shoot."
            )
            self._selected_path_label.configure(
                text=f"Photo Library: {self._photo_library}"
            )
            self._select_button.configure(state="disabled")
            return

        is_photo_shoot = has_culling_content(directory)
        self._selection_label.configure(
            text=(
                "✓ This photo shoot can be opened."
                if is_photo_shoot
                else "Continue opening folders until you reach a photo shoot."
            )
        )
        self._selected_path_label.configure(
            text=f"Selected folder: {directory}"
        )
        self._select_button.configure(
            state="normal" if is_photo_shoot else "disabled"
        )

    def _on_double_click(
        self,
        _event: tk.Event,
    ) -> None:
        directory = self._selected_directory()

        if (
            directory is not None
            and has_culling_content(directory)
        ):
            self._select()

    def _selected_directory(self) -> Path | None:
        selection = self._tree.selection()

        if not selection:
            return None

        values = self._tree.item(
            selection[0],
            "values",
        )

        if not values or not values[0]:
            return None

        return Path(values[0])

    def _select(self) -> None:
        directory = self._selected_directory()

        if directory is None:
            return

        if not has_culling_content(directory):
            messagebox.showinfo(
                "Choose a photo shoot",
                (
                    "This folder is not yet a photo shoot.\n\n"
                    "Continue through Year and Month until you reach "
                    "the folder that contains the photographs from one shoot."
                ),
                parent=self._window,
            )
            return

        self._result = directory
        self._window.destroy()

    def _cancel(self) -> None:
        self._result = None
        self._window.destroy()


def choose_import_session(
    parent: tk.Misc,
    photo_library: Path,
    title: str = "Choose a photo shoot",
) -> Path | None:
    picker = ImportSessionPicker(
        parent=parent,
        photo_library=photo_library,
        title=title,
    )
    return picker.wait()
