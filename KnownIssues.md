# Known Issues

## Current import workflow

The GUI now provides native Resume / Start new / Cancel session choices and a
calendar-first destination selector. The actual import discovery and progress
still run in a terminal; this is the planned focus of Sprint 015.14.

An active session is never silently deleted. Corrupt or unsafe state is blocked
and remains available for diagnosis. Resume validates the saved structured
destination, manifest, session ID, provenance evidence and import root before
continuing.

## Compatibility paths

The legacy CLI destination layout remains available for explicit compatibility
commands. It is not used by the GUI Start new flow.
