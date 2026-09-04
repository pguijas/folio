---
title: The kanban docs tell the truth
status: released
tags: [plugins, kanban]
created: '2026-08-25'
artifacts:
  - url: https://github.com/pguijas/folio/tree/feat/split-docs-and-agents/folio-agents/docs/board
    label: Folio for Agents board guides
milestone: "0.1"
---

The kanban documentation was rewritten to match what the plugin actually does, with every command verified against the CLI and every rule checked against the code. Five pages were restructured to separate concerns: how to start, how agents operate boards, what the CLI provides, what the formats allow, and what cards can carry.

The what-a-card-produces page waits for artifacts-live-beside-their-card's derived-artifacts criteria.

## Comments
- 2026-08-27 @claude: Audit 2026-08-27: this card's own claim — five pages rewritten and verified — is done and committed (e68606126 and the docs/kanban-rework trail). The what-a-card-produces page it mentions does not exist yet and waits on artifacts-live-beside-their-card (still in-progress); that page should be tracked there, not hold this card open. Note the card carries no acceptance criteria at all, so release rests on the body claim plus the artifacts listed.

## Trail
- 2026-08-24 @pguijas (docs/kanban-rework): kanban docs rewritten for truth — four pages restructured, every command verified
- 2026-08-25 @pguijas (docs/kanban-rework): addendum tasks applied — 7 cards carded, artifacts attached, protocol demonstrated
- 2026-08-25 @pguijas (e68606126): discovery section repaired: no runtime scans board/, the page now says who points an agent there; a guard now pins SKILL.md examples to board.yaml columns
- 2026-08-27 @claude: audit: the five rewritten pages exist and match the plugin as shipped; the deferred what-a-card-produces page is artifacts-live-beside-their-card's deliverable, not this card's remaining work
