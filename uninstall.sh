#!/bin/bash
set -euo pipefail

PKG_NAME="mac-photo-studio"

echo "Uninstalling Mac Photo Studio..."

rm -rf "$HOME/.local/share/$PKG_NAME"
rm -f "$HOME/.local/bin/mac-photo-studio"
rm -f "$HOME/.local/share/applications/MacPhotoStudio.desktop"
for size in 16 24 32 48 64 128 256 512; do
  rm -f "$HOME/.local/share/icons/hicolor/${size}x${size}/apps/mac-photo-studio.png"
done

echo
echo "Application removed."
echo "User config preserved at: $HOME/.config/$PKG_NAME"
echo "Logs preserved at:        $HOME/.local/state/$PKG_NAME"
echo "Photos preserved at:      $HOME/Photos_Master"
