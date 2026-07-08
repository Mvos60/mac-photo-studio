# Photo Provenance Certificate

Sprint 009.0 introduces the first certificate model for Mac Photo Studio.

A certificate records the evidence needed to connect an imported file to its provenance chain:

- certificate ID
- provenance ID
- import session ID
- source path
- destination path
- SHA-256 checksum
- verification status
- optional camera, source media, and MPS version

The certificate does not modify the original RAW file. It is written as a sidecar JSON artifact.
