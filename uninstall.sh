#!/bin/bash
set -euo pipefail

PKG_NAME="mac-photo-studio"

echo "Uninstalling Mac Photo Studio..."

rm -rf "$HOME/.local/share/$PKG_NAME"
rm -f "$HOME/.local/bin/mac-photo-studio"
rm -f "$HOME/.local/share/applications/MacPhotoStudio.desktop"

echo
echo "Application removed."
echo "User config preserved at: $HOME/.config/$PKG_NAME"
echo "Logs preserved at:        $HOME/.local/state/$PKG_NAME"
echo "Photos preserved at:      $HOME/Photos_Master"
