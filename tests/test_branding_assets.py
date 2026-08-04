from pathlib import Path

from PIL import Image, ImageStat

from mps.gui import branding
from mps.gui.branding import CAMERA_ICON_SIZES, camera_asset_path


def test_camera_master_and_variants_are_rgba_pngs():
    for size in CAMERA_ICON_SIZES:
        path = Path(camera_asset_path(size))
        assert path.is_file()
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (size, size)
            assert image.mode == "RGBA"
            assert image.getextrema()[3][0] < 255


def test_master_is_the_canonical_512_asset():
    assert Path(camera_asset_path(512)).name == "mps-camera-512.png"


def _visible_luminance(path: Path) -> float:
    with Image.open(path).convert("RGBA") as image:
        return ImageStat.Stat(
            image.convert("L"), mask=image.getchannel("A")
        ).mean[0]


def test_dark_display_assets_are_transparent_and_mildly_darker():
    master_luminance = _visible_luminance(Path(camera_asset_path(512)))
    for size in (96, 144):
        path = Path(camera_asset_path(size))
        assert path.name == f"mps-camera-dark-{size}.png"
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (size, size)
            assert image.mode == "RGBA"
            assert image.getchannel("A").getextrema() == (0, 255)
            visible_extrema = ImageStat.Stat(
                image.convert("L"), mask=image.getchannel("A")
            ).extrema[0]
            assert visible_extrema[1] > 100
        display_luminance = _visible_luminance(path)
        assert 0 < display_luminance < master_luminance

    assert branding.CAMERA_DISPLAY_BRIGHTNESS == 0.77
    assert branding.CAMERA_DISPLAY_CONTRAST == 1.06


def test_pyproject_packages_all_branding_pngs():
    project = Path("pyproject.toml").read_text(encoding="utf-8")
    assert '"assets/branding/*.png"' in project
    assert '"assets/branding/display/*.png"' in project
    assert '"assets/branding/icons/*/*.png"' in project


def test_master_hash_is_the_approved_source_hash():
    import hashlib

    digest = hashlib.sha256(Path(camera_asset_path(512)).read_bytes()).hexdigest()
    assert digest == "09f9ed094f54cd2949079833a9b14f6db8a3cf61460b2c3faa1706d5634328c5"


def test_branding_has_no_light_backdrop_constant():
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (Path("mps/gui/app.py"), Path("mps/gui/about.py"))
    )
    assert "#f2efe8" not in production
    assert "CAMERA_BACKDROP" not in production


def test_window_icon_keeps_all_photoimage_references(monkeypatch):
    images = []

    class PhotoImage:
        def __init__(self, *, master, file):
            self.master = master
            self.file = file
            images.append(self)

    class Window:
        def iconphoto(self, default, *received):
            self.icon_call = (default, received)

    monkeypatch.setattr(branding.tk, "PhotoImage", PhotoImage)
    monkeypatch.setattr(
        branding,
        "camera_asset_path",
        lambda size: f"camera-{size}.png",
    )
    window = Window()
    retained = branding.apply_window_icon(window)
    assert window.icon_call == (True, retained)
    assert window._mps_icon_images == retained
    assert len(retained) == len(CAMERA_ICON_SIZES)
    assert retained == tuple(images)
