# Mac Photo Studio - Sprint 008.7 Verification Pass RC1

This release adds the first verification pass service.

After an import manifest exists, Mac Photo Studio can now check whether the destination files still exist and whether their contents match the recorded SHA-256 checksums.

This strengthens the provenance foundation by adding an independent verification step after copy/import activity.

Expected test result: **61 passed**.
