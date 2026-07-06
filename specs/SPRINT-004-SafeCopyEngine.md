# Sprint 004 — Safe Copy Engine

## Goal

Mac Photo Studio must safely copy one file and verify the result.

This is the first sprint that writes to a destination, so scope is intentionally small.

## In scope

- Copy one file from source to destination.
- Create the destination parent directory if needed.
- Refuse to overwrite an existing destination file.
- Verify copied file size.
- Verify copied file SHA-256 checksum.
- Return a structured result.

## Out of scope

- Copying folders.
- Batch import.
- Renaming files.
- Deleting source files.
- Moving files.
- Writing to memory cards.
- Overwriting existing files.
- Progress bars.

## Acceptance criteria

- `copy_one_file()` copies a file to a destination.
- Parent destination folders are created.
- Source and destination file sizes match.
- Source and destination SHA-256 checksums match.
- Existing destination files are not overwritten.
- Missing source files fail safely.
- Unit tests cover success and failure paths.

## Safety rule

The copy engine must never modify the source file.

The copy engine must never overwrite an existing destination file.
