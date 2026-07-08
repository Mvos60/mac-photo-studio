# Chain of Custody

Mac Photo Studio uses provenance records to begin an auditable history for each imported file.

A provenance record links a file to:

- the import session that created it,
- its original source path,
- its archive destination,
- its SHA-256 checksum,
- and optional camera/source-media context.

This is intentionally simple in Sprint 008.8. Later sprints can extend it into full provenance certificates.
