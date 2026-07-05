from __future__ import annotations

import tkinter as tk

from mps.version import get_version


def run_gui() -> None:
    root = tk.Tk()
    root.title("Mac Photo Studio")
    root.geometry("560x300")

    title = tk.Label(root, text="📷 Mac Photo Studio", font=("Sans", 18, "bold"))
    title.pack(pady=(25, 10))

    version = tk.Label(root, text=f"Environment-Aware Foundation {get_version()}")
    version.pack(pady=5)

    msg = (
        "Alpha 3 is installed correctly.\n\n"
        "New: AppImage/custom application detection and card scan skeleton.\n"
        "Use the terminal command for now:\n"
        "mac-photo-studio --scan-cards"
    )
    body = tk.Label(root, text=msg, justify="center")
    body.pack(pady=18)

    btn = tk.Button(root, text="Close", command=root.destroy, width=16)
    btn.pack(pady=10)

    root.mainloop()
