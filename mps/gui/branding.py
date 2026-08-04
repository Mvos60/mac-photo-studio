from __future__ import annotations

import tkinter as tk

from mps.resources import ResourceNotFoundError, asset_path


CAMERA_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
CAMERA_DISPLAY_SIZES = (96, 144)
CAMERA_MASTER_ASSET = "branding/mps-camera-512.png"
CAMERA_DISPLAY_BRIGHTNESS = 0.77
CAMERA_DISPLAY_CONTRAST = 1.06


def camera_asset_path(size: int) -> str:
    if size == 512:
        relative = CAMERA_MASTER_ASSET
    elif size in CAMERA_DISPLAY_SIZES:
        relative = f"branding/display/mps-camera-dark-{size}.png"
    elif size in CAMERA_ICON_SIZES:
        relative = f"branding/icons/{size}x{size}/mac-photo-studio.png"
    else:
        raise ValueError(f"Unsupported camera asset size: {size}")
    return str(asset_path(relative))


def load_camera_image(master: tk.Misc, size: int) -> tk.PhotoImage:
    return tk.PhotoImage(master=master, file=camera_asset_path(size))


def apply_window_icon(window: tk.Misc) -> tuple[tk.PhotoImage, ...]:
    """Apply the camera icon and retain all Tk image references."""

    images = [load_camera_image(window, 512)]
    for size in CAMERA_ICON_SIZES[:-1]:
        try:
            images.append(load_camera_image(window, size))
        except (ResourceNotFoundError, tk.TclError):
            continue

    retained = tuple(images)
    window.iconphoto(True, *retained)
    window._mps_icon_images = retained
    return retained
