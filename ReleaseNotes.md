# Release Notes — Mac Photo Studio 0.1.0-alpha3

Alpha3 handles the digiKam AppImage situation we found on Mac's laptop.

## Recommended digiKam AppImage setup

Place the AppImage here:

```text
~/Applications/digiKam-9.1.0-Qt6-x86-64.appimage
```

Then edit:

```text
~/.config/mac-photo-studio/settings.yaml
```

Set:

```yaml
applications:
  digikam:
    executable: ~/Applications/digiKam-9.1.0-Qt6-x86-64.appimage
```

Then run:

```bash
mac-photo-studio --health
```

## Card scanner

Run:

```bash
mac-photo-studio --scan-cards
```

This only scans and reports. It does not copy, import, delete, or modify anything.
