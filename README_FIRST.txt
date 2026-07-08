Mac Photo Studio
Sprint 008.7 - Verification Pass RC1

Run from the extracted sprint package directory:

  ./apply.sh
  ./verify.sh

This package applies to:

  ~/Downloads/mac-photo-studio

Expected verification result:

  61 passed

After verification succeeds:

  cd ~/Downloads/mac-photo-studio
  git add .
  git commit -F COMMIT_MESSAGE.txt
  git push
  git status
  git branch -vv
