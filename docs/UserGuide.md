# User Guide — 0.1.0-alpha3

## Install

```bash
bash install.sh
source ~/.bashrc
```

## Health

```bash
mac-photo-studio --health
```

## Configure digiKam AppImage

Edit:

```text
~/.config/mac-photo-studio/settings.yaml
```

Set:

```yaml
applications:
  digikam:
    executable: ~/Applications/digiKam-9.1.0-Qt6-x86-64.appimage
```

## Read-only card scan

```bash
mac-photo-studio --scan-cards
```
