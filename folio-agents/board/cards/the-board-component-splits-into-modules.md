---
title: "The board component splits into modules"
status: ideas
milestone: "0.2"
tags: [plugins, kanban]
created: 2026-08-20
type: chore
size: M
source: folio#feat/artifact-board-poc
parent: the-board-reads-as-a-tree
---

`kanban-board.tsx` is 4312 lines and holds one view. It carries the card
contract, the staging overlay and its YAML writer, the whole filter language
(tokenizer, parser, matcher), the composer rail and its four control types, the
card face, the dialog, and the board itself. Adding a second view to that file
does not add a view, it doubles a file that is already the largest thing in the
template.

Split it before the table lands, not after. A refactor that follows a feature
ships the feature twice.

Agreed shape:

**The seams are already drawn.** The file's own section comments name them. The
split follows those lines rather than inventing new ones:

- the card contract and the board identity helpers;
- the filter language: tokenize, parse, match, count — it has no React in it at
  all and is the obvious first module out;
- the staging overlay: clone, diff, apply, and the YAML and move-command
  writers;
- the composer rail and its controls;
- the card face and the dialog;
- the board view itself.

**No behaviour changes in this card.** Pure moves plus the imports they force.
The test suites that cover the filter language and the YAML writer must pass
untouched — if a test has to change, the move was not pure and the change
belongs in its own card.

**One incidental fix.** `kanban-board.tsx:1431` writes a cache-key separator as
a literal NUL byte inside a template string. It works, and it makes the file
binary to `grep`, `diff`, and anything else that sniffs content — every search
of this file needs `grep -a` today. Write it `\0`.

The point of the split is not tidiness. It is that the next three cards each
touch one of these seams, and they should be able to touch one without holding
the other five in view.

## Acceptance criteria
- [ ] No module exceeds roughly 800 lines.
- [ ] The filter language module imports no React.
- [ ] Every existing kanban test passes without modification.
- [ ] The board renders identically before and after: same markup, same
      behaviour, same staged-move commands.
- [x] `grep` reads the sources without `-a`.

## Comments
- 2026-08-27 @claude: Still open and grown: kanban-board.tsx is now 4834 lines (card says 4312). This card is the head of the blocked chain for the entire table view (second-view → one-row-per-card → tree-filters), all milestone 0.4 under the tree epic. Metadata is already coherent; if the table is release-blocking for 0.4, this is the card that deserves high.

## Trail
- 2026-08-20 @claude: card created; NUL byte found while grepping the file for the tree work
- 2026-08-23 @codex (feat/artifact-board-poc): replaced the raw NUL with an escaped separator; the component is UTF-8 text again, while the larger module split remains open
