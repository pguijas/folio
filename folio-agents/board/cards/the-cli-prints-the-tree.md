---
title: "folio kanban show prints the tree"
status: backlog
milestone: "0.2"
tags: [plugins, kanban, cli]
created: 2026-08-20
type: feature
size: S
source: folio#feat/artifact-board-poc
parent: the-board-reads-as-a-tree
---

`folio kanban show` prints a flat table. If the site nests and the CLI does not,
the decomposition is visible to people and invisible to agents — and the CLI is
the surface agents actually operate this board through. The board's whole claim
is that humans and agents work the same files through the same commands; a
structure only one of them can see breaks it.

Agreed shape:

**`show` nests by default.** Children indent under their parent, roots in the
existing order. The columns the table already prints stay as they are; only the
id column gains indentation. A board where no card sets `parent` prints exactly
what it prints today, so this changes nothing until decomposition is used.

**A flat reading stays available.** `--flat` prints the current output, because
piping into `grep` and `awk` wants one card per line with no leading structure,
and a tool that only offers the pretty form is a tool you fight.

**One subtree.** `folio kanban show --under <id>` prints that card and
everything beneath it. This is the command an agent runs when it picks up an
epic, and the reason to have it is that `parent:<id>` as a filter gives only
direct children, not the subtree.

**Cycles do not hang the CLI.** The build already refuses a ring once
`a-parent-cycle-fails-the-build` lands, but `show` reads boards it did not
build. It carries its own visited set and prints a legible complaint rather
than spinning.

**The skill file teaches the gesture.** `board/SKILL.md` documents the card
schema and the session protocol; `parent` is listed there as a field with no
worked example of decomposing anything. Add the example, and say plainly when a
card should become a parent instead of growing a longer criteria list.

## Acceptance criteria
- [ ] `show` indents children under parents by default.
- [ ] `--flat` reproduces today's output byte for byte.
- [ ] `--under <id>` prints the full subtree of that card.
- [ ] `--under` with an unknown id fails with a message naming the id.
- [ ] A board with a parent ring prints a complaint and exits, and does not hang.
- [ ] A board where no card sets `parent` prints what it prints today.
- [ ] `SKILL.md` shows a worked decomposition.

## Trail
- 2026-08-20 @claude: card created
