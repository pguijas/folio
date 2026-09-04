---
title: "Cards carry comments"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-18
type: feature
size: M
source: folio#feat/artifact-board-poc
assignee: claude
---

The trail records what happened; nothing on a card holds a conversation.
The owner wants comments — and, correcting the first mockup, wants them
**as their own separated section, like the artifacts**: a full-width band
of the dialog, not prose squeezed between criteria and trail.

Agreed shape:

**The section.** `## Comments` in the card markdown, one line per
comment: `- YYYY-MM-DD @actor: text`. The trail's grammar family minus
the ref — a comment argues, it does not point at a commit. Strict
writer, tolerant reader: a bullet that misses the grammar warns at build
and still renders as prose, exactly like a malformed trail line.

**The band.** Between the body grid and the artifacts band: bubble glyph,
`Comments · N`, one row per comment — mono date, bold `@actor`, the text
with its inline markdown rendered. Same scroll cap and keyboard stop as
the artifacts band. No comments, no band: a mail without replies shows
no empty thread.

**The pipeline.** Loader parses the section; normalizer carries
`comments: {date, actor, text}[]`; the emitted interface grows
`KanbanComment`. CLI: `folio kanban comment <id> "text"
[--by NAME] [--commit]` — `--by` defaults to git user.name, the writer
validates date/actor/single-line text, and the line appends at the
section's tail through the same surgery as trail.

## Acceptance criteria
- [x] `## Comments` parses to `comments: [{date, actor, text}]`; a malformed line warns and the build survives
- [x] the dialog shows the comments band between body and artifacts — date, `@actor`, markdown-rendered text — and no band when empty
- [x] `folio kanban comment <id> "text"` appends the canonical line, creates the section when missing, defaults `--by` to git user.name, collapses whitespace like the trail writer, and refuses empty text
- [x] Comments stay in the card Markdown; move-command export never rewrites or duplicates them
- [x] docs cover the section grammar, the CLI verb, and the band; SKILL.md and the agents table teach the gesture
- [x] tests: loader parse + malformed warn, CLI append/create/refuse, component pins for band order and `<MdInline text={comment.text} />`

## Trail
- 2026-08-18 @claude: carded from owner direction — comments as their own separated section like the artifacts; conversation distinct from the trail's record.
- 2026-08-19 @claude (bb05cf990): shipped: ## Comments parsed/normalized/exported, the thread band above the artifacts, folio kanban comment with git-user default; review reproduced the Rich-markup crash and the case-blind heading hole, both fixed with the trail sharing the cure
- 2026-08-29 @codex (release/0.3.0): removed the obsolete boardToYaml criterion after that export format retired; the shipped Markdown contract is fully covered.

## Comments
- 2026-08-18 @claude: dogfood: this very thread renders in the band this card ships
- 2026-08-26 @claude: The boardToYaml criterion is unsatisfiable since the export writer retired with the single-format change; reword it against the move-command export when this card is reviewed.
- 2026-08-27 @claude: Audit 2026-08-27: five of six criteria verified by named artifacts (kanban_board.py:335-358 + test_kanban_board.py:1404; kanban-board.tsx:3607-3638 + test_the_dialog_threads_comments_like_a_mail; kanban_cli.py:965-991 + test_kanban_cli.py:906; formats.md:207-213, cli.md:220-234/279, SKILL.md:75-110). The boardToYaml criterion cannot be ticked: boardToYaml no longer exists and test_kanban_plugin.py:591 pins its absence — it held at ship (bb05cf990) and retired with the single-format change. Reword or strike that criterion and the card graduates to released; everything it shipped is on this branch.
