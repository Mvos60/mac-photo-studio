# Sprint 008.6 - Resume Engine

The Resume Engine inspects an incomplete import session and its manifest to decide what can safely continue.

It does not copy, delete, overwrite, or rename photographs.

The first version provides:

- incomplete session detection
- resume plan model
- verified destination detection
- missing destination detection
- conflict detection
- resume blocking when conflicts are found

This prepares Mac Photo Studio for safe interrupted-import recovery in a later sprint.
