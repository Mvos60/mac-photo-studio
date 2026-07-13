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

The production import architecture now uses:

- `ProvenanceCertificate`
- per-file certificate JSON
- provenance IDs
- certificate IDs
- import session IDs
- SHA-256 evidence
- import manifest relationships
- certificate indexing
- post-import provenance verification

This implemented production system is now part of:

**Extended Photo Provenance**

## Current Rule

New provenance development must extend Extended Photo Provenance.

The historical `ProvenanceRecord` model and `chain_of_custody.py` service must
not be extended with new workflow features.

They remain temporarily during the Mac Photo Studio 0.2 development cycle for
historical test coverage.

## Current Verified-Ingest Evidence

The production evidence flow is:

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
    Post-Import Provenance Verification
        |
        v
    Final Import Session Reconciliation

This is the first implemented phase of Extended Photo Provenance.
