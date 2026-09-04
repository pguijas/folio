---
title: 'Folio board: the rename and the merge'
status: backlog
priority: high
tags: [plugins, kanban, core]
created: '2026-08-28'
milestone: "0.2"
type: feature
size: XL
source: folio#1
blocked_by: [the-board-takes-the-name-and-absorbs-the-roadmap]
---

One git-backed store named **board**, several views. The kanban plugin
becomes the board plugin, the roadmap plugin folds into it, and every
surface follows: `board:` in docs.yaml, `folio board` on the CLI,
`/docs/board/` in the guide, the `/board` route. Kanban stays as the
name of the column view. The decision and its recorded counterarguments
live on `the-board-takes-the-name-and-absorbs-the-roadmap`.

The scope is real: ~368 "kanban" mentions in folio/, ~807 in tests,
~181 in docs, 7 template components — plus both consuming repos
(folio and the personal board). Pre-beta is the only cheap window;
at 0.7 this breakage costs an order of magnitude more.

**Open sequencing question for the owner:** before or after
`kanban-edits-from-the-browser` Part One lands. Renaming under an
in-flight XL invites conflicts; renaming after means the write path is
born under the old name and swept once. Default leaning: land Part One
first, rename immediately after, both inside the pre-beta window.

## Acceptance criteria
- [ ] The plugin, config key, CLI, docs section, and route all say board; kanban survives only as the column view's name
- [ ] Milestones/phases live in board data with git history; a phase status change is one commit
- [ ] /roadmap renders from the board's registry and keeps its own visibility toggle, independent of the board's
- [ ] `folio roadmap` prints the same registry `folio board check` validates
- [ ] A milestone registry with zero cards is legal and renders /roadmap alone
- [ ] `kanban:` and `roadmap:` in docs.yaml fail with a message naming the migration, not silently
- [ ] Both consuming repos migrated; the personal board runs on the renamed plugin
- [ ] Docs hold the line everywhere: kanban, roadmap, and tree are views OF the board, never boards themselves
- [ ] No orchestration claim anywhere the code does not back

## Trail
- 2026-08-28 @claude: carded from the panel decision, owner-confirmed; sequencing vs the write path recorded as the one open question
- 2026-08-29 @codex (PR #1): retained the useful Folio Plan workflow idea here; deleted the stale 4,433-line implementation and its remote branch so the board is rebuilt on the current plugin model
