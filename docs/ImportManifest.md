# Import Manifest

The import manifest is the permanent JSON record produced by the verified
import pipeline for one import session. It is part of the Photo Provenance
Certificate and resume-validation evidence.

Each manifest stores:

- session ID
- creation timestamp
- project name
- day/session name
- Mac Photo Studio version
- per-file source path
- per-file destination path
- per-file SHA-256 checksum
- action and status
- file count and total bytes

Manifests are written inside the exact import root selected for the session.
The manifest session ID must match the active session during resume and final
reconciliation. Manifest entries are verified together with destination files
and provenance certificates before a batch is considered trusted.
