# Legacy Compatibility Boundaries

## Purpose

Mac Photo Studio currently contains two generations of import workflow code.

The distinction is intentional during the 0.2 development cycle.

## Primary Import Workflow

The supported interactive photographer workflow is:

    mac-photo-studio import

This workflow is based on the flexible media-session architecture.

Primary modules include:

- `mps.models.import_media_session`
- `mps.services.import_media_discovery`
- `mps.services.import_media_selector`
- `mps.services.import_media_batch_planner`
- `mps.services.import_media_batch_processor`
- `mps.services.import_media_wizard_runner`
- `mps.services.import_media_session_store`
- `mps.services.import_media_resume_validator`
- `mps.services.import_media_session_reconciler`

This workflow supports:

- one card reader with sequential card swaps
- multiple simultaneous card readers
- RAW-only media
- JPEG-only media
- mixed RAW and JPEG media
- persistent interrupted-session recovery
- Extended Photo Provenance evidence
- final import-session reconciliation

New interactive import development must target this architecture.

## Compatibility CLI Workflow

The following explicit CLI commands still use the original two-folder import architecture:

    mac-photo-studio --plan-import YEAR PROJECT DAY RAW_FOLDER JPEG_FOLDER
    mac-photo-studio --dry-run-import YEAR PROJECT DAY RAW_FOLDER JPEG_FOLDER
    mac-photo-studio --import YEAR PROJECT DAY RAW_FOLDER JPEG_FOLDER

These commands depend on modules including:

- `mps.models.import_session_request`
- `mps.services.import_session_builder`
- `mps.services.import_planner`

They remain supported as compatibility and diagnostic interfaces.

New photographer-facing workflow features must not be added to this path unless
required for compatibility or correctness.

## Historical Workflow Modules

The following modules are historical implementations and are not used by a
current production entry point:

- `mps.services.import_wizard`
- `mps.services.import_wizard_runner`
- `mps.services.import_request_planner`

The following session subsystem also predates the flexible media-session
architecture:

- `mps.models.import_session`
- `mps.services.session_manager`
- `mps.services.resume_engine`

These modules are retained temporarily during the 0.2 development cycle so
their behaviour remains documented by the existing test suite.

They must not be used for new sequential import development.

## Removal Policy

Legacy or historical modules must not be removed merely because a newer
implementation exists.

Removal requires:

1. confirmation that no supported CLI or application entry point imports them;
2. a migration or compatibility decision for any public behaviour;
3. a full regression suite;
4. an explicit cleanup sprint or release decision.

## Architectural Rule

When the term `import session` is used for current development, it refers to
`ImportMediaSession` unless legacy compatibility is explicitly being discussed.
