from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from mps.gui.session_picker import choose_import_session
from mps.paths import get_photo_library

from mps.services.quarantine_manager import (
    QuarantineItem,
    permanently_delete_quarantine_item,
    restore_quarantine_item,
    scan_quarantine,
    total_quarantine_size,
)


TITLE_FONT = ("Sans", 20, "bold")
SECTION_TITLE_FONT = ("Sans", 14, "bold")
BODY_FONT = ("Sans", 13)
BODY_BOLD_FONT = ("Sans", 13, "bold")
BODY_ITALIC_FONT = ("Sans", 13, "italic")
DIALOG_TITLE_FONT = ("Sans", 18, "bold")


def format_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            return (
                f"{int(size)} {unit}"
                if unit == "B"
                else f"{size:.1f} {unit}"
            )
        size /= 1024.0
    return f"{value} B"



def photo_library_for_import_root(import_root: Path) -> Path:
    root = import_root.expanduser()
    parents = root.parents
    if len(parents) >= 3:
        return parents[2]
    if len(parents) >= 1:
        return parents[-1]
    return root


def quarantine_folder_for_import_root(import_root: Path) -> Path:
    return import_root.expanduser() / ".mps_quarantine" / "culling"


def item_detail_values(
    item: QuarantineItem | None,
) -> tuple[str, str, str]:
    if item is None:
        return ("No photograph selected", "—", "—")
    return (
        item.stem,
        str(item.original_raw_path or "Unknown"),
        str(item.raw_quarantine_path or item.quarantine_root),
    )

def item_status(item: QuarantineItem) -> str:
    if item.restorable:
        return "Ready to restore"
    return "Incomplete"


class QuarantineManagerDialog:
    def __init__(
        self,
        parent: tk.Misc,
        import_root: Path,
    ) -> None:
        self._import_root = import_root.expanduser()
        self._photo_library = photo_library_for_import_root(
            self._import_root
        )
        self._quarantine_folder = quarantine_folder_for_import_root(
            self._import_root
        )
        self._items: dict[str, QuarantineItem] = {}

        self._window = tk.Toplevel(parent)
        self._window.title("Quarantine Manager")
        self._window.geometry("1180x965")
        self._window.minsize(980, 825)
        self._window.transient(parent)

        self._configure_styles()

        self._window.columnconfigure(0, weight=1)
        self._window.rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()
        self._build_footer()

        self._window.protocol(
            "WM_DELETE_WINDOW",
            self._window.destroy,
        )
        self._window.bind(
            "<Escape>",
            lambda _event: self._window.destroy(),
        )

        self._refresh()
        self._window.grab_set()
        self._window.focus_set()

    def _configure_styles(self) -> None:
        style = ttk.Style(self._window)
        style.configure("Quarantine.Treeview", font=BODY_FONT, rowheight=36)
        style.configure("Quarantine.Treeview.Heading", font=BODY_BOLD_FONT)
        style.configure("Quarantine.TButton", font=BODY_FONT, padding=(10, 6))
        style.configure("Quarantine.TLabelframe.Label", font=SECTION_TITLE_FONT)

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
            text="Quarantine Manager",
            font=TITLE_FONT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text=(
                "During culling, one or more RAW photographs were removed. "
                "Mac Photo Studio kept them safely in Safe Quarantine "
                "instead of deleting them immediately."
            ),
            font=BODY_FONT,
            justify="left",
            wraplength=980,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

        session_info = ttk.Frame(header)
        session_info.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(12, 0),
        )
        session_info.columnconfigure(1, weight=1)

        details = (
            ("Photo library:", self._photo_library),
            ("Import session:", self._import_root),
            ("Quarantine folder:", self._quarantine_folder),
        )
        for row, (label, value) in enumerate(details):
            ttk.Label(
                session_info,
                text=label,
                font=BODY_BOLD_FONT,
            ).grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(0, 10),
                pady=(0, 3),
            )
            ttk.Label(
                session_info,
                text=str(value),
                font=BODY_ITALIC_FONT,
                justify="left",
                wraplength=850,
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=(0, 3),
            )

    def _build_content(self) -> None:
        content = ttk.Frame(
            self._window,
            padding=(22, 0, 22, 0),
        )
        content.grid(
            row=1,
            column=0,
            sticky="nsew",
        )
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1, minsize=125)

        help_box = ttk.LabelFrame(
            content,
            text="What can I do here?",
            padding=(12, 6),
            style="Quarantine.TLabelframe",
        )
        help_box.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        help_box.columnconfigure(0, weight=1)

        ttk.Label(
            help_box,
            text=(
                "Restore a photograph when you removed it by mistake. "
                "Permanently remove it only when you are certain it is no "
                "longer needed; MPS will ask for confirmation twice."
            ),
            font=BODY_FONT,
            justify="left",
            wraplength=940,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
        )

        toolbar = ttk.Frame(content)
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        toolbar.columnconfigure(4, weight=1)

        ttk.Button(
            toolbar,
            text="↩ Restore",
            style="Quarantine.TButton",
            command=self._restore_selected,
        ).grid(row=0, column=0, padx=(0, 8))

        ttk.Button(
            toolbar,
            text="🗑 Delete permanently",
            style="Quarantine.TButton",
            command=self._delete_selected,
        ).grid(row=0, column=1, padx=(0, 8))

        ttk.Button(
            toolbar,
            text="⟳ Refresh",
            style="Quarantine.TButton",
            command=self._refresh,
        ).grid(row=0, column=2, padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Details",
            style="Quarantine.TButton",
            command=self._show_selected_details,
        ).grid(row=0, column=3)

        list_frame = ttk.Frame(content)
        list_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = (
            "candidate",
            "date",
            "size",
            "status",
            "location",
        )
        self._tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Quarantine.Treeview",
        )

        headings = {
            "candidate": "Photograph",
            "date": "Quarantined",
            "size": "Size",
            "status": "Recovery status",
            "location": "Original RAW location",
        }
        widths = {
            "candidate": 145,
            "date": 165,
            "size": 95,
            "status": 170,
            "location": 445,
        }

        for column in columns:
            self._tree.heading(
                column,
                text=headings[column],
            )
            self._tree.column(
                column,
                width=widths[column],
                anchor="w",
            )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self._tree.yview,
        )
        self._tree.configure(
            yscrollcommand=scrollbar.set,
        )

        self._tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self._tree.bind(
            "<<TreeviewSelect>>",
            self._update_selection_details,
        )
        self._tree.bind(
            "<Double-1>",
            self._on_tree_double_click,
        )
        self._tree.bind(
            "<Button-3>",
            self._show_context_menu,
        )

        self._context_menu = tk.Menu(
            self._window,
            tearoff=False,
            font=BODY_FONT,
            relief="raised",
            borderwidth=1,
        )
        self._context_menu.add_command(
            label="Restore",
            command=self._restore_selected,
        )
        self._context_menu.add_command(
            label="Delete permanently",
            command=self._delete_selected,
        )
        self._context_menu.add_separator()
        self._context_menu.add_command(
            label="Show details",
            command=self._show_selected_details,
        )
        self._context_menu.add_command(
            label="Copy original RAW path",
            command=self._copy_original_path,
        )

        lower_panel = ttk.Frame(content)
        lower_panel.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        lower_panel.columnconfigure(0, weight=1)

        detail_box = ttk.LabelFrame(
            lower_panel,
            text="Selected photograph details",
            padding=(12, 8),
            style="Quarantine.TLabelframe",
        )
        detail_box.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        detail_box.columnconfigure(0, weight=1)

        self._selected_raw_var = tk.StringVar()
        self._original_raw_var = tk.StringVar()
        self._quarantined_raw_var = tk.StringVar()

        detail_rows = (
            ("Photograph", self._selected_raw_var),
            (
                "Original location (before culling)",
                self._original_raw_var,
            ),
            (
                "Current quarantine location",
                self._quarantined_raw_var,
            ),
        )
        for row, (label, variable) in enumerate(detail_rows):
            base_row = row * 2
            ttk.Label(
                detail_box,
                text=f"{label}:",
                font=BODY_BOLD_FONT,
                justify="left",
                anchor="w",
            ).grid(
                row=base_row,
                column=0,
                sticky="ew",
                pady=(0 if row == 0 else 6, 1),
            )
            ttk.Label(
                detail_box,
                textvariable=variable,
                font=BODY_FONT,
                justify="left",
                anchor="w",
                wraplength=1040,
            ).grid(
                row=base_row + 1,
                column=0,
                sticky="ew",
                pady=(0, 2),
            )

        legend = ttk.LabelFrame(
            lower_panel,
            text="Recovery status",
            padding=(12, 6),
            style="Quarantine.TLabelframe",
        )
        legend.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        legend.columnconfigure(1, weight=1)

        legend_rows = (
            ("Ready", "Complete recovery information is available."),
            (
                "Incomplete",
                "Recovery metadata is missing; restore is unavailable.",
            ),
        )
        for row, (status, explanation) in enumerate(legend_rows):
            ttk.Label(
                legend,
                text=status,
                font=BODY_BOLD_FONT,
            ).grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(0, 12),
                pady=(0, 2),
            )
            ttk.Label(
                legend,
                text=explanation,
                font=BODY_FONT,
                justify="left",
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=(0, 2),
            )

        self._summary = ttk.Label(content, text="", anchor="w", font=BODY_FONT)
        self._summary.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        self._set_selection_details(None)

    def _build_footer(self) -> None:
        footer = ttk.Frame(
            self._window,
            padding=(22, 10, 22, 18),
        )
        footer.grid(
            row=2,
            column=0,
            sticky="ew",
        )
        footer.columnconfigure(2, weight=1)

        ttk.Button(
            footer,
            text="Select All",
            style="Quarantine.TButton",
            command=self._select_all,
        ).grid(
            row=0,
            column=0,
            padx=(0, 8),
        )

        ttk.Button(
            footer,
            text="Select None",
            style="Quarantine.TButton",
            command=self._select_none,
        ).grid(
            row=0,
            column=1,
        )

        ttk.Label(
            footer,
            text="Tip: right-click an item for more actions.",
            font=BODY_ITALIC_FONT,
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=(12, 12),
        )

        ttk.Button(
            footer,
            text="Close",
            style="Quarantine.TButton",
            command=self._window.destroy,
        ).grid(
            row=0,
            column=3,
            sticky="e",
        )

    def _refresh(self) -> None:
        self._tree.delete(
            *self._tree.get_children()
        )
        items = scan_quarantine(self._import_root)
        self._items = {
            str(index): item
            for index, item in enumerate(items)
        }

        for key, item in self._items.items():
            self._tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    item.stem,
                    item.created_at.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    format_size(item.total_size),
                    item_status(item),
                    str(
                        item.original_raw_path
                        or "Unknown"
                    ),
                ),
            )

        count = len(items)
        noun = "item" if count == 1 else "items"
        self._summary.configure(
            text=(
                f"{count} quarantine {noun} — "
                f"{format_size(total_quarantine_size(items))} used"
            )
        )
        self._set_selection_details(None)

    def _set_selection_details(
        self,
        item: QuarantineItem | None,
    ) -> None:
        selected_raw, original_raw, quarantined_raw = (
            item_detail_values(item)
        )
        self._selected_raw_var.set(selected_raw)
        self._original_raw_var.set(original_raw)
        self._quarantined_raw_var.set(quarantined_raw)

    def _update_selection_details(
        self,
        _event: tk.Event[tk.Misc] | None = None,
    ) -> None:
        selection = self._tree.selection()
        if len(selection) != 1:
            self._set_selection_details(None)
            if len(selection) > 1:
                self._selected_raw_var.set(
                    f"{len(selection)} photographs selected"
                )
            return
        self._set_selection_details(
            self._items.get(selection[0])
        )

    def _selected_items(
        self,
    ) -> list[QuarantineItem]:
        return [
            self._items[key]
            for key in self._tree.selection()
        ]

    def _select_all(self) -> None:
        self._tree.selection_set(
            self._tree.get_children()
        )
        self._update_selection_details()

    def _select_none(self) -> None:
        self._tree.selection_remove(
            self._tree.selection()
        )
        self._update_selection_details()

    def _single_selected_item(self) -> QuarantineItem | None:
        selection = self._tree.selection()
        if len(selection) != 1:
            return None
        return self._items.get(selection[0])

    def _on_tree_double_click(
        self,
        event: tk.Event[tk.Misc],
    ) -> None:
        row = self._tree.identify_row(event.y)
        if row:
            self._tree.selection_set(row)
            self._tree.focus(row)
            self._update_selection_details()
            self._show_selected_details()

    def _show_context_menu(
        self,
        event: tk.Event[tk.Misc],
    ) -> None:
        row = self._tree.identify_row(event.y)
        if not row:
            return
        if row not in self._tree.selection():
            self._tree.selection_set(row)
            self._tree.focus(row)
            self._update_selection_details()
        self._context_menu.tk_popup(
            event.x_root,
            event.y_root,
        )

    def _copy_text(self, value: str) -> None:
        self._window.clipboard_clear()
        self._window.clipboard_append(value)
        self._window.update_idletasks()

    def _copy_original_path(self) -> None:
        item = self._single_selected_item()
        if item is None:
            messagebox.showinfo(
                "Quarantine Manager",
                "Select exactly one photograph first.",
                parent=self._window,
            )
            return
        self._copy_text(str(item.original_raw_path or "Unknown"))

    def _show_selected_details(self) -> None:
        item = self._single_selected_item()
        if item is None:
            messagebox.showinfo(
                "Quarantine Manager",
                "Select exactly one photograph first.",
                parent=self._window,
            )
            return

        dialog = tk.Toplevel(self._window)
        dialog.title(f"Quarantine details — {item.stem}")
        dialog.transient(self._window)
        dialog.geometry("960x645")
        dialog.minsize(820, 595)

        frame = ttk.Frame(dialog, padding=(22, 18, 22, 20))
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)

        ttk.Label(
            frame,
            text=item.stem,
            font=DIALOG_TITLE_FONT,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 14),
        )

        ttk.Label(
            frame,
            text="Recovery status:",
            font=BODY_BOLD_FONT,
        ).grid(
            row=1,
            column=0,
            sticky="nw",
            padx=(0, 10),
            pady=(0, 8),
        )
        ttk.Label(
            frame,
            text=item_status(item),
            font=BODY_FONT,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )

        ttk.Label(
            frame,
            text="Original location (before culling):",
            font=BODY_BOLD_FONT,
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4, 4),
        )
        ttk.Label(
            frame,
            text=str(item.original_raw_path or "Unknown"),
            font=BODY_FONT,
            justify="left",
            wraplength=760,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
        )
        ttk.Button(
            frame,
            text="Copy original location",
            style="Quarantine.TButton",
            command=lambda: self._copy_text(
                str(item.original_raw_path or "Unknown")
            ),
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 10),
        )

        ttk.Label(
            frame,
            text="Current quarantine location:",
            font=BODY_BOLD_FONT,
        ).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4, 4),
        )
        ttk.Label(
            frame,
            text=str(item.raw_quarantine_path or item.quarantine_root),
            font=BODY_FONT,
            justify="left",
            wraplength=760,
        ).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
        )
        ttk.Button(
            frame,
            text="Copy quarantine location",
            style="Quarantine.TButton",
            command=lambda: self._copy_text(
                str(item.raw_quarantine_path or item.quarantine_root)
            ),
        ).grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 10),
        )

        ttk.Label(
            frame,
            text="Quarantined:",
            font=BODY_BOLD_FONT,
        ).grid(
            row=8,
            column=0,
            sticky="nw",
            padx=(0, 10),
            pady=(0, 8),
        )
        ttk.Label(
            frame,
            text=item.created_at.strftime("%Y-%m-%d %H:%M"),
            font=BODY_FONT,
        ).grid(
            row=8,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )

        ttk.Label(
            frame,
            text="Size:",
            font=BODY_BOLD_FONT,
        ).grid(
            row=9,
            column=0,
            sticky="nw",
            padx=(0, 10),
            pady=(0, 8),
        )
        ttk.Label(
            frame,
            text=format_size(item.total_size),
            font=BODY_FONT,
        ).grid(
            row=9,
            column=1,
            sticky="ew",
            pady=(0, 8),
        )

        ttk.Separator(
            frame,
            orient="horizontal",
        ).grid(
            row=10,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 12),
        )

        ttk.Button(
            frame,
            text="Close",
            style="Quarantine.TButton",
            command=dialog.destroy,
        ).grid(
            row=11,
            column=0,
            columnspan=2,
            sticky="e",
        )

        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()
        dialog.focus_set()

    def _restore_selected(self) -> None:
        selected = self._selected_items()
        if not selected:
            messagebox.showinfo(
                "Quarantine Manager",
                "Select one or more items first.",
                parent=self._window,
            )
            return

        blocked = [
            item.stem
            for item in selected
            if not item.restorable
        ]
        if blocked:
            messagebox.showwarning(
                "Restore unavailable",
                (
                    "These quarantine items have incomplete or "
                    "unavailable recovery information:\n\n"
                    + "\n".join(blocked)
                    + (
                        "\n\nThey cannot currently be restored. "
                        "Nothing was changed."
                    )
                ),
                parent=self._window,
            )
            return

        if not messagebox.askyesno(
            "Confirm restore",
            (
                f"Restore {len(selected)} selected item(s)?\n\n"
                "The RAW files and their MPS records will be "
                "returned to their original locations."
            ),
            parent=self._window,
        ):
            return

        results = [
            restore_quarantine_item(
                self._import_root,
                item,
            )
            for item in selected
        ]
        successes = sum(
            result.success
            for result in results
        )
        details = "\n".join(
            f"{result.stem}: {result.message}"
            for result in results
        )
        dialog = (
            messagebox.showinfo
            if successes == len(results)
            else messagebox.showwarning
        )
        dialog(
            "Restore report",
            (
                f"Restored: {successes}\n"
                f"Failed: {len(results) - successes}\n\n"
                f"{details}"
            ),
            parent=self._window,
        )
        self._refresh()

    def _delete_selected(self) -> None:
        selected = self._selected_items()
        if not selected:
            messagebox.showinfo(
                "Quarantine Manager",
                "Select one or more items first.",
                parent=self._window,
            )
            return

        names = "\n".join(
            item.stem
            for item in selected
        )
        if not messagebox.askyesno(
            "Permanent removal",
            (
                f"Permanently remove "
                f"{len(selected)} quarantine item(s)?\n\n"
                f"{names}\n\n"
                "This action cannot be undone."
            ),
            icon="warning",
            parent=self._window,
        ):
            return

        typed = self._ask_delete_confirmation()
        if typed != "DELETE":
            messagebox.showinfo(
                "Permanent removal cancelled",
                (
                    "The confirmation text did not match. "
                    "Nothing was deleted."
                ),
                parent=self._window,
            )
            return

        results = [
            permanently_delete_quarantine_item(
                self._import_root,
                item,
            )
            for item in selected
        ]
        successes = sum(
            result.success
            for result in results
        )
        released = sum(
            result.released_bytes
            for result in results
            if result.success
        )
        details = "\n".join(
            f"{result.stem}: {result.message}"
            for result in results
        )
        dialog = (
            messagebox.showinfo
            if successes == len(results)
            else messagebox.showwarning
        )
        dialog(
            "Permanent removal report",
            (
                f"Removed: {successes}\n"
                f"Failed: {len(results) - successes}\n"
                f"Space released: {format_size(released)}\n\n"
                f"{details}"
            ),
            parent=self._window,
        )
        self._refresh()

    def _ask_delete_confirmation(
        self,
    ) -> str | None:
        dialog = tk.Toplevel(self._window)
        dialog.title("Confirm permanent removal")
        dialog.transient(self._window)
        dialog.resizable(False, False)

        result: dict[str, str | None] = {
            "value": None
        }

        frame = ttk.Frame(
            dialog,
            padding=(22, 18, 22, 20),
        )
        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text="Permanent removal",
            font=DIALOG_TITLE_FONT,
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            frame,
            text=(
                "Type DELETE exactly to confirm that the "
                "selected quarantine items may be removed forever."
            ),
            font=BODY_FONT,
            justify="left",
            wraplength=470,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 12),
        )

        entry = ttk.Entry(
            frame,
            width=36,
            font=BODY_FONT,
        )
        entry.grid(
            row=2,
            column=0,
            sticky="ew",
        )
        entry.focus_set()

        buttons = ttk.Frame(frame)
        buttons.grid(
            row=3,
            column=0,
            sticky="e",
            pady=(16, 0),
        )

        def accept() -> None:
            result["value"] = entry.get()
            dialog.destroy()

        ttk.Button(
            buttons,
            text="Cancel",
            style="Quarantine.TButton",
            command=dialog.destroy,
        ).grid(
            row=0,
            column=0,
            padx=(0, 8),
        )
        ttk.Button(
            buttons,
            text="Confirm Permanent Removal",
            style="Quarantine.TButton",
            command=accept,
        ).grid(
            row=0,
            column=1,
        )

        dialog.bind(
            "<Return>",
            lambda _event: accept(),
        )
        dialog.bind(
            "<Escape>",
            lambda _event: dialog.destroy(),
        )
        dialog.grab_set()
        self._window.wait_window(dialog)
        return result["value"]


def show_quarantine_manager(
    parent: tk.Misc,
) -> None:
    selected = choose_import_session(
        parent=parent,
        photo_library=get_photo_library(),
        title="Choose the photo shoot to review",
    )
    if selected is None:
        return

    QuarantineManagerDialog(
        parent,
        selected,
    )