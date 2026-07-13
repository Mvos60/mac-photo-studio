# Changelog

## 0.2.0

Added:

- Flexible sequential media-import sessions
- RAW, JPEG, HEIF and video discovery
- RAW/JPEG pairing and orphan reporting
- Year/project/day destination layout
- SHA-256 verified copy operations
- Import manifests and logs
- Photo Provenance Certificates and certificate index
- Ingest, edit, derivative and export provenance events
- Hash-linked provenance event chains
- Derived-file identity resolution
- File-backed provenance verification
- Photographer-readable provenance history
- Safe interrupted-session resume
- Post-import verification
- Source-card reconciliation
- digiKam workflow adapter and verified import handoff
- Trusted-photo handoff from digiKam to darktable
- darktable edit and export recording
- Final exported-photo verification
- End-to-end photographer workflow test

Changed:

- Mac Photo Studio now performs real verified imports.
- The primary destination layout is `Photos_Master/YEAR/PROJECT/DAY`.
- digiKam remains the catalogue owner.
- darktable remains the RAW-development owner.
- Source media remains read-only.
- Release status changed from alpha foundation to version 0.2.0.

Verified:

- 421 automated tests passed
- Real-laptop smoke test passed
- RAW/JPEG import, provenance verification, edit recording and export verification passed

## 0.1.0-alpha3

Added:

- Application resolver for digiKam and darktable
- Custom executable paths in settings
- AppImage detection support
- Card scanner skeleton
- `--scan-cards`
- `--show-config`
- Settings merge during installation

## 0.1.0-alpha2

- Fixed launcher and `PYTHONPATH` handling.

## 0.1.0-alpha1

- Initial foundation release.
