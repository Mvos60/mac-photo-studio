# Release Builder

The Release Builder creates Mac Photo Studio sprint packages from the local repository.

It exists so release ZIP files can be produced reproducibly from the actual project state.

## Basic idea

A release spec lists:

- sprint number
- codename
- release candidate
- expected test count
- commit message
- payload files

The builder copies those payload files into a release directory, adds standard release documentation and scripts, then creates a ZIP archive.

## Example

```bash
python3 tools/release_builder.py release_spec.json --repo-root . --output-root dist
```

The result is a ZIP package such as:

```text
Sprint_008_5_ReleaseBuilder_RC1.zip
```

## Why this matters

Mac Photo Studio treats release packaging as part of the engineering process.

A release should be reproducible, inspectable, and safe to apply.
