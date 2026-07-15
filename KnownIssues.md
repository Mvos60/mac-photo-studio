# Known Issues

## 0.2.1 development

### Interrupted import session UX

When an interrupted import session exists, answering `n` to:

```text
Resume this import session? [Y/n]
```

currently leaves the saved session unchanged and exits.

Expected workflow:

```text
Resume
Start new import
Cancel
```

Starting a new import should safely replace the stale active-session state and continue with a new session ID.

### Import destination layout

The current destination layout is:

```text
YEAR / PROJECT / DAY_SESSION
```

A calendar-oriented workflow using year, month, date and description is planned.

Trip/project organization must remain supported.

### Culling quarantine purge

Confirmed culling currently quarantines verified orphan RAW files and their provenance evidence.

Permanent purge and restore commands are not yet implemented.

### User interface

The current primary workflow is command-line based.

The GUI remains limited and does not yet expose the complete import, culling, verification and application-handoff workflow.
