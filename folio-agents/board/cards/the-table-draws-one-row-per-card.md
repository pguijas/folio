---
title: "The table draws one row per card"
status: backlog
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-20
type: feature
size: L
source: folio#feat/artifact-board-poc
parent: the-board-reads-as-a-tree
blocked_by: [the-table-is-a-second-view, a-parent-cycle-fails-the-build]
---

The table itself: the row grammar, the tree column, and the columns you read
down. This is the card the whole view is made of.

Agreed shape:

**One row per card, always.** No summarized rows, no "and 4 more". 35 cards is
35 rows. A reading whose row count does not match the card count is a reading
you cannot trust.

**The first column is the tree.** Indentation carries depth; a disclosure
triangle sits on any card with children and nothing sits where a card has none,
so a leaf is not a parent with an empty box. The card id renders beside the
title in mono, right-aligned in the column, because the id is what every CLI
command takes and copying it out of the view is the common gesture.

**The other columns are fields.** Status, milestone, type, size, assignee. Each
one read straight down as a single scannable column, which is the whole reason
this view exists and the one thing the column board cannot do. Absent values
render as nothing, not as a dash: 32 of 35 cards have no priority today and a
column of dashes is noise pretending to be data.

**Status is the control.** The status cell is where a move is staged, using the
same overlay and the same `folio kanban move` output as the columns. No second
mechanism.

**Sorting keeps the tree intact.** Sorting by a column sorts siblings within
their parent; a child never leaves its parent. A sort that flattens the tree is
a different view, and if that is ever wanted it is a different card.

**Collapse is cheap and total.** A row collapses, and expand-all and
collapse-all are one press each. Collapse state survives filtering.

**Keyboard.** Up and down move between rows, left and right collapse and
expand, and focus is visible. A table of 35 rows that needs a mouse is a table
that failed.

Watch for, found in the prototype: when a collapsed parent shows a value
derived from its hidden children, that value must not be drawn in the same
register as a value the card owns. The prototype rendered an inherited size as
if the card carried it, which is a lie the reader has no way to detect.

## Acceptance criteria
- [ ] Row count equals card count, at every filter and collapse state.
- [ ] Depth renders correctly at three levels.
- [ ] A card with no children draws no disclosure control.
- [ ] Empty fields render as empty, not as a placeholder glyph.
- [ ] Staging a move from a status cell produces the same command as the board.
- [ ] Sorting any column leaves every child under its parent.
- [ ] Full keyboard navigation with visible focus.
- [ ] A derived value is visually distinct from an own value.

## Trail
- 2026-08-20 @claude: card created
