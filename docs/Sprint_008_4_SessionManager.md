# Sprint 008.4 - Session Manager

The Session Manager gives every import a durable identity.

A session records:

- session ID
- start timestamp
- end timestamp
- status
- camera
- card label
- discovered files
- imported files
- skipped files
- conflicts
- manifest path

This is another provenance foundation layer. A manifest says what happened to
files. A session says which import operation those file events belonged to.
