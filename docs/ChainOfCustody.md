# Chain of Custody

## Status

The original Chain of Custody implementation was introduced during Sprint 008
as the first provenance prototype.

It used:

- `ProvenanceRecord`
- `chain_of_custody.py`

That prototype is historical.

## Evolution

The Sprint 008 design explicitly anticipated later provenance certificates.

The production provenance architecture now uses Extended Photo Provenance.

It includes:

- verified import evidence
- per-file provenance certificates
- provenance IDs
- certificate IDs
- import session IDs
- SHA-256 evidence
- certificate indexing
- persistent provenance event chains
- event-chain validation
- controlled event recording
- original and derived-file identity resolution
- stable file hashing
- file-backed lineage verification

## Current Rule

New provenance development must extend Extended Photo Provenance.

The historical `ProvenanceRecord` model and `chain_of_custody.py` service must
not be extended with new workflow features.

They remain temporarily during the Mac Photo Studio 0.2 development cycle for
historical test coverage.

## Verified Ingest Evidence

The production ingest evidence flow is:

    Verified Copy
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
        |
        v
    Post-Import Provenance Verification
        |
        v
    Final Import Session Reconciliation

## Extended Lineage

After ingest, a photographic lineage may continue through derived files:

    Original ARW
        |
        v
    EDIT Event
        |
        v
    Master TIFF
        |
        v
    EXPORT Event
        |
        v
    Exported JPEG

Each file has its own SHA-256 identity.

The files remain connected by one provenance ID and by validated hash
continuity between ordered provenance events.

A derived file can become the input identity for a later provenance event.

## Trust Rule

A provenance JSON file is not trusted merely because it exists.

Extended Photo Provenance verifies relationships between:

- the actual file
- the recorded SHA-256 identity
- the provenance identity
- the stored event chain
- event ordering
- hash continuity

A file-backed verification succeeds only when the actual stable file hash
matches its recorded identity and the complete stored lineage validates.

## Public Service Boundary

Production workflow integrations must use:

    mps.services.extended_photo_provenance

The supported service operations are:

- `append_file_provenance_event`
- `verify_provenance_file`

Lower-level provenance services implement persistence, identity resolution,
validation, recording, and compatibility behaviour.

They are internal architecture and should not be composed directly by future
workflow integrations.
