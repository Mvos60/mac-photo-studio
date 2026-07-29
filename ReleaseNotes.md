# Release Notes — Mac Photo Studio 0.2.1 RC2

Mac Photo Studio 0.2.1 RC2 extends the verified import and provenance workflow with a native photographer dashboard, safe culling review, quarantine management, photograph verification and readable Photo History.

The stable release remains 0.2.0. RC2 is the second release candidate for 0.2.1.

## Photographer dashboard

The native Tkinter dashboard provides direct access to:

- verified photograph import
- culling analysis and review
- Quarantine Manager
- photograph verification
- Photo History
- settings, logs and application information

The dashboard shows the configured photo archive path and checks whether digiKam and darktable are available.

## Safe culling and quarantine

The 0.2.1 workflow protects the photographer against accidental deletion:

- culling analysis remains read-only
- a surviving RAW must match its recorded identity before it becomes a culling candidate
- confirmed culling moves recoverable evidence into `.mps_quarantine`
- the active manifest and certificate index are updated
- Quarantine Manager can inspect and restore quarantined photographs
- permanent removal requires explicit confirmation

## Photograph verification

The verification dialog reports whether a selected photograph is trusted, changed or not managed by MPS.

An unmanaged photograph is not described as altered or AI-generated. It only means that MPS cannot link the file to a verified MPS import and provenance record.

## Photo History

Photo History provides:

- a photographer-readable journey
- a readable provenance timeline
- raw technical history details when deeper inspection is needed

## Application discovery

digiKam and darktable use the shared application resolver.

RC2 supports:

- configured executables
- applications found on `PATH`
- Flatpak discovery
- update-safe AppImage discovery
- automatic fallback when a configured executable becomes stale

This allows a newer digiKam AppImage to be detected without editing a version-specific path.

## Import and provenance guarantees

A successful managed import retains the established MPS guarantees:

- SHA-256 verified file copies
- import manifest
- provenance certificates and certificate index
- ingest provenance events
- post-import verification
- source-card reconciliation
- cross-library duplicate-import protection
- removable-media trash and system-directory exclusion

Camera source media remains read-only.

## Tested release status

- 558 automated tests passed
- full Python compile passed
- native GUI workflow manually checked on Ubuntu/Linux
- configured photo archive: `/home/mac/Pictures`
- digiKam AppImage discovery passed
- darktable discovery passed
- rsync and exiftool health checks passed
