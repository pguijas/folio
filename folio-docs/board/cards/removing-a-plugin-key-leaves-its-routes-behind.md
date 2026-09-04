---
title: Removing a plugin key leaves its routes behind
status: backlog
tags: [core, plugins]
created: '2026-08-28'
milestone: "0.3"
type: bug
---

Only the kanban plugin cleans its generated routes when its config key disappears (kanban.py:663-678, test-pinned). The roadmap plugin's emit_assets returns early with no cleanup when roadmap: is absent, so a previously built /roadmap page keeps publishing from a warm workspace until a clean build. Found by an adversarial fact-check of the plugin catalog page, 2026-08-28: the docs claimed every route disappears on the next build and had to be scoped down to kanban. The docs should get the strong sentence back only when the behavior is uniform.
