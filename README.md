# Mac Photo Studio

**Version:** 0.1.0-alpha3  
**Release type:** Environment-aware foundation + card scanner skeleton  
**Target platform:** Ubuntu/Linux

This alpha does **not** import photos yet. It improves system detection and introduces the first dry-run card scanner.

## Install

```bash
unzip MacPhotoStudio-0.1.0-alpha3.zip
cd MacPhotoStudio-0.1.0-alpha3
bash install.sh
source ~/.bashrc
```

## Run

```bash
mac-photo-studio --health
mac-photo-studio --scan-cards
mac-photo-studio --gui
```

## New in alpha3

- digiKam AppImage/custom path support
- Better external application detection
- User settings upgrade/merge
- Card scanner skeleton
- Dry-run removable-media scan
- Environment report
