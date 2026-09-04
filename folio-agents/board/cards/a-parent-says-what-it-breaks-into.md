---
title: "A parent says what it breaks into"
status: backlog
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-20
type: feature
size: M
source: folio#feat/artifact-board-poc
parent: the-board-reads-as-a-tree
blocked_by: [the-table-draws-one-row-per-card]
---

A tree that only indents is an outline. What makes decomposition useful is the
parent answering two questions without being opened: how much of this is done,
and does any of it disagree with where the parent sits.

Agreed shape:

**The rollup.** A parent carries how many cards sit beneath it — the whole
subtree, not just direct children, because a parent of two epics of five is not
a parent of two — and how far they have got. The measure is which columns the
descendants are in, and it must be legible when they are all in the same one:
the prototype's bar was full and its fraction read `0/10`, which is truthful and
reads as a contradiction. Whatever form this takes, state what the number counts
in the row itself rather than in a tooltip.

**The disagreement, named.** A child whose column differs from its parent's is
marked on its row, and the count of such rows appears in the toolbar. Today the
board has exactly one: `theme-contract-for-plugin-surfaces` sits in Backlog
under a parent in In review. That is not an error and must never be styled as
one. It is the ordinary case of a plan that has started in parts, and the
reason the table earns its place next to the columns is that it can show it at
all.

**The card knows both directions.** In both views, a card links to its parent
and lists its children. A child says what it is part of; a parent says what it
breaks into. Following either is one press.

**Inherited values are marked as inherited.** When a collapsed row shows
something drawn from below it, the register differs from a value the card owns,
and hovering says where it came from. This was the real defect the prototype's
verification pass found and it is the easiest one to reintroduce.

## Acceptance criteria
- [ ] A parent shows its whole-subtree count, not just direct children.
- [ ] The progress measure is legible when every descendant is in one column.
- [ ] What the number counts is stated in the row, not only on hover.
- [ ] A child in a different column than its parent is marked, and the total is
      in the toolbar.
- [ ] The marker does not read as an error.
- [ ] A card links to its parent and to its children in both views.
- [ ] A derived value never renders in the same register as an own value.

## Trail
- 2026-08-20 @claude: card created
