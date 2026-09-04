---
title: "The tree filters without re-rooting"
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

Filtering a flat list hides rows. Filtering a tree has a decision in it that a
flat list never poses: when a child matches and its parent does not, what
happens to the parent?

Three answers exist. Drop the parent and the child rises to the root, which is
fast to implement and changes what the card means — a card lifted out of its
parent is a card without its context. Hide the child with its parent, which
loses matches. Or keep the parent as context.

Agreed shape:

**The parent stays as context.** A non-matching ancestor of a match renders,
dimmed, not counted as a match, and never re-rooted. Depth is invariant: a row
that silently changes indentation while you type is a row you cannot trust, and
the tree's shape is the one thing this view exists to show.

**Ancestors of a match open automatically.** A match inside a collapsed branch
is a match you cannot see. Opening for a filter does not overwrite the collapse
state you set by hand: clear the filter and the tree returns to how you left it.

**Two counts, both stated.** How many cards matched, and how many rows are on
screen. They differ by exactly the context ancestors, and stating one without
the other is how a filtered tree lies about its size.

**Matched text is marked** in the accent, in the title and in the id, since the
filter language matches on both.

**The filter language is unchanged.** The same expression that filters the
columns filters the tree; no view-specific syntax, no second parser. `parent`
is already a filter field, so `parent:some-id` narrows to one card's children
in either view, and that keeps working.

## Acceptance criteria
- [ ] A matching child renders under its non-matching parent, at its real depth.
- [ ] A context ancestor is visually distinct from a match and is not counted
      as one.
- [ ] Matches inside collapsed branches become visible while filtering.
- [ ] Clearing the filter restores the hand-set collapse state.
- [ ] Both counts are shown: cards matched, rows displayed.
- [ ] The same filter expression yields the same card set in both views.

## Trail
- 2026-08-20 @claude: card created
