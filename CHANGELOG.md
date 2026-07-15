# Changelog

## Unreleased — 0.2.1

Added:

- Global imported-photo registry built from provenance certificate indexes
- Cross-library SHA-256 duplicate-import detection
- Shared removable-media path exclusion policy
- Read-only provenance-aware culling analyzer
- Culling candidate RAW identity verification
- Photographer-readable culling analysis report
- `--analyze-culling`
- Explicit confirmed culling workflow
- `--confirm-culling`
- Verified orphan RAW quarantine
- Provenance evidence quarantine for confirmed culled RAW/JPG pairs
- Active certificate-index cleanup after confirmed culling
- Active import-manifest cleanup after confirmed culling
- End-to-end culling workflow integration test

Changed:

- Previously imported source files are skipped even when a card is presented again for a different project or session.
- `.Trash*`, `$RECYCLE.BIN` and `System Volume Information` directories are ignored during removable-media scanning and import planning.
- Confirmed photographer culling removes the affected RAW/JPG pair from the active import record while preserving recoverable quarantine evidence.

Verified:

- 462 automated tests passed
- Cross-library card-reuse regression test passed
- Camera-card trash exclusion tests passed
- Real Sony A7 III RAW/JPG culling workflow passed with `MAC02592`

Known development items:

- Interrupted-session Resume / Start new / Cancel workflow
- Year/month/date-description destination layout
- Culling quarantine restore and permanent purge commands

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
