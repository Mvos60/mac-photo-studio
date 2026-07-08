# Mac Photo Studio Architecture v2

## Purpose

Mac Photo Studio is designed as a safe, predictable photo import workflow.

The core rule is:

**Observe first. Decide second. Act last.**

No part of the system should copy, move, delete, or rename files unless that is its explicit responsibility.

## Pipeline

Card / Folder
→ Scanner
→ CardScanResult
→ Import Planner
→ Import Decision
→ Safe Copy Engine
→ Verification

## Scanner

The scanner observes source media.

Responsibilities:

- Find cards or scan a given path
- Count RAW, JPEG, HEIF, and video files
- Count RAW/JPEG pairs
- Count RAW and JPEG orphans
- Estimate source size
- Produce JSON-safe scan data

The scanner is always read-only.

## Import Planner

The Import Planner turns facts into a plan.

Responsibilities:

- Choose destination path
- Estimate import workload
- Report warnings
- Decide which files should be included
- Preserve RAW/JPEG pairing rules

The planner is always read-only.

## Import Decision

An Import Decision answers:

- Where will the files go?
- How many files will be copied?
- Are there warnings?
- Are RAW/JPEG pairs preserved?
- Are orphan files included?
- Should checksums be verified?
- Should originals remain untouched?

## Safe Copy Engine

The Safe Copy Engine performs the actual file copy.

Responsibilities:

- Copy selected files
- Refuse unsafe overwrites
- Verify copied files
- Report success or failure

It follows the Import Decision. It does not decide what to copy.

## Design Rules

1. No hidden file changes.
2. Scanner is read-only.
3. Planner is read-only.
4. Copy engine follows instructions.
5. Tests protect every layer.

## Sprint 006 Direction

- 006.0 Scanner cleanup checkpoint
- 006.1 Import plan warnings
- 006.2 Architecture v2 blueprint
- 006.3 Introduce ImportDecision model
- 006.4 Build ImportDecision from planner
- 006.5 Display ImportDecision in CLI

## Long-Term Goal

Mac Photo Studio should feel calm, predictable, and trustworthy.

Before any file is copied, the user should clearly see:

- what was found
- what will happen
- where files will go
- what warnings exist
- whether verification will be used
