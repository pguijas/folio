---
title: Experiment tracking integration plugin
status: ideas
milestone: "0.3"
tags: [plugins, integrations]
created: 2026-08-29
type: feature
size: M
parent: ecosystem-technical-plan
source: folio#20
---

Publish experiment runs, metrics, and charts as normal Folio documents through
an opt-in integration plugin. W&B is a useful first adapter, but the extension
boundary should describe experiment tracking rather than bake one vendor into
the core.

PR #20 targeted an older feature gate and plugin API, bundled unrelated font
changes, and accumulated a full wizard before the smallest read-only slice was
proven. Its implementation and branch are deleted; a future version starts
from the current plugin contract.

## Acceptance criteria
- [ ] A read-only adapter emits run summaries through the current plugin document pipeline
- [ ] Credentials remain build-time inputs and never enter generated assets
- [ ] Tests use deterministic fixtures and require no network access
- [ ] Tables and charts inherit normal routes, search, mirrors, and theme behavior
- [ ] W&B-specific code remains outside Folio's core contract

## Trail
- 2026-08-29 @codex (PR #20): stale implementation and branch deleted; the provider-neutral integration idea is retained for a clean rebuild.
