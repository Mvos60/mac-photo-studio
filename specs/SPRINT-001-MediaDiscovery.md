# Sprint 001 — Media Discovery

## Goal

Mac Photo Studio must understand what is present on one or more memory cards before any import takes place.

This sprint is read-only.

## In scope

- Scan configured media roots.
- Scan an explicit folder path for testing.
- Find DCIM folders.
- Count RAW files.
- Count JPEG files.
- Count other files.
- Estimate total file size.
- Print a readable console report.

## Out of scope

- Copying files.
- Renaming files.
- Pairing RAW and JPEG files.
- Writing metadata.
- Writing to memory cards.
- Deleting or formatting anything.

## Acceptance criteria

- `mac-photo-studio --scan-cards` works without a card inserted.
- `mac-photo-studio --scan-path <folder>` analyzes a chosen folder.
- The scanner is read-only.
- The report clearly shows RAW, JPEG, other files, and size.
- No file on the scanned source is modified.

## Safety rule

The media discovery layer may only read directory and file metadata.

It must not open files for writing.

It must not create files on the card.

It must not delete files.
