---
title: Browser edits for a git-backed board
status: ideas
priority: high
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-26
type: feature
size: L
source: folio#33
---

Let a board opened in the browser change its cardfiles without replacing git
as the database. Local development may commit through `folio serve`; a remote
board needs an explicit backend, personal credentials, conflict detection, and
the same validated operations as the CLI. With no write endpoint, the board
must remain static and read-only.

PR #33 explored this before the current plugin and board boundaries settled.
After its base moved, GitHub exposed an unusable 301-file review surface. The
implementation is discarded and its branch is deleted; any future attempt
starts from the current operation API and threat model rather than reviving
that diff.

## Acceptance criteria
- [ ] Browser and CLI edits call one validated operation layer
- [ ] A local edit produces one narrow conventional commit and converges after the watcher echo
- [ ] A board with no backend remains byte-identical and read-only
- [ ] Remote writes define authentication, authorization, stale-write refusal, and private-read behavior before implementation
- [ ] The feature is rebuilt and reviewed from the current main branch

## Trail
- 2026-08-26 @claude: carded from the board-write architecture discussion.
- 2026-08-29 @codex (PR #33): stale implementation and head branch deleted; the product idea survives here for a clean rebuild from current main.
