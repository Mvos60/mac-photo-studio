# Sprint 002 — Pairing Engine

## Goal

Mac Photo Studio must recognize which RAW and JPEG files belong together before any import takes place.

This sprint is read-only.

## In scope

- Analyze one RAW folder and one JPEG folder.
- Match files by original camera base name.
- Report paired files.
- Report RAW-only files.
- Report JPEG-only files.
- Provide a command-line dry run.

## Out of scope

- Copying files.
- Renaming files.
- Reading EXIF metadata.
- Writing metadata.
- Writing to memory cards.
- Deleting or formatting anything.

## Acceptance criteria

- `mac-photo-studio --pair-paths <raw-folder> <jpg-folder>` works.
- RAW/JPEG files with the same stem are reported as pairs.
- RAW-only files are reported separately.
- JPEG-only files are reported separately.
- No files are modified.
