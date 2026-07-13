# Extended Photo Provenance

## Purpose

Extended Photo Provenance records and verifies evidence about the history of a
photographic file without modifying the photographic file itself.

The original ingest certificate remains the root evidence artifact.

Persistent provenance events extend that evidence through later photographic
workflow operations.

## Ingest Certificate

The production ingest evidence model is:

    ProvenanceCertificate

Each certificate records:

- certificate ID
- provenance ID
- import session ID
- source path
- destination path
- SHA-256 hash
- camera model when detectable
- import manifest path
- certificate creation time

The certificate is written as JSON beneath the import root provenance
directory.

The original RAW or JPEG file is not modified.

## Ingest Evidence Relationship

The ingest certificate participates in this relationship:

    Source File
        |
        v
    Verified Destination File
        |
        v
    Import Manifest Entry
        |
        v
    Provenance Certificate
        |
        v
    Certificate Index
        |
        v
    INGEST Provenance Event

The destination SHA-256 hash links the destination file, manifest entry,
certificate, certificate index entry, and ingest event.

The provenance ID identifies the photographic lineage.

## Certificate Index

Every ingest certificate is represented in the provenance certificate index.

The index records:

- certificate ID
- provenance ID
- session ID
- destination path
- certificate path
- SHA-256 hash
- camera model
- creation time

Sequential import batches append to the same index.

The certificate index remains the root identity source for imported files.

## Provenance Event Chain

A provenance lineage is extended with ordered provenance events.

Implemented event types include:

- INGEST
- EDIT
- DERIVE
- EXPORT
- VERIFY

Each event records:

- event ID
- provenance ID
- session ID
- event type
- creation time
- input SHA-256
- output SHA-256 when applicable
- application context when supplied
- description when supplied
- metadata

File-backed events also record the derived output path in event metadata.

## Derived File Identity

A derived output file becomes part of the same photographic lineage.

For example:

    Sony ARW
        |
        v
    EDIT
        |
        v
    Master TIFF
        |
        v
    EXPORT
        |
        v
    JPEG

The ARW, TIFF, and JPEG each have distinct SHA-256 identities.

They share one provenance ID.

The output SHA-256 of one event must match the input SHA-256 of the following
event.

This hash continuity forms the persistent lineage relationship.

## Stable File Evidence

File-backed provenance events do not trust a caller-supplied output hash.

Mac Photo Studio hashes the actual output file.

The file is inspected and hashed twice.

The event is not recorded when:

- the file does not exist
- the path is not a file
- the file changes during hashing
- the two SHA-256 calculations disagree

Only a stable output identity may enter the provenance chain.

## Verification

Extended Photo Provenance can verify an original or derived file.

Verification performs this evidence path:

    Actual File
        |
        v
    Stable SHA-256
        |
        v
    Provenance Identity Resolution
        |
        v
    Stored Provenance Event Chain
        |
        v
    Hash Continuity Validation
        |
        v
    Recorded Identity Comparison

A file is trusted only when:

- its actual stable SHA-256 matches its recorded identity
- its provenance identity resolves
- its stored provenance chain is not empty
- the complete event chain validates

A file that still opens or appears visually correct is not automatically
trusted when its recorded identity no longer matches.

## Public Service Boundary

Production workflow integrations use:

    mps.services.extended_photo_provenance

Supported operations:

- `append_file_provenance_event`
- `verify_provenance_file`

The lower-level certificate, index, event writer, recorder, resolver, validator,
and chain persistence services are internal Extended Photo Provenance
architecture.

## Compatibility Boundary

The historical Sprint 008 `ProvenanceRecord` and `chain_of_custody.py`
implementation remains temporarily for compatibility and historical test
coverage.

New workflow integrations must not extend that prototype.

Extended Photo Provenance is the production provenance architecture for Mac
Photo Studio.
