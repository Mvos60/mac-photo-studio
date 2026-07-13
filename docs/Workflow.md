# Photographer Workflow

```text
Sony A7 III
→ Mac Photo Sudio 
→ digiKam
→ darktable
→ verified exports
```

## Responsibilities

### Mac Photo Studio

- card discovery
- RAW/JPEG pairing
- verified import
- manifests and provenance
- post-import verification
- source-card reconciliation
- workflow handoffs

### digiKam

- catalogue
- albums
- tags
- ratings
- searches
- faces

### darktable

- RAW development
- photographic edits
- exports

## Folder layout

```text
Photos_Master/
└── 2026/
    └── Adriatic/
        ├── 01_Germany/
        ├── 02_Austria/
        ├── 03_Slovenia/
        ├── 04_Croatia/
        ├── 05_Bosnia/
        ├── 06_Montenegro/
        └── 07_Italy/
```

## Provenance workflow

```text
Camera original
    |
    v
INGEST
    |
    v
darktable developed master
    |
    v
EDIT
    |
    v
final JPEG or TIFF
    |
    v
EXPORT
```

Each recorded file is verified against its SHA-256 identity and provenance event chain.

## Typical commands

```bash
mac-photo-studio import
```

```bash
mac-photo-studio digikam-darktable /path/to/photo.ARW
```

```bash
mac-photo-studio darktable-edit   /path/to/photo.ARW   /path/to/photo_master.tif
```

```bash
mac-photo-studio darktable-complete-export   /path/to/photo_master.tif   /path/to/photo_export.jpg
```

```bash
mac-photo-studio photo-history /path/to/photo_export.jpg
```
