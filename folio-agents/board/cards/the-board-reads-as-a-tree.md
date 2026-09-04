---
title: "The board reads as a tree"
status: backlog
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-20
type: feature
size: XL
source: folio#feat/artifact-board-poc
artifacts:
  - doc: board/cards/the-board-reads-as-a-tree/prototypes-compared.md
    label: Five layouts compared
  - file: board/cards/the-board-reads-as-a-tree/tree-table.html
    label: Tree table (chosen)
  - file: board/cards/the-board-reads-as-a-tree/epic-swimlanes.html
    label: Epic swimlanes (rejected)
  - file: board/cards/the-board-reads-as-a-tree/board-inline-expansion.html
    label: Inline expansion (rejected)
  - file: board/cards/the-board-reads-as-a-tree/document-outline.html
    label: Document outline (rejected)
  - file: board/cards/the-board-reads-as-a-tree/tree-rail-detail.html
    label: Tree rail and detail (rejected)
---

`parent` has been a real field since the cardfile format shipped: one card id,
validated against the board, settable from the CLI, and already a filter field.
Nothing renders it. The docs admit the gap in as many words — "`parent` is a
validated pointer, not a workflow" — and when this card was written, not one of
the board's 36 cards set it. The pointer existed and the shape it pointed at was
invisible, so nobody reached for it. The seven cards below are the first to use
it, and they exist so this view has real work to show.

The owner's call, after five prototypes built side by side: **the column board
stays exactly as it is** and a second view joins it. Columns are the right
reading for "what is in flight"; they are the wrong reading for "what does this
break into". Two readings of one set of files, not two products.

The five prototypes and the comparison they produced are attached, and they sit
in this card's own directory, which the build now publishes: each tile opens
the layout it argues for, on the board's own site rather than somebody else's.
Read `prototypes-compared.md` for why the tree table won and what the other
four were better at.

Agreed shape:

**The view is a table.** One row per card, no exceptions. The first column is
the tree: indentation carries depth, a disclosure triangle sits on any card
with children. Every other column is one field read straight down — status,
milestone, type, size, assignee — the way a spreadsheet is read and a column
board cannot be.

**Status and parent are allowed to disagree.** A child in Backlog under a
parent in In review is not a contradiction to hide: a kanban orders by column,
a tree orders by parent, and the two orders are independent by design. The
table keeps the child under its parent, marks the row, and counts how many such
rows exist. The disagreement is a number, not a surprise.

**A parent says what it breaks into.** Children count, how far they have got,
and what a collapsed row is hiding. A derived value never reads as an own
value.

**Nothing new in the format.** No `children` key, no ordering key, no epic
type. The tree is `parent` read backwards, and that is the whole data model.

Rejected while deciding, so it stays rejected: swimlanes by epic (resolves the
cross-column child for free, but encodes exactly one level of decomposition and
leaves half the grid empty); expanding children inside the existing cards (no
new view to learn, but a deep tree stretches a column without end); the board
as one nested document (reads beautifully, scans worse than a grid on any
single field).

Out of scope, deliberately: reparenting from the interface. Changing a card's
parent stays a cardfile edit or a CLI call, like every other structural change.

## Acceptance criteria
- [ ] The column board is unchanged by this work.
- [ ] A second view renders the board as a table, one row per card.
- [ ] A card's children are reachable from it in both views.
- [x] The board's own cards use `parent`, so the view has real work to show.
- [ ] No new frontmatter key.

## Trail
- 2026-08-20 @claude: card created after five prototypes; tree table chosen, swimlanes and outline rejected
- 2026-08-20 @pguijas: five layouts prototyped against the real board and verified adversarially; tree table chosen, columns kept; all five rollups read zero, so what counts as done is still open
- 2026-08-20 @claude: prototypes and the comparison moved into the card's own directory and attached; six artifacts, all local paths
- 2026-08-27 @claude: audit 2026-08-27: prototyping and decomposition are done, but the table view is unbuilt (no tree/table code in kanban-board.tsx) and all seven children sit in backlog — the epic parks in backlog until its children deliver; its four open criteria are exactly the children's work
