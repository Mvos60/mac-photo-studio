# Import Manifest

Sprint 008.3 introduces the first import manifest layer for Mac Photo Studio.

The manifest is a permanent JSON record of an import session. It is the first building block of the future Photo Provenance Certificate system.

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

Manifests are written to:

```text
<destination-root>/manifest/import_manifest_<session-id>.json
```

This sprint does not yet connect manifests into the full import pipeline. That happens in the next sprint after the manifest writer has proven stable in isolation.
