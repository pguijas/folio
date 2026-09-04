---
title: Agents claim and orchestrate
status: ideas
tags: [spec, kanban]
parent: project-os-technical-plan
created: '2026-08-25'
type: plan
milestone: "0.2"
---

The board has `assignee`, `parent`, and trail lines, but no claim semantics, no decomposition protocol, and no fleet patterns. An agent can read who owns a card, but not take it; can see a parent link, but not break work into child cards; can append trail lines, but not coordinate with other agents through the board state.

This card defines the proposal: claim semantics for `assignee` so an agent marks a card as its own, decomposition via `parent` so one card breaks into a tree of child tasks, and fleet patterns so multiple agents coordinate through board queries rather than shared memory. The panel's A-item outlines claim, decompose, and report as the three operations. This proposal must be code and tests, not documentation prose.

## Acceptance criteria
- [ ] Claim semantics are defined and implemented for `assignee`
- [ ] Decomposition protocol is defined: how a card creates children via `parent`
- [ ] Fleet coordination patterns are demonstrated with working examples
- [ ] An agent can claim a card, decompose it, and report completion through board state

## Comments
- 2026-08-27 @claude: Criteria are define-and-demonstrate level (claim semantics, fleet patterns) rather than checkable behavior; if 0.4 scoping tightens, this is the first candidate to slide to ideas or absorb into project-os-technical-plan's write-MCP item.

## Trail
- 2026-08-27 @claude: reorganization: criteria are define-and-demonstrate level, not pick-up-able work — pooled in ideas per the owner's ideas/backlog split; milestone kept, project-os remains the parent context
