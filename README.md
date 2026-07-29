# Mac Photo Studio

**Stable release:** 0.2.0<br>
**Release candidate:** 0.2.1 RC2<br>
**Target platform:** Ubuntu/Linux

Mac Photo Studio is a verified photographic import and provenance workflow for photographers using digiKam and darktable.

It does not replace digiKam's catalogue or darktable's RAW-development workflow.

## Photographer workflow

```text
Camera media
→ Mac Photo Studio verified import
→ digiKam catalogue and culling
→ Mac Photo Studio provenance-aware culling analysis
→ trusted handoff to darktable
→ recorded edit
→ verified export
```

## Responsibilities

| Application | Responsibility |
|---|---|
| Mac Photo Studio | Verified import, integrity checks, provenance, culling safety and workflow handoffs |
| digiKam | Catalogue, albums, tags, ratings, searches, faces and visual culling |
| darktable | RAW development and exports |

## Main capabilities

- RAW and JPEG camera-card discovery
- RAW/JPEG pairing
- Year/project/day destination layout
- SHA-256 verified copying
- Cross-library duplicate-import prevention
- Removable-media trash and system-directory exclusion
- Import manifests and logs
- Photo Provenance Certificates
- Provenance certificate index
- Provenance event history
- Hash-linked photographic lineage
- Interrupted-session resume protection
- Post-import verification
- Source-card reconciliation
- digiKam workflow handoff
- Trusted-photo handoff to darktable
- Recorded darktable edits and exports
- Final exported-photo verification
- Read-only provenance-aware culling analysis
- Explicit confirmed culling
- Verified orphan RAW quarantine
- Active manifest and provenance cleanup after confirmed culling
- Native photographer dashboard
- Import-session and photograph pickers
- Native culling review
- Quarantine Manager with restore and explicit permanent removal
- Native photograph verification
- Readable Photo History
- Update-safe digiKam and darktable discovery

## Installation

From a checked-out release or source directory:

```bash
bash install.sh
source ~/.bashrc
```

Verify the installation:

```bash
mac-photo-studio --version
mac-photo-studio --health
```

## Interactive import

```bash
mac-photo-studio import
```

Mac Photo Studio 0.2.0 uses:

```text
Photos_Master/
└── YEAR/
    └── PROJECT/
        └── DAY_SESSION/
```

A calendar-oriented year/month/date-description layout is planned for 0.2.1 development.

## Read-only card scan

```bash
mac-photo-studio --scan-cards
```

## Analyze culling

After deliberately deleting rejected JPG photographs in digiKam or darktable:

```bash
mac-photo-studio --analyze-culling \
  "/path/to/import-session"
```

The analysis is read-only.

A missing imported JPG is correlated with its matching RAW by original camera filename stem. The surviving RAW must still match its recorded SHA-256 identity before it is reported as a verified culling candidate.

## Confirm a culling candidate

```bash
mac-photo-studio --confirm-culling \
  "/path/to/import-session" \
  PHOTO_STEM
```

Example:

```bash
mac-photo-studio --confirm-culling \
  "$HOME/Photos_Master/2026/Adriatic/03_Slovenia" \
  DSC01234
```

Exact confirmation with `CULL` is required.

The verified orphan RAW and its provenance evidence are moved to `.mps_quarantine`. The RAW/JPG pair is removed from the active import manifest and active certificate index.

No immediate permanent RAW deletion is performed.

## Verify a managed photograph

```bash
mac-photo-studio verify-photo /path/to/photo
```

## Show provenance history

```bash
mac-photo-studio photo-history /path/to/photo
```

## Hand a trusted photograph to darktable

```bash
mac-photo-studio digikam-darktable /path/to/photo
```

## Record a darktable edit

```bash
mac-photo-studio darktable-edit \
  /path/to/source.ARW \
  /path/to/master.tif
```

## Record and verify a darktable export

```bash
mac-photo-studio darktable-complete-export \
  /path/to/master.tif \
  /path/to/export.jpg
```

## Safety policy

Mac Photo Studio does not automatically:

- delete camera-card source photographs
- rename camera-card source photographs
- move camera-card source photographs
- format memory cards
- permanently delete culled RAW files

Camera source media remains read-only.

Confirmed culling requires explicit photographer action and quarantines verified orphan RAW files before any future permanent disposal.

## Release status

### 0.2.0 Final

- 421 automated tests passed
- verified RAW/JPEG import
- provenance certificate and event-chain workflow
- trusted digiKam/darktable workflow integration
- final photograph verification

### 0.2.1 RC2

Current release-candidate capabilities include:

- cross-library duplicate-import prevention
- camera-card trash/system directory filtering
- provenance-aware culling analysis
- verified orphan RAW quarantine
- native culling review and Quarantine Manager
- quarantine restore and explicit permanent removal
- managed-photograph verification and readable Photo History
- centralized photo archive configuration
- update-safe digiKam and darktable discovery
- polished native photographer dashboard

Current release-candidate test suite:

```text
558 passed
```
