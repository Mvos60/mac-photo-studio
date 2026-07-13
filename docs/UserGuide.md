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

The wizard asks for year, project and day/session.

The destination layout is:

```text
~/Photos_Master/YEAR/PROJECT/DAY
```

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
