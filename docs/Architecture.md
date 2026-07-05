# Architecture

Mac Photo Studio has no internal photo catalogue database.

- digiKam owns catalogue, tags, ratings, searches, faces.
- darktable owns RAW development.
- Mac Photo Studio owns ingestion, verification, backup, and reports.

## Alpha3 addition

External applications are resolved through:
1. User-configured executable
2. PATH
3. Flatpak ID
4. AppImage search directories
