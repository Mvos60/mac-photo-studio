from pathlib import Path


def test_desktop_launcher_uses_camera_icon_name_and_valid_core_fields():
    desktop = Path("desktop/MacPhotoStudio.desktop").read_text(encoding="utf-8")
    assert desktop.startswith("[Desktop Entry]\n")
    assert "\nType=Application\n" in desktop
    assert "\nExec=" in desktop
    assert "\nIcon=mac-photo-studio\n" in desktop
    assert "Icon=camera-photo" not in desktop


def test_installer_installs_every_hicolor_camera_icon():
    installer = Path("install.sh").read_text(encoding="utf-8")
    assert "16 24 32 48 64 128 256" in installer
    assert '"$ICON_ROOT/512x512/apps"' in installer
    assert "mps/assets/branding/mps-camera-512.png" in installer
    assert "mac-photo-studio.png" in installer
