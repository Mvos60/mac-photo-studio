# Mac Photo Studio Roadmap

## 0.2.0 — Verified Import Foundation

**Status:** Released

Delivered:

- Camera-card discovery
- RAW/JPEG pairing
- SHA-256 verified imports
- Import manifests
- Photo Provenance Certificates
- Provenance certificate index
- Hash-linked event chains
- Interrupted-session recovery
- Post-import verification
- Source-card reconciliation
- digiKam and darktable workflow integration

## 0.2.1 — Safe Culling and Duplicate Protection

**Status:** Release Candidate 1

Delivered:

- Cross-library duplicate-import prevention
- Shared imported-photo registry
- Camera-card trash and system-directory filtering
- Read-only culling analysis
- Verified orphan RAW detection
- RAW and provenance quarantine
- JPG-only provenance cleanup
- Active manifest cleanup
- Active certificate-index cleanup
- Explicit photographer confirmation
- Transaction rollback protection
- Real-world Sony A7 III field testing

Remaining before final release:

- Fix interrupted-session Resume / Start new / Cancel workflow
- Add year/month/date-description import layout
- Prevent path separators in session descriptions
- Return a clear error for nonexistent import-session paths
- Complete release documentation review
- Run final full-suite and real-world import tests

## 0.2.2 — Quarantine Management

Planned:

- List quarantined photographs
- Restore a quarantined photograph
- Restore provenance evidence
- Permanently purge confirmed quarantine items
- Quarantine audit report
- Safer batch operations

## 0.3.0 — Photographer Workflow Polish

Planned:

- Clearer top-level workflow menu
- Better first-import guidance
- More photographer-friendly status messages
- Improved digiKam and darktable handoff visibility
- Installation and upgrade improvements
- Expanded GUI workflow

## 1.0 — Stable Photographer Release

Target:

- Stable verified import workflow
- Mature provenance lifecycle
- Safe culling and recovery
- Clear user documentation
- Reliable installation and upgrades
- Extended real-world travel and field testing

## Guiding Principles

Mac Photo Studio should:

- protect original photographs
- keep camera media read-only
- verify important file operations
- require explicit confirmation for destructive actions
- preserve recoverability before permanent deletion
- explain actions in photographer-friendly language
- work alongside digiKam and darktable rather than replace them
