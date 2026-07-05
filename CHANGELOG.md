# Changelog

## 0.1.0-alpha3

Added:
- Application resolver for digiKam/darktable
- Custom executable paths in settings
- AppImage detection support
- Card scanner skeleton
- `--scan-cards`
- `--show-config`
- Settings merge/upgrade during install

Changed:
- Health check now checks configured paths, PATH executables, Flatpak IDs, and common AppImage locations.
- Installer preserves user settings while adding new default keys.

## 0.1.0-alpha2
- Fixed launcher/PYTHONPATH issue.

## 0.1.0-alpha1
- Initial foundation release.
