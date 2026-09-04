---
title: Folio for Agents release cadence
status: in-review
priority: high
tags: [release]
type: release
size: L
created: 2026-08-30
milestone: "0.1"
---

Package, tag, and publish Folio for Agents independently from Folio Docs. The
first release is `folio-agents` 0.1 and uses its own `agents-v*` tag sequence.

## Acceptance criteria
- [x] The distribution, import package, executable, and version belong to Folio for Agents
- [x] Release automation listens only to `agents-v*` tags
- [x] A clean environment installs the Agents wheel without Folio Docs
- [ ] Folio for Agents 0.1 reaches its own release criteria
- [ ] Tag, push, and publication happen only after explicit owner approval

## Trail
- 2026-08-30 @codex (board): split from the former shared-distribution card when the products received independent boards and release cycles.
