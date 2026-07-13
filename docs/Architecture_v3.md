# Mac Photo Studio Architecture v3

## Status

Architecture v3 describes the primary Mac Photo Studio 0.2 development
architecture.

The authoritative photographer-facing import workflow is:

    mac-photo-studio import

Historical and compatibility boundaries are documented separately in
`LegacyCompatibility.md`.

## Purpose

Mac Photo Studio is a trust-oriented photographic ingest and workflow system.

It does not replace digiKam or darktable.

Responsibilities are deliberately separated:

- digiKam owns catalogue management, tags, ratings, searches, and faces.
- darktable owns RAW development.
- Mac Photo Studio owns media discovery, verified ingest, import-session
  integrity, recovery, Extended Photo Provenance, and workflow evidence.

The architectural principle remains:

**Observe first. Decide second. Act last. Verify before trust.**

## Primary Production Flow

The current interactive import architecture is:

    Photo Media
        |
        v
    Media Discovery
        |
        v
    New Media Detection
        |
        v
    Import Media Session
        |
        v
    Batch Planning
        |
        v
    Verified Copy Engine
        |
        v
    Import Manifest
        |
        v
    Extended Photo Provenance
        |
        v
    Post-Import Verification
        |
        v
    Media Registration
        |
        v
    Additional Media / Card Swap
        |
        v
    Final Session Reconciliation
        |
        v
    Trusted Photo Archive

Each layer has a distinct responsibility.

## Media Discovery

Primary modules:

- `mps.services.card_scanner`
- `mps.services.import_media_discovery`
- `mps.services.import_media_selector`
- `mps.models.card`
- `mps.models.import_media_selection`

Media discovery is read-only.

It observes configured removable-media roots and reports photographic media.

The architecture supports:

- one card reader
- multiple card readers
- RAW-only media
- JPEG-only media
- RAW and JPEG on the same card
- RAW and JPEG on separate cards
- sequential card swaps
- simultaneous media sources

Discovery does not copy, rename, delete, or modify source media.

## Media Identity and New Media Detection

Primary modules:

- `mps.services.media_source_identity`
- `mps.services.import_media_new_source_detector`
- `mps.models.import_media_session`

A media source is identified by a content-derived fingerprint.

The fingerprint allows Mac Photo Studio to distinguish between:

- the same processed card still mounted
- a different card mounted at the same reader path
- several independent media sources

Mount paths are not treated as permanent card identities.

This is essential for a one-reader sequential workflow where different cards
may appear at the same filesystem path.

## Import Media Session

Primary modules:

- `mps.models.import_media_session`
- `mps.services.import_media_session`
- `mps.services.import_media_session_store`
- `mps.services.import_media_resume_validator`
- `mps.services.import_media_wizard_runner`

`ImportMediaSession` is the current import-session model.

It tracks durable workflow facts including:

- session identity
- processed media fingerprints
- exact processed source-file paths

A session may contain one or more media batches.

For example:

    RAW card
        |
        v
    Batch 1
        |
        v
    card swap
        |
        v
    JPEG card
        |
        v
    Batch 2

Both batches remain part of one import session and share one session ID.

## Persistent Session Recovery

The active sequential import session may be stored under the Mac Photo Studio
user state directory.

The active-session state records:

- session ID
- processed media fingerprints
- exact processed source-file paths

After an interruption, Mac Photo Studio may resume only when:

1. a saved session identity exists;
2. the existing import manifest belongs to the same session;
3. imported destination files still verify;
4. Extended Photo Provenance evidence still verifies.

A failed validation blocks resume.

The system must never silently resume a previous import under a new session
identity.

## Batch Planning

Primary modules:

- `mps.models.import_media_batch_plan`
- `mps.services.import_media_batch_planner`
- `mps.models.import_decision`

The batch planner operates on media physically available during the current
batch.

It is read-only.

Responsibilities include:

- calculate the canonical destination
- locate configured RAW and JPEG file types
- create explicit copy operations
- estimate batch size
- detect destination filename collisions
- produce an `ImportDecision`

The canonical destination layout is:

    Photos_Master
        /
        YEAR
        /
        PROJECT
        /
        DAY_OR_SESSION

Example:

    ~/Photos_Master/2026/Adriatic/03_Slovenia

Planning never creates the destination directory.

## Batch Processing

Primary module:

- `mps.services.import_media_batch_processor`

The batch processor coordinates one currently mounted media batch.

Its responsibilities are:

1. create the media batch plan;
2. reject planner warnings that block safe processing;
3. identify the camera when metadata permits;
4. invoke the verified import engine;
5. verify the resulting import root;
6. register media as processed only after successful verification;
7. record the exact source files that were processed.

The critical safety rule is:

**Media is not registered as processed until copy and verification succeed.**

## Verified Copy Engine

Primary modules:

- `mps.services.import_engine`
- `mps.services.safe_copy`
- `mps.models.import_result`
- `mps.models.import_progress`

The import engine executes explicit copy operations from an `ImportDecision`.

Responsibilities include:

- create the destination when real import begins
- perform safe file copies
- verify file checksums
- report file progress
- maintain the import log
- update the import manifest
- create provenance certificates
- update the provenance certificate index

The engine does not discover cards and does not decide which media should be
processed.

## Import Manifest

Primary modules:

- `mps.models.import_manifest`
- `mps.services.manifest_writer`

The import manifest is the authoritative record of files accepted into one
import session.

Each file entry records:

- source path
- destination path
- SHA-256 hash
- action
- verification status
- byte count

The manifest also records:

- session ID
- creation time
- project
- day or session
- Mac Photo Studio version

Sequential media batches append to one persistent manifest.

A manifest belonging to another session ID must never be silently reused.

## Extended Photo Provenance

Extended Photo Provenance is a first-class Mac Photo Studio subsystem.

The current implemented phase establishes provenance at verified ingest.

Primary modules include:

- `mps.models.provenance_certificate`
- `mps.models.provenance_certificate_index`
- `mps.services.provenance_certificate`
- `mps.services.provenance_writer`
- `mps.services.provenance_index_builder`
- `mps.services.provenance_index_writer`
- `mps.services.provenance_paths`
- `mps.services.provenance_index_paths`

For every successfully verified imported file, Mac Photo Studio records
provenance evidence linking:

- source path
- destination path
- SHA-256 hash
- camera model when available
- import manifest
- import session ID
- certificate identity
- provenance identity
- creation time

A certificate index links the import root to all provenance certificates.

Sequential batches append to the same provenance index.

### Extended Photo Provenance Direction

The current implementation covers verified ingest.

Future phases may extend the same provenance system to include:

- darktable edit records
- XMP relationships
- master derivative creation
- export records
- published-image relationships
- digital signatures
- human-readable verification reports

These are extensions of one provenance architecture, not separate authenticity
systems.

## Post-Import Verification

Primary modules:

- `mps.services.verification_pass`
- `mps.services.post_import_verifier`
- `mps.models.post_import_verification`

Post-import verification distrusts the copy result until the written evidence
has been checked.

It verifies:

- expected destination files exist
- destination SHA-256 hashes match the manifest
- manifest entries are complete
- certificate count matches the manifest
- certificate files exist
- certificate session IDs match the manifest
- certificate manifest paths match
- certificate hashes match manifest hashes
- certificate-index session IDs match
- certificate-index hashes match

A successful copy is not by itself sufficient for media release decisions.

## Media Registration

After post-import verification succeeds, the processed media is registered in
the active `ImportMediaSession`.

Registration records:

- the media fingerprint
- the exact source files processed

This ordering prevents a failed media batch from being remembered as complete.

The session can therefore reject duplicate rescans while still recognising a
new card mounted at the same reader path.

## Card Swap Behaviour

The interactive workflow is designed around real photographic use.

After a verified batch, Mac Photo Studio reports that it has finished reading
the current media.

The user is instructed to eject or unmount media before physical removal.

When another source is requested:

- already processed mounted media defaults to another search;
- an empty reader may finish the import session;
- new media is processed as another batch in the same session.

This behaviour supports both camper-style one-reader workflows and studio
systems with several readers.

## Final Session Reconciliation

Primary modules:

- `mps.services.import_media_session_reconciler`
- `mps.models.import_media_session_reconciliation`
- `mps.services.source_card_reconciler`

At the end of the interactive workflow, the complete import session is
reconciled.

The final reconciliation verifies:

- processed source inventory matches the manifest
- no processed source is missing from the manifest
- no unexpected manifest source exists
- destination hashes still verify
- provenance evidence still verifies
- the manifest session ID matches the active import session
- post-import verification remains safe

The final successful status is:

    IMPORT SESSION RECONCILED

`ImportMediaWizardResult.success` is true only when the complete session
reconciles successfully.

## Trust Boundary

Mac Photo Studio distinguishes between operational success and trusted success.

Operational success means a function completed.

Trusted success requires verified evidence.

The primary trust sequence is:

    Copy
        |
        v
    Checksum Verification
        |
        v
    Manifest Evidence
        |
        v
    Extended Photo Provenance Evidence
        |
        v
    Post-Import Verification
        |
        v
    Session Reconciliation
        |
        v
    Trusted Import

No earlier stage may claim the guarantees of a later stage.

## Source Media Policy

Source media is treated as read-only by the import architecture.

The current design does not automatically:

- delete source files
- rename source files
- move source files
- format cards

Mac Photo Studio may determine that it has finished reading media, but physical
removal remains an operating-system eject or unmount action.

## External Application Boundary

Mac Photo Studio deliberately has no internal photographic catalogue database.

digiKam remains the catalogue owner.

darktable remains the RAW development owner.

Mac Photo Studio may integrate with these applications, but it must not
duplicate their primary responsibilities.

This separation is a deliberate architectural choice.

## Compatibility Boundary

The original two-folder import planner remains available through explicit
compatibility CLI commands.

See:

    docs/LegacyCompatibility.md

New interactive photographer-facing development targets the flexible
`ImportMediaSession` architecture.

## Core Design Rules

1. Source media is observed before action.
2. Discovery and planning are read-only.
3. Copy operations are explicit.
4. Media identity is not inferred from mount path alone.
5. A failed batch is never registered as processed.
6. Checksums are evidence, not decoration.
7. Session identity must persist across sequential batches and safe resume.
8. Provenance belongs to the complete import workflow.
9. Final trust requires reconciliation.
10. digiKam and darktable keep their established responsibilities.
11. Tests protect architectural boundaries.
12. Compatibility code must not silently become the primary workflow again.

## Current Architectural Pillars

Mac Photo Studio 0.2 is organised around five pillars:

### Media Ingest

Discover, identify, plan, and safely process photographic media.

### Verified Import

Copy files through explicit decisions and verify resulting data integrity.

### Import Session Reliability

Support sequential media, interruption recovery, persistent identity, and final
session reconciliation.

### Extended Photo Provenance

Record verifiable evidence describing how photographic files entered and move
through the Mac Photo Studio workflow.

### Workflow Integration

Work alongside digiKam and darktable without replacing their catalogue and RAW
development responsibilities.

## Architectural Goal

Mac Photo Studio should feel calm, predictable, and trustworthy.

The system should not merely say:

    Import completed.

It should be able to demonstrate:

    These files were discovered.
    These files were selected.
    These files were copied.
    These hashes were verified.
    This manifest records them.
    This provenance evidence belongs to them.
    This session identity links the batches.
    The complete import reconciles.

The goal is not simply successful file transfer.

The goal is a trusted photographic workflow supported by evidence.
