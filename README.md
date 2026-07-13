# Mac Photo Studio

**Version:** 0.2.0  
**Target platform:** Ubuntu/Linux

Mac Photo Studio performs verified photographic imports while working alongside digiKam and darktable.

It does not replace digiKam's catalogue or darktable's RAW-development workflow.

## Photographer workflow

```text
Camera media
→ Mac Photo Studio verified import
→ digiKam catalogue
→ trusted handoff to darktable
→ recorded edit
→ verified export
```

## Responsibilities

| Application | Responsibility |
|---|---|
| Mac Photo Studio | Verified import, integrity checks, provenance and workflow handoffs |
| digiKam | Catalogue, albums, tags, ratings, searches and faces |
| darktable | RAW development and exports |

## Main capabilities

- RAW and JPEG card discovery
- RAW/JPEG pairing
- Year/project/day destination layout
- SHA-256 verified copying
- Import manifests and logs
- Photo provenance certificates
- Provenance event history
- Interrupted-session resume protection
- Post-import verification
- Source-card reconciliation
- digiKam handoff
- Trusted-photo handoff to darktable
- Recorded darktable edits and exports
- Final exported-photo verification

## Installation

```bash
bash install.sh
source ~/.bashrc
```

## Health check

```bash
mac-photo-studio --health
```

## Read-only card scan

```bash
mac-photo-studio --scan-cards
```

## Interactive import

```bash
mac-photo-studio import
```

Imported photographs use this layout:

```text
Photos_Master/
└── YEAR/
    └── PROJECT/
        └── DAY_SESSION/
```

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

- delete source photographs
- rename source photographs
- move source photographs
- format memory cards

Source media remains read-only.

## Release status

- Version 0.2.0
- 421 automated tests passing
- Real-world laptop smoke test passed
- Verified ingest, edit and export workflow passed
