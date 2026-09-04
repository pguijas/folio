---
title: Folio for Agents 0.1 release
status: in-progress
priority: high
parent: folio-for-agents-release-cadence
tags: [release, agents]
assignee: codex
size: L
source: folio#feat/split-docs-and-agents
type: release
created: 2026-08-29
milestone: "0.1"
---

Release the repository-native meta-harness as Folio for Agents 0.1. It wraps
existing coding harnesses with shared context, board state, rules, and durable
artifacts without requiring users to understand its low-level machinery.

## Acceptance criteria
- [ ] Board operations live under `folio_agents` and `folio-agents` with no legacy alias
- [ ] `agents.yaml`, cards, and releases are independent from Folio Docs
- [ ] Guides explain the meta-harness at product level without low-level overload
- [ ] The standalone wheel installs without Docs or Node.js and board checks pass
- [ ] The optional Docs adapter remains explicit and does not enter the core runtime

## Trail
- 2026-08-29 @codex (board): created when the mixed 0.3 release was split into independent product tracks.
- 2026-08-30 @codex (board): moved into the standalone Agents board; Docs no longer participates in its release gate.
