History rewrite and remote update — documentation

Date: 2025-10-29

## Summary

This repository had its history rewritten locally to set the author/committer name and email to the user's private values. The remote repository location changed and `origin` has been updated to the new URL.

## Backups made before destructive operations

Check these paths in the workspace root (they were created during the session):

- `app.py.bak` — local backup of `app.py` prior to overwrites
- Full workspace artifacts (look for timestamped backups, e.g. `agent_wcag_backup_YYYY-MM-DD_HH-mm-ss`)

## Repository HEAD after operations

- Current HEAD: 33b7cb1abe2925d8205e01d83ad4e92e6032d339
- Commit metadata: 33b7cb1abe2925d8205e01d83ad4e92e6032d339 2025-10-28 20:32:28 +0100 Joanna Kraciuk <joanna.kraciuktest@gmail.com> Add MIT LICENSE (Joanna Kraciuk)

## Exact commands executed (representative)

These are the Git commands run during the session (not necessarily all, but the key ones):

1. Backup workspace (Windows copy / robocopy used interactively)

   - Example: robocopy . "..\agent_wcag_backup_2025-10-28_07-45-48" /MIR

2. Fetch remote and save remote file (one-off exploratory commands)

   - git fetch origin
   - git show origin/main:app.py > app.py.from_remote

3. Restore safely via git

   - git reset --hard origin/main
   - git reset --hard 6e28975 # (user requested rollback to specific commit)

4. Rewrite author/committer metadata (history rewrite)

   - git filter-branch --env-filter "
     if [ \"$GIT_COMMITTER_EMAIL\" = \"old@example.com\" ]; then
     export GIT_COMMITTER_NAME='Joanna Kraciuk'
     export GIT_COMMITTER_EMAIL='joanna.kraciuktest@gmail.com'
     export GIT_AUTHOR_NAME='Joanna Kraciuk'
     export GIT_AUTHOR_EMAIL='joanna.kraciuktest@gmail.com'
     fi
     " -- --all
   - rm -rf .git/refs/original/
   - git reflog expire --expire=now --all
   - git gc --prune=now --aggressive

5. Push rewritten history to remote (force)

   - git push --force-with-lease origin main
   - git push --force-with-lease origin --tags

6. Update `origin` remote to new location and push
   - git remote set-url origin https://github.com/JoannaKraciuk/AuditAI.git
   - git remote -v
   - git push origin main

## Notes and recommendations

- The rewritten history was forced; collaborators cloning the old repo URL should reclone or reset their local clones to avoid divergent histories.
- There are many generated report files in the workspace (docx/pdf/xlsx). These were intentionally not pushed to remote. Consider adding them to `.gitignore` if not desired in the repo.
- If you want a safer, repeatable history-rewrite in future, prefer `git filter-repo` (faster and more robust) over `git filter-branch`.

If you want, I can:

- Search for timestamped backup folders and list their full paths inside the repo.
- Mark this documentation file as committed and push it to `origin`.
- Restore a specific helper function (like `format_recommendation`) from backups into `app.py` and run tests locally.

-- end of document
