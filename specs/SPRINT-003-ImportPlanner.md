# Sprint 003 — Import Planner

## Goal

Mac Photo Studio must show what an import would do before any file is copied.

This sprint is read-only.

## In scope

- Accept a project name.
- Accept a day/session folder name.
- Accept RAW and JPEG source folders.
- Reuse the pairing engine.
- Calculate file counts.
- Calculate estimated source size.
- Show the proposed destination.
- Print a readable import plan.

## Out of scope

- Copying files.
- Creating destination folders.
- Renaming files.
- Writing metadata.
- Writing to memory cards.
- Deleting or formatting anything.

## Acceptance criteria

- `mac-photo-studio --plan-import <project> <day> <raw-folder> <jpg-folder>` works.
- The plan reports pairs, RAW-only files, and JPEG-only files.
- The plan reports the destination under `Photos_Master/<project>/<day>`.
- No files or folders are created by the planner.
- No source files are modified.
