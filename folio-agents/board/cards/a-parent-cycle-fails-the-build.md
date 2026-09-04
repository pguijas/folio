---
title: "A parent cycle fails the build"
status: backlog
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-20
type: bug
size: S
source: folio#feat/artifact-board-poc
parent: the-board-reads-as-a-tree
---

`_validate_relations` checks two things about `parent`: that it names a card on
this board, and that it is not the card itself. It does not check that following
the chain ends. Two cards that name each other, or any longer ring, pass
validation and ship.

This has been harmless because nothing walks the chain. The moment a view
renders the tree, a ring is an infinite descent: the page hangs, and the build
that produced it reported success. The bug has to be fixed before anything
reads `parent` recursively, not after a board bricks itself.

Agreed shape:

**The rule.** Following `parent` from any card must terminate. A ring of any
length raises the same way a dangling parent does — a build error naming the
cards in the cycle, in the order they point, so the reader can see which link to
cut. Consistent with the rest of the topology checks, which fail the build
rather than warn: an unresolvable board is not a board.

**Where.** `_validate_relations` in `kanban_board.py`, beside the checks it
already makes. One pass over the cards, following each chain with a visited set;
a board of a few thousand cards is not worth an algorithm.

**The self-parent case folds in.** A card naming itself is a cycle of length
one. Keep its message, which is clearer than the general one, and let the
general check catch everything longer.

`blocked_by` is a list and can also form a ring. It is not walked recursively by
anything and is out of scope here; say so in the code rather than leaving the
asymmetry unexplained.

## Acceptance criteria
- [ ] `a → b → a` fails the build with an error naming both cards.
- [ ] A longer ring fails the same way, naming every card in it.
- [ ] A card naming itself keeps its existing, more specific message.
- [ ] A deep but acyclic chain still builds.
- [ ] `folio kanban check` surfaces the failure as a red gate, not a warning.

## Trail
- 2026-08-20 @claude: card created; gap found while designing the tree view
