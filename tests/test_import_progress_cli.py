from types import SimpleNamespace

from mps.config import Settings
from mps.main import run_interactive_import_command
from mps.services.import_progress_output import print_import_progress


def test_interactive_import_uses_visible_progress_reporter(
    monkeypatch,
    tmp_path,
) -> None:
    settings = Settings(
        {
            "paths": {
                "photos_root": str(tmp_path / "Pictures"),
            },
            "gui": {
                "launch_digikam_after_import": False,
            },
        }
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "mps.main.load_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "mps.main.USER_STATE_DIR",
        tmp_path / "state",
    )
    monkeypatch.setattr(
        "mps.main.prompt_year",
        lambda default: 2026,
    )
    monkeypatch.setattr(
        "mps.main.prompt_project",
        lambda: "Field Test",
    )
    monkeypatch.setattr(
        "mps.main.prompt_day",
        lambda: "01-08-2026",
    )
    monkeypatch.setattr(
        "mps.main.media_import_destination",
        lambda settings, *, year, project, day: (
            tmp_path / "Pictures" / str(year) / project / day
        ),
    )
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: "",
    )

    def fake_run_import_media_session(settings, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            batches_processed=1,
            copied=1,
            failed=0,
            completed=True,
            success=True,
        )

    monkeypatch.setattr(
        "mps.main.run_import_media_session",
        fake_run_import_media_session,
    )

    assert run_interactive_import_command() == 0
    assert captured["progress_callback"] is print_import_progress
