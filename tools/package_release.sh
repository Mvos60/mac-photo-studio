#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="$(cat VERSION)"
cd ..
zip -r "MacPhotoStudio-${VERSION}.zip" "MacPhotoStudio-${VERSION}" -x "*/__pycache__/*"
