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

Completed in the current development line:

- Native Resume / Start new / Cancel workflow
- Calendar-first destination layout
- Protected replacement of active session state
- Safe structured resume validation
- Quarantine restore and explicit permanent removal
- Documentation synchronization

Historical RC1 planning items are retained in the changelog for release context.

## 0.2.2 — Quarantine Management

Status: Completed in the current development line.

Delivered:

- List quarantined photographs
- Restore quarantined photographs and provenance evidence
- Permanently purge confirmed quarantine items

Planned:

- Quarantine audit report
- Safer batch operations

## 015.14 — Native GUI Import Workflow

Planned:

- Replace terminal import progress with a fully native MPS import window
- Preserve native Resume / Start new / Cancel and calendar-first selection semantics
- Keep CLI import compatibility during the transition

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
