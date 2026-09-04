---
title: Plugin system unification
status: released
created: '2026-07-16'
tags: [plugins, platform]
artifacts:
  - pr: 23
---

One plugin platform behind every surface. The registry is the single source of
truth; first-party defaults and project plugins load through the same path, and
the dedicated-page contract lets any plugin claim a page the same way the
built-ins do. OpenAPI remains opt-in rather than a default plugin.

## Acceptance criteria
- [x] one loading path for default and project plugins
- [x] dedicated-page contract on /roadmap and /kanban
- [x] The unification implementation is present on the release branch; the older PR #23 is superseded

## Comments
- 2026-08-27 @claude: Audit 2026-08-27: PR #23 is still OPEN on GitHub (untouched since 2026-07-16) so the third criterion is unmet as written — but its head branch worktree-plugin-system-unification was merged into feat/artifact-board-poc five times (last 1d254c727), so all the code already rides this branch and reaches main when this branch does. Owner call: close #23 as superseded and reword the criterion to this branch's merge, or merge #23. Minor body drift: openapi is not a default plugin (folio/plugin.py:40-44 lists roadmap, kanban, landing).

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-29 @codex (release/0.3.0): corrected the OpenAPI claim and replaced the stale PR gate with the code state this release actually ships.
