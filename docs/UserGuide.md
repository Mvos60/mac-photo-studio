# User Guide — 0.2.0

## Install

```bash
bash install.sh
source ~/.bashrc
```

## Version

```bash
mac-photo-studio --version
```

## Health check

```bash
mac-photo-studio --health
```

## Configure digiKam AppImage

Edit:

```text
~/.config/mac-photo-studio/settings.yaml
```

Example:

```yaml
applications:
  digikam:
    executable: ~/Applications/digiKam-9.1.0-Qt6-x86-64.appimage
```

## Scan connected photo cards

```bash
mac-photo-studio --scan-cards
```

This command is read-only.

## Interactive import

```bash
mac-photo-studio import
```

The GUI offers a native Resume / Start new / Cancel choice when an active
session exists. A new GUI import uses the calendar-first selector and the
configured photo library root:

```text
PHOTOS_ROOT/YEAR/MM/DD[_DESCRIPTION]/PROJECT
```

Example:

```text
/home/mac/Pictures/2026/08/02_Ljubljana/Adriatic
```

RAW and JPG cards in one session use exactly the same destination. Resume
reuses the persisted structured destination and does not reopen the selector.
Start new requires exact `START NEW` confirmation and protects the previous
state until the first new batch is copied and verified. Cancel leaves state
unchanged. Import discovery and progress currently run in a terminal; Sprint
015.14 will provide the fully native MPS import window.

## Explicit two-folder import

```bash
mac-photo-studio --import   2026   Adriatic   03_Slovenia   /media/raw-card   /media/jpeg-card
```

## Verify an imported or derived photo

```bash
mac-photo-studio verify-photo   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001.ARW
```

A successful result reports `Status: TRUSTED`.

## Show provenance history

```bash
mac-photo-studio photo-history   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001.ARW
```

## Hand a trusted photo to darktable

```bash
mac-photo-studio digikam-darktable   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001.ARW
```

The photo is verified before darktable is launched.

## Record a darktable edit

```bash
mac-photo-studio darktable-edit   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001.ARW   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001_master.tif
```

## Record and verify a darktable export

```bash
mac-photo-studio darktable-complete-export   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001_master.tif   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001_export.jpg
```

## Inspect the final history

```bash
mac-photo-studio photo-history   ~/Photos_Master/2026/Adriatic/03_Slovenia/DSC0001_export.jpg
```

Expected event sequence:

```text
INGEST
EDIT
EXPORT
```

## Source-card safety

Mac Photo Studio does not automatically delete, rename, move or format files on source media.
