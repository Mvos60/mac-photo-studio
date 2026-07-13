# Release Notes — Mac Photo Studio 0.2.0

Mac Photo Studio 0.2.0 is the first complete verified photographer-workflow release.

## Workflow

```text
Camera
→ verified Mac Photo Studio import
→ digiKam
→ trusted handoff to darktable
→ recorded edit
→ recorded and verified export
```

## Import guarantees

A successful import includes:

- SHA-256 verified file copies
- import manifest
- provenance certificates
- provenance certificate index
- ingest provenance events
- post-import verification
- source-card reconciliation

The program reports `SAFE TO RELEASE` only when imported files and certificates verify.

## Provenance

Mac Photo Studio records a file-linked photographic lineage:

- `INGEST`
- `EDIT`
- `DERIVATIVE`
- `EXPORT`

Each derived file retains the same provenance identity while also receiving its own SHA-256 identity.

Modified or unknown files are not reported as trusted.

## digiKam

digiKam remains responsible for catalogue management, albums, tags, ratings, searches and face recognition.

Catalogue-only actions do not create photographic provenance events.

## darktable

darktable remains responsible for RAW development and exports.

Mac Photo Sudio can:

- verify a managed photograph before launching darktable
- record the developed output
- record the exported output
- verify the final exported photograph

## Tested release status

- 421 automated tests passed
- real-laptop smoke test passed
- verified RAW/JPEG import passed
- trusted ingest/edit/export history passed
- final JPEG  provenance verification passed
