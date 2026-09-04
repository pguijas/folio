---
title: "The table is a second view, not a second page"
status: backlog
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-20
type: feature
size: M
source: folio#feat/artifact-board-poc
parent: the-board-reads-as-a-tree
blocked_by: [the-board-component-splits-into-modules]
---

The board has one view and no concept of having more than one. Before the table
can be drawn, the page has to be able to hold two readings of the same data and
let you change which one you are looking at without losing your place.

Two pages was the alternative and it loses the thing that makes this worth
building: you narrow the board to a filter, you want the same set as a tree, and
a second route means retyping the filter. One page, two renderings, one filter.

Agreed shape:

**The switch.** A two-position control in the filter bar, beside the filter
glyph that already opens the composer. Board and Table, the current one marked.
It is a control on the bar because the bar is what both views share.

**The URL carries it.** `?view=table` alongside the existing `?q=`, written the
same way the query already writes itself — on a pause, not on every keystroke.
A link to a filtered tree is then just a link, which is what the board's own
protocol asks for: every report ends in something the reader can click.
`?view=board` and an absent parameter both mean the columns.

**What crosses the switch.** The filter and its results, the staged moves and
their count, and the selected card. Changing the view must never discard staged
work: the overlay is keyed by the column set and knows nothing about views, and
it stays that way.

**What does not cross.** Collapse state belongs to the tree and does not exist
in the columns. Scroll position is per view.

**The board is untouched.** This card adds the switch, the URL parameter, and
the seam a second view plugs into. It does not change a pixel of the columns.

## Acceptance criteria
- [ ] A control in the filter bar switches between board and table.
- [ ] `?view=table` restores the table on load; an absent or unknown value
      gives the board.
- [ ] Filter text survives the switch in both directions.
- [ ] Staged moves and their count survive the switch in both directions.
- [ ] The columns render identically to before this card.

## Trail
- 2026-08-20 @claude: card created
