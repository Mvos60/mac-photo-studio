from pathlib import Path

from mps.main import main
from mps.services.digikam_darktable_handoff import (
    DigiKamDarktableHandoff,
)
from mps.services.photo_provenance_verification import (
    PhotoProvenanceVerification,
)


def test_cli_digikam_darktable_launches_trusted_photo(
    tmp_path,
    monkeypatch,
    capsys,
):
    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.main.handoff_digikam_photo_to_darktable",
        lambda **kwargs: DigiKamDarktableHandoff(
            photo_path=photo,
            handed_off=True,
            verification=PhotoProvenanceVerification(
                photo_path=photo,
                trusted=True,
            ),
        ),
    )

    result = main(
        [
            "digikam-darktable",
            str(photo),
        ]
    )

    output = capsys.readouterr().out

    assert result == 0
    assert "Status:        LAUNCHED" in output
    assert str(photo) in output


def test_cli_digikam_darktable_blocks_untrusted_photo(
    tmp_path,
    monkeypatch,
    capsys,
):
    photo = tmp_path / "DSC0001.ARW"

    monkeypatch.setattr(
        "mps.main.handoff_digikam_photo_to_darktable",
        lambda **kwargs: DigiKamDarktableHandoff(
            photo_path=photo,
            handed_off=False,
            verification=PhotoProvenanceVerification(
                photo_path=photo,
                trusted=False,
            ),
            errors=("Photo provenance did not verify",),
        ),
    )

    result = main(
        [
            "digikam-darktable",
            str(photo),
        ]
    )

    output = capsys.readouterr().out

    assert result == 1
    assert "Status:        NOT LAUNCHED" in output
    assert "Photo provenance did not verify" in output


def test_cli_digikam_darktable_requires_photo_path():
    try:
        main(["digikam-darktable"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected argparse SystemExit")
