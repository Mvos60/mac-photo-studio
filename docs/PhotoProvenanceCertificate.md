# Extended Photo Provenance — Ingest Certificate

## Purpose

The Provenance Certificate is the verified-ingest evidence artifact produced by
Extended Photo Provenance.

It records evidence connecting one successfully imported photographic file to
its import session and manifest.

## Production Model

The production evidence model is:

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

## Evidence Relationship

The certificate participates in this relationship:

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

The destination SHA-256 hash links the destination file, manifest entry,
certificate, and certificate index entry.

The session ID links certificates created across sequential media batches to
one import session.

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

## Verification

Post-import verification checks the certificate evidence against the import
manifest.

Verification includes:

- certificate count
- certificate file existence
- certificate destination relationship
- certificate session ID
- certificate manifest path
- certificate SHA-256 hash
- index session ID
- index SHA-256 hash

A written certificate is not automatically trusted merely because the JSON file
exists.

Its evidence relationship must verify.

## Extended Photo Provenance

The ingest certificate is the first implemented evidence type in Extended Photo
Provenance.

Future EPP evidence types may include:

- Edit Record
- Derivative Record
- Export Record
- Verification Report
- Digital Signature evidence

These future records will extend the provenance chain.

They do not replace the existing ingest certificate.
