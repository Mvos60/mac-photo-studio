#!/bin/bash
set -euo pipefail

APP_NAME="Mac Photo Studio"
PKG_NAME="mac-photo-studio"
VERSION="$(cat VERSION)"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/share/$PKG_NAME"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/$PKG_NAME"
STATE_DIR="$HOME/.local/state/$PKG_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"
PHOTOS_ROOT="$HOME/Photos_Master"

echo "Installing $APP_NAME $VERSION..."
echo

REPORT=()

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    REPORT+=("OK    $1")
    return 0
  else
    REPORT+=("WARN  $1 not found")
    return 1
  fi
}

check_cmd python3 >/dev/null || {
  echo "ERROR: python3 is required."
  exit 1
}

python3 - <<'PY' >/dev/null 2>&1 && REPORT+=("OK    tkinter") || REPORT+=("WARN  tkinter not available; install python3-tk for GUI")
import tkinter
PY

check_cmd rsync >/dev/null || true
check_cmd exiftool >/dev/null || true

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$CONFIG_DIR" "$STATE_DIR/logs" "$DESKTOP_DIR"
mkdir -p "$PHOTOS_ROOT"/{01_ORIGINALS,02_WORKING,03_EXPORTS,04_DELIVERED,05_BACKUP_REPORTS,99_ADMIN}
mkdir -p "$HOME/Applications"

rsync -a --delete \
  --exclude ".git" \
  --exclude "__pycache__" \
  "$SRC_DIR/" "$INSTALL_DIR/"

SETTINGS="$CONFIG_DIR/settings.yaml"
DEFAULTS="$INSTALL_DIR/config/default_settings.yaml"

if [ ! -f "$SETTINGS" ]; then
  cp "$DEFAULTS" "$SETTINGS"
  REPORT+=("OK    user settings created")
else
  python3 "$INSTALL_DIR/tools/merge_settings.py" "$DEFAULTS" "$SETTINGS"
  REPORT+=("OK    user settings upgraded/preserved")
fi

cat > "$BIN_DIR/mac-photo-studio" <<EOF
#!/bin/bash
export PYTHONPATH="$INSTALL_DIR:\${PYTHONPATH:-}"
exec python3 -m mps.main "\$@"
EOF
chmod +x "$BIN_DIR/mac-photo-studio"
REPORT+=("OK    command launcher installed")

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    REPORT+=("OK    ~/.local/bin added to ~/.bashrc")
  else
    REPORT+=("WARN  ~/.local/bin in ~/.bashrc but not current shell PATH")
  fi
else
  REPORT+=("OK    ~/.local/bin already in PATH")
fi

sed "s|@INSTALL_DIR@|$INSTALL_DIR|g" \
  "$INSTALL_DIR/desktop/MacPhotoStudio.desktop" > "$DESKTOP_DIR/MacPhotoStudio.desktop"
chmod +x "$DESKTOP_DIR/MacPhotoStudio.desktop"
REPORT+=("OK    desktop launcher installed")

if "$BIN_DIR/mac-photo-studio" --version >/tmp/mps_install_test.out 2>/tmp/mps_install_test.err; then
  REPORT+=("OK    launcher smoke test")
else
  REPORT+=("FAIL  launcher smoke test")
  cat /tmp/mps_install_test.err
  exit 2
fi

echo
echo "Installation Report"
echo "==================="
printf '%s\n' "${REPORT[@]}"

echo
echo "Install complete."
echo
echo "Run:"
echo "  source ~/.bashrc"
echo "  mac-photo-studio --health"
echo "  mac-photo-studio --scan-cards"
