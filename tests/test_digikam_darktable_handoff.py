from pathlib import Path

from mps.config import Settings
from mps.services.digikam_darktable_handoff import (
    handoff_digikam_photo_to_darktable,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
)
from mps.services.workflow_application_launcher import (
    WorkflowApplicationLaunch,
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        {
            "paths": {
                "photos_root": str(
                    tmp_path / "Photos_Master"
                ),
            },
        }
    )


def test_handoff_verifies_photo_before_launch(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "DSC0001.ARW"
    called = []

    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "verify_managed_photo",
        lambda **kwargs: called.append(
            ("verify", kwargs)
        )
        or PhotoProvenanceVerification(
            photo_path=photo,
            trusted=True,
        ),
    )
    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "launch_darktable",
        lambda **kwargs: called.append(
            ("launch", kwargs)
        )
        or WorkflowApplicationLaunch(
            application="darktable",
            launched=True,
            target=photo,
        ),
    )

    settings = _settings(tmp_path)

    result = handoff_digikam_photo_to_darktable(
        settings=settings,
        photo_path=photo,
    )

    assert result.handed_off is True
    assert [item[0] for item in called] == [
        "verify",
        "launch",
    ]
    assert called[0][1]["settings"] is settings
    assert called[0][1]["photo_path"] == photo
    assert called[1][1]["settings"] is settings
    assert called[1][1]["photo_path"] == photo


def test_handoff_blocks_untrusted_photo(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "DSC0001.ARW"
    launched = []

    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "verify_managed_photo",
        lambda **kwargs: PhotoProvenanceVerification(
            photo_path=photo,
            trusted=False,
            errors=["Photo provenance did not verify"],
        ),
    )
    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "launch_darktable",
        lambda **kwargs: launched.append(kwargs),
    )

    result = handoff_digikam_photo_to_darktable(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.handed_off is False
    assert result.launch is None
    assert result.errors == (
        "Photo provenance did not verify",
    )
    assert launched == []


def test_handoff_reports_darktable_launch_failure(
    tmp_path,
    monkeypatch,
):
    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "verify_managed_photo",
        lambda **kwargs: PhotoProvenanceVerification(
            photo_path=photo,
            trusted=True,
        ),
    )
    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "launch_darktable",
        lambda **kwargs: WorkflowApplicationLaunch(
            application="darktable",
            launched=False,
            target=photo,
            errors=("darktable application was not found",),
        ),
    )

    result = handoff_digikam_photo_to_darktable(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.handed_off is False
    assert result.launch is not None
    assert result.errors == (
        "darktable application was not found",
    )


def test_handoff_expands_photo_path(
    tmp_path,
    monkeypatch,
):
    photo = Path("~/Photos_Master/DSC0001.ARW")
    expected = photo.expanduser()

    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "verify_managed_photo",
        lambda **kwargs: PhotoProvenanceVerification(
            photo_path=expected,
            trusted=True,
        ),
    )
    monkeypatch.setattr(
        "mps.services.digikam_darktable_handoff."
        "launch_darktable",
        lambda **kwargs: WorkflowApplicationLaunch(
            application="darktable",
            launched=True,
            target=expected,
        ),
    )

    result = handoff_digikam_photo_to_darktable(
        settings=_settings(tmp_path),
        photo_path=photo,
    )

    assert result.photo_path == expected
    assert result.handed_off is True
