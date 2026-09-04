---
title: Make source parsing honest and retire dead paths
status: released
priority: high
tags: [core, parser, cleanup]
assignee: codex
created: '2026-08-29'
---

Fix documented Python exclusion and source-root behavior, fail on invalid Python instead of publishing empty API pages, and remove code paths proven unreachable after earlier refactors.

## Trail
- 2026-08-29 @local (575e2968a): fixed syntax failures, documented excludes and src roots; removed unreachable parser, CLI, plugin, builder, and test-only paths; full suite and static build pass
