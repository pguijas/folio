# Decomposition views for the board — five prototypes compared

Built 2026-08-20 to answer one question: the cards carry a `parent` field that
nothing renders, so what should render it. Five layouts were built in full,
against the real 35-card board, and compared side by side rather than argued on
paper. Each was then verified adversarially in a headless browser.

The prototypes are here, beside this document and beside the card both belong
to. None of it is product code and none of it will become product code; it is
the evidence a decision was made on, kept where the decision is recorded. Open
any `.html` in this directory to see the layout it argues for.

## The question

`parent` has been in the cardfile format since it shipped: one card id,
validated against the board, settable from the CLI, already a filter field. The
guide states the gap plainly — "`parent` is a validated pointer, not a
workflow". On a board of 35 cards, none used it. The pointer existed and the
shape it pointed at was invisible, so nobody reached for it.

Because no real hierarchy existed, the prototypes ran on an invented one,
chosen to force the cases that break naive implementations: three levels deep,
and one child sitting in a different column than its parent.

## The five

**Tree table.** One table for the whole board, the first column carrying the
tree by indentation, every other column a field read straight down. The literal
reading of the request and the baseline for the rest.

**Epic swimlanes.** The kanban columns kept; rows become lanes, one per epic,
with children placed in the column their own status names. Decomposition and
status as two axes of one grid.

**Board with inline expansion.** The incumbent column board, minimally changed:
a card with children grows a disclosure and lists them inside itself.

**Tree rail and detail.** A persistent outline rail on the left, the selected
node's children as a table on the right. Master-detail, the shape a product
tool with deep decomposition converges on.

**Document outline.** The board as one nested document: no rules, no cells,
indentation and typography carrying depth. The argument is that these cards are
markdown files and a plan should read like a plan.

## What was chosen

**Tree table**, with the column board kept untouched beside it.

Columns are the right reading for what is in flight and the wrong reading for
what something breaks into. The two readings want different shapes, and the
board already works — so the answer is a second view over the same files, not a
replacement.

Taken from the losing variants: the `DIVERGED` marker and its toolbar count
from the tree table's own answer to the cross-column child, and the subtree
rollup header from tree rail and detail.

Rejected, with the reason worth keeping:

- **Swimlanes** resolve the cross-column child for free, which is the strongest
  single argument any variant made. They also encode exactly one level of
  decomposition — a grandchild cannot get a lane without shredding the grid —
  and they are mostly air: six lanes by four columns is twenty-four cells, of
  which this board fills nine, measuring 4,457px tall at 1440px.
- **Inline expansion** costs nothing to learn, and a deep tree stretches a
  column without end.
- **Tree rail and detail** scales furthest and shows the least at once.
- **Document outline** reads best and scans worst. Comparing one field across
  35 rows is a saccade per line where a table is one glance down a column.

## What five independent implementations all got wrong

This is the part that justifies building five instead of one. A defect that
every implementation reaches independently is a property of the problem, not of
the implementation, and the real one will reach it too.

### "Done" has no meaning on this board

All five defined a parent's progress as how many descendants reached the last
column. `Released` is empty, and `In progress` is empty. Every parent therefore
printed `0 of N` while its distribution bar rendered full — truthful, and it
reads as a contradiction.

Three separate verification passes reached the same conclusion independently:
this is not an execution defect and cannot be fixed by adjusting the widget.
Redefining done to include `In review` would be a lie about the board.

**The open question, which is a product decision:** what counts as done for a
parent — the last column, the ratio of checked acceptance criteria across the
subtree, or nothing at all. Until it is answered, any rollup shipped will read
as a constant zero on this board.

### Collapsing or filtering throws the focus out of the tree

Three of the five lost keyboard focus when the tree re-rendered, each for a
different reason: reading `document.activeElement` after `innerHTML` had
already been replaced; leaving the only `tabindex="0"` on a node that
collapsing had set to `display: none`; and dropping the roving tab stop when a
filter removed the active row.

Three independent implementations hitting the same class of bug means a
re-rendering tree must decide explicitly where focus lands when the focused row
stops existing. The rule that worked: move to the nearest still-rendered
ancestor, and fall back to the first row.

### A roving tab stop leaks

One implementation promoted rows to `tabindex="0"` without demoting the
previous holder; after four arrow presses a single column had five tab stops
while its own comment claimed one.

### Filter highlighting falls back to the browser default

Two variants styled `<mark>` in some contexts and not others, so matching text
in an unstyled context painted `#ff0` into an oklch palette, most visible in
dark mode.

### A match can hide inside a collapsed branch

One filter marked ancestors as context only when the ancestor was not itself a
match, so a match nested under another match never rendered while the toolbar
counted it. A filtered tree must open every ancestor of every match, and must
restore the hand-set collapse state when the filter clears.

## Cycles are not validated

Found while designing, not while prototyping. `_validate_relations` checks that
`parent` names an existing card and is not the card itself. It does not check
that following the chain terminates, so `a → b → a` passes the build today.

This is harmless only because nothing walks the chain. Every prototype had to
carry its own visited set, and each was tested by injecting a two-cycle, a
three-cycle, a self-parent and a dangling parent. The fix belongs in the
loader, before anything renders a tree.

## A note on the NUL byte

`template/components/kanban-board.tsx` wrote a cache-key separator as a
literal NUL byte inside a template string. It worked, and it made the file
binary to `grep` and `diff`.

The brief warned the prototype agents about it. One of them, while fixing an
unrelated markdown bug, wrote four raw NUL bytes into its own source — and
caught it. The failure mode is easy to reach by accident, which is the argument
for fixing the original rather than documenting it. The branch now writes an
escaped separator, so the component is ordinary UTF-8 text again.

## Where this went

- `the-board-reads-as-a-tree` — the epic, and the choice recorded above
- `a-parent-cycle-fails-the-build` — the loader gap
- `the-board-component-splits-into-modules` — the 4312-line file, and the NUL byte
- `the-table-is-a-second-view` — the view switch and the URL
- `the-table-draws-one-row-per-card` — the row grammar
- `the-tree-filters-without-re-rooting` — filter semantics
- `a-parent-says-what-it-breaks-into` — the rollup and the divergence marker
- `the-cli-prints-the-tree` — the agent-facing surface
