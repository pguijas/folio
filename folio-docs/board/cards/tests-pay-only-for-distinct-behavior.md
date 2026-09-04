---
title: "Tests pay only for distinct behavior"
status: released
priority: high
tags: [testing, ci]
assignee: codex
size: M
source: folio#feat/test-suite-efficiency
type: maintenance
created: 2026-08-29
artifacts:
  - pr: 36
---

The suite has grown broad enough that repeated execution is expensive. Profile
the real cost, remove coverage that repeats an already-pinned behavior, and keep
the smallest set of tests that still protects Folio's public contracts and
failure boundaries.

## Acceptance criteria
- [x] The slowest and most repeated test paths are measured before editing
- [x] Redundant work is removed without dropping a unique public contract or edge case
- [x] The relevant tests and the full suite pass after the change
- [x] The measured before/after cost and the suite-sizing rule are documented
- [x] The main CI runs the suite once on Python 3.12 instead of a version matrix

## Trail
- 2026-08-29 @codex (feat/test-suite-efficiency): card created; profiling started in an isolated worktree
- 2026-08-29 @codex (working-tree): kept all 9 filter-language tests while batching their shared boundary from 29 Node launches to 9; 1228 passed and 1 skipped, with the observed suite time moving from 174.26s to 53.73s; ruff and board checks green
- 2026-08-29 @local (57c9abe00): implementation rebased onto release/0.3.0; 1236 tests, ruff, and board checks pass
- 2026-08-29 @local (fdc87a59c): main CI now runs one Python 3.12 job; 30 release-metadata tests and ruff pass
- 2026-08-29 @local (f57373aa3): test-running workflows use Node 24; 39 affected tests, ruff, and board checks pass
- 2026-08-29 @local (c73fa853d): PR #36 merged into release/0.3.0; single Python 3.12 CI passed
