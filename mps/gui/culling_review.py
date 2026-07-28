from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Sequence

from mps.services.culling_analyzer import (
    CullingAnalysis,
    CullingCandidateStatus,
    MissingImportedJpeg,
    analyze_culling,
)
from mps.services.culling_executor import (
    CullingExecutionResult,
    execute_culling_candidate,
)


@dataclass(frozen=True, slots=True)
class CandidateSelection:
    candidates: tuple[MissingImportedJpeg, ...]


AnalysisLoader = Callable[[Path], CullingAnalysis]
CandidateExecutor = Callable[
    [str | Path, MissingImportedJpeg],
    CullingExecutionResult,
]


def execute_selected_candidates(
    session: Path,
    candidates: Sequence[MissingImportedJpeg],
    executor: CandidateExecutor = execute_culling_candidate,
) -> tuple[CullingExecutionResult, ...]:
    return tuple(
        executor(session, candidate)
        for candidate in candidates
    )


def build_confirmation_message(
    candidates: Sequence[MissingImportedJpeg],
) -> str:
    return (
        f"{len(candidates)} selected candidate(s) will now be "
        "processed.\n\n"
        "Verified RAW files and their provenance data will be "
        "moved to this import session's Safe Quarantine. The "
        "import manifest and certificate index will be updated.\n\n"
        "Nothing will be permanently deleted. Each candidate is "
        "handled transactionally and rolled back if its execution "
        "fails.\n\n"
        "Continue with Safe Quarantine?"
    )


def execution_totals(
    results: Sequence[CullingExecutionResult],
) -> dict[str, int]:
    successful = tuple(
        result for result in results if result.success
    )
    failed = tuple(
        result for result in results if not result.success
    )

    return {
        "successful": len(successful),
        "failed": len(failed),
        "raws": sum(
            result.raw_quarantine_path is not None
            for result in successful
        ),
        "manifest": sum(
            result.removed_manifest_entries
            for result in successful
        ),
        "index": sum(
            result.removed_index_entries
            for result in successful
        ),
        "provenance": sum(
            result.quarantined_provenance_items
            for result in successful
        ),
    }


def result_status_text(
    result: CullingExecutionResult,
) -> str:
    return "SUCCESS" if result.success else "FAILED"


def result_detail_text(
    result: CullingExecutionResult,
) -> str:
    lines = [
        f"Status: {result_status_text(result)}",
        result.message,
    ]

    if result.raw_quarantine_path is not None:
        lines.append(
            f"RAW quarantine: {result.raw_quarantine_path}"
        )

    if result.success:
        lines.extend(
            [
                (
                    "Manifest entries removed: "
                    f"{result.removed_manifest_entries}"
                ),
                (
                    "Index entries removed: "
                    f"{result.removed_index_entries}"
                ),
                (
                    "Provenance items moved: "
                    f"{result.quarantined_provenance_items}"
                ),
            ]
        )

    return "\n".join(lines)


def load_culling_analysis(
    session: Path,
) -> CullingAnalysis:
    from mps.main import load_settings

    return analyze_culling(
        session,
        load_settings(),
    )


def actionable_candidates(
    analysis: CullingAnalysis,
) -> tuple[MissingImportedJpeg, ...]:
    return tuple(analysis.actionable_candidates)


def candidate_title(
    candidate: MissingImportedJpeg,
) -> str:
    if candidate.raw_path is not None:
        return candidate.raw_path.name

    return candidate.stem


def candidate_details(
    candidate: MissingImportedJpeg,
) -> str:
    if (
        candidate.status
        == CullingCandidateStatus.CULL_CANDIDATE
    ):
        return (
            "JPEG removed · RAW verified · "
            "eligible for Safe Quarantine"
        )

    if (
        candidate.status
        == (
            CullingCandidateStatus
            .PROVENANCE_CLEANUP_CANDIDATE
        )
    ):
        return (
            "JPEG removed · no imported RAW · "
            "provenance cleanup candidate"
        )

    return "Not actionable"


class CullingResultDialog:
    def __init__(
        self,
        parent: tk.Misc,
        session: Path,
        results: Sequence[CullingExecutionResult],
    ) -> None:
        self._results = tuple(results)
        totals = execution_totals(self._results)

        self._window = tk.Toplevel(parent)
        self._window.title("Safe Quarantine Report")
        self._window.geometry("900x650")
        self._window.minsize(760, 520)
        self._window.transient(parent)

        self._window.columnconfigure(0, weight=1)
        self._window.rowconfigure(2, weight=1)

        header = ttk.Frame(
            self._window,
            padding=(22, 18, 22, 10),
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Safe Quarantine Report",
            font=("Sans", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text=f"Session: {session}",
            font=("Sans", 10, "italic"),
            wraplength=840,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

        summary = ttk.Frame(
            self._window,
            padding=(22, 0, 22, 12),
        )
        summary.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        labels = (
            (
                "Successful",
                totals["successful"],
            ),
            (
                "Failed",
                totals["failed"],
            ),
            (
                "RAWs quarantined",
                totals["raws"],
            ),
            (
                "Provenance moved",
                totals["provenance"],
            ),
        )

        for column, (label, value) in enumerate(labels):
            card = ttk.Frame(
                summary,
                padding=(14, 10),
                relief="solid",
                borderwidth=1,
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0, 8 if column < 3 else 0),
            )
            summary.columnconfigure(column, weight=1)

            ttk.Label(
                card,
                text=str(value),
                font=("Sans", 16, "bold"),
                anchor="center",
            ).grid(
                row=0,
                column=0,
                sticky="ew",
            )

            ttk.Label(
                card,
                text=label,
                anchor="center",
            ).grid(
                row=1,
                column=0,
                sticky="ew",
                pady=(3, 0),
            )

        content = ttk.Frame(
            self._window,
            padding=(22, 0, 22, 0),
        )
        content.grid(
            row=2,
            column=0,
            sticky="nsew",
        )
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        canvas = tk.Canvas(
            content,
            highlightthickness=0,
        )
        canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            content,
            orient="vertical",
            command=canvas.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        canvas.configure(
            yscrollcommand=scrollbar.set,
        )

        result_frame = ttk.Frame(
            canvas,
            padding=(8, 8),
        )
        canvas_window = canvas.create_window(
            (0, 0),
            window=result_frame,
            anchor="nw",
        )

        result_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(
                scrollregion=canvas.bbox("all"),
            ),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                canvas_window,
                width=event.width,
            ),
        )

        result_frame.columnconfigure(0, weight=1)

        for row, result in enumerate(self._results):
            card = ttk.Frame(
                result_frame,
                padding=(12, 10),
                relief="solid",
                borderwidth=1,
            )
            card.grid(
                row=row,
                column=0,
                sticky="ew",
                pady=(0, 8),
            )
            card.columnconfigure(0, weight=1)

            ttk.Label(
                card,
                text=result.stem,
                font=("Sans", 11, "bold"),
            ).grid(
                row=0,
                column=0,
                sticky="w",
            )

            ttk.Label(
                card,
                text=result_detail_text(result),
                justify="left",
                wraplength=790,
            ).grid(
                row=1,
                column=0,
                sticky="ew",
                pady=(5, 0),
            )

        footer = ttk.Frame(
            self._window,
            padding=(22, 14, 22, 20),
        )
        footer.grid(
            row=3,
            column=0,
            sticky="ew",
        )
        footer.columnconfigure(0, weight=1)

        footer_text = (
            "Nothing was permanently deleted."
            if totals["failed"] == 0
            else (
                "Completed with warnings. Failed candidates "
                "were not changed."
            )
        )

        ttk.Label(
            footer,
            text=footer_text,
            font=("Sans", 10, "italic"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            footer,
            text="Close",
            command=self._window.destroy,
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

        self._window.protocol(
            "WM_DELETE_WINDOW",
            self._window.destroy,
        )
        self._window.bind(
            "<Escape>",
            lambda _event: self._window.destroy(),
        )

        self._window.grab_set()
        self._window.focus_set()

    def wait(self) -> None:
        self._window.wait_window()


class CullingReviewDialog:
    def __init__(
        self,
        parent: tk.Misc,
        session: Path,
        analysis: CullingAnalysis,
        candidate_executor: CandidateExecutor = (
            execute_culling_candidate
        ),
    ) -> None:
        self.selection: CandidateSelection | None = None
        self._parent = parent
        self._session = session
        self._candidate_executor = candidate_executor
        self._candidates = actionable_candidates(analysis)
        self._variables: list[tk.BooleanVar] = []

        self._window = tk.Toplevel(parent)
        self._window.title("Culling Candidate Review")
        self._window.geometry("900x650")
        self._window.minsize(720, 500)
        self._window.transient(parent)

        self._window.columnconfigure(0, weight=1)
        self._window.rowconfigure(1, weight=1)

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
            text="Culling Candidate Review",
            font=("Sans", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            header,
            text=(
                "Select the candidates to place in Safe "
                "Quarantine. Nothing will be permanently deleted."
            ),
            justify="left",
            wraplength=840,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

        ttk.Label(
            header,
            text=f"Session: {session}",
            font=("Sans", 10, "italic"),
            justify="left",
            wraplength=840,
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(10, 0),
        )

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
        content.rowconfigure(0, weight=1)

        canvas = tk.Canvas(
            content,
            highlightthickness=0,
        )
        canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            content,
            orient="vertical",
            command=canvas.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        canvas.configure(
            yscrollcommand=scrollbar.set,
        )

        self._candidate_frame = ttk.Frame(
            canvas,
            padding=(8, 8),
        )
        self._canvas_window = canvas.create_window(
            (0, 0),
            window=self._candidate_frame,
            anchor="nw",
        )

        self._candidate_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(
                scrollregion=canvas.bbox("all"),
            ),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                self._canvas_window,
                width=event.width,
            ),
        )

        self._build_candidate_rows()

        footer = ttk.Frame(
            self._window,
            padding=(22, 14, 22, 20),
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
            command=self._select_all,
        ).grid(
            row=0,
            column=0,
            padx=(0, 8),
        )

        ttk.Button(
            footer,
            text="Select None",
            command=self._select_none,
        ).grid(
            row=0,
            column=1,
        )

        self._counter = ttk.Label(
            footer,
            anchor="e",
        )
        self._counter.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=16,
        )

        ttk.Button(
            footer,
            text="Close",
            command=self._close,
        ).grid(
            row=0,
            column=3,
            padx=(0, 8),
        )

        self._continue_button = ttk.Button(
            footer,
            text="Continue",
            command=self._continue,
        )
        self._continue_button.grid(
            row=0,
            column=4,
        )

        self._update_counter()

        self._window.protocol(
            "WM_DELETE_WINDOW",
            self._close,
        )
        self._window.bind(
            "<Escape>",
            lambda _event: self._close(),
        )

        self._window.grab_set()
        self._window.focus_set()

    def _build_candidate_rows(self) -> None:
        if not self._candidates:
            ttk.Label(
                self._candidate_frame,
                text=(
                    "No actionable culling candidates were "
                    "found in this import session."
                ),
                justify="left",
            ).grid(
                row=0,
                column=0,
                sticky="w",
                padx=10,
                pady=18,
            )
            return

        self._candidate_frame.columnconfigure(
            0,
            weight=1,
        )

        for row, candidate in enumerate(
            self._candidates
        ):
            variable = tk.BooleanVar(value=True)
            self._variables.append(variable)

            card = ttk.Frame(
                self._candidate_frame,
                padding=(12, 10),
                relief="solid",
                borderwidth=1,
            )
            card.grid(
                row=row,
                column=0,
                sticky="ew",
                pady=(0, 8),
            )
            card.columnconfigure(1, weight=1)

            check = ttk.Checkbutton(
                card,
                variable=variable,
                command=self._update_counter,
            )
            check.grid(
                row=0,
                column=0,
                rowspan=3,
                sticky="n",
                padx=(0, 8),
            )

            ttk.Label(
                card,
                text=candidate_title(candidate),
                font=("Sans", 11, "bold"),
            ).grid(
                row=0,
                column=1,
                sticky="w",
            )

            ttk.Label(
                card,
                text=candidate_details(candidate),
                justify="left",
            ).grid(
                row=1,
                column=1,
                sticky="w",
                pady=(3, 0),
            )

            if candidate.raw_path is not None:
                ttk.Label(
                    card,
                    text=str(candidate.raw_path),
                    font=("Sans", 9, "italic"),
                    justify="left",
                    wraplength=760,
                ).grid(
                    row=2,
                    column=1,
                    sticky="ew",
                    pady=(5, 0),
                )

    def _selected_candidates(
        self,
    ) -> tuple[MissingImportedJpeg, ...]:
        return tuple(
            candidate
            for candidate, variable in zip(
                self._candidates,
                self._variables,
                strict=True,
            )
            if variable.get()
        )

    def _select_all(self) -> None:
        for variable in self._variables:
            variable.set(True)

        self._update_counter()

    def _select_none(self) -> None:
        for variable in self._variables:
            variable.set(False)

        self._update_counter()

    def _update_counter(self) -> None:
        selected = len(self._selected_candidates())
        total = len(self._candidates)

        self._counter.configure(
            text=(
                f"Selected: {selected} of {total} "
                "candidates"
            )
        )

        self._continue_button.configure(
            state=(
                "normal"
                if selected > 0
                else "disabled"
            )
        )

    def _continue(self) -> None:
        selected = self._selected_candidates()

        if not selected:
            return

        confirmed = messagebox.askyesno(
            "Confirm Safe Quarantine",
            build_confirmation_message(selected),
            icon="warning",
            parent=self._window,
        )

        if not confirmed:
            return

        self._continue_button.configure(
            state="disabled"
        )
        self._window.update_idletasks()

        try:
            results = execute_selected_candidates(
                self._session,
                selected,
                executor=self._candidate_executor,
            )
        except Exception as exc:
            self._continue_button.configure(
                state="normal"
            )
            messagebox.showerror(
                "Safe Quarantine failed",
                (
                    "Mac Photo Studio could not complete "
                    "Safe Quarantine.\n\n"
                    f"{exc}"
                ),
                parent=self._window,
            )
            return

        self.selection = CandidateSelection(
            candidates=selected,
        )

        self._window.grab_release()
        self._window.withdraw()

        report = CullingResultDialog(
            parent=self._parent,
            session=self._session,
            results=results,
        )
        report.wait()

        self._window.destroy()

    def _close(self) -> None:
        self.selection = None
        self._window.destroy()

    def wait(self) -> CandidateSelection | None:
        self._window.wait_window()
        return self.selection


def show_culling_review(
    parent: tk.Misc,
    session: Path,
    analysis_loader: AnalysisLoader = (
        load_culling_analysis
    ),
    candidate_executor: CandidateExecutor = (
        execute_culling_candidate
    ),
) -> CandidateSelection | None:
    try:
        analysis = analysis_loader(session)
    except (
        OSError,
        ValueError,
        KeyError,
    ) as exc:
        messagebox.showerror(
            "Culling analysis unavailable",
            (
                "Mac Photo Studio could not complete "
                "the culling analysis.\n\n"
                f"{exc}"
            ),
            parent=parent,
        )
        return None

    dialog = CullingReviewDialog(
        parent=parent,
        session=session,
        analysis=analysis,
        candidate_executor=candidate_executor,
    )
    return dialog.wait()
