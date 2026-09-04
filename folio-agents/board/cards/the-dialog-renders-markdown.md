---
title: "The dialog renders its markdown"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-18
type: feature
size: M
source: folio#feat/artifact-board-poc
assignee: claude
---

Cards are markdown files, and the dialog prints their prose raw: a
description authored as `**The header.**` shows its asterisks, backticked
commands show their backticks. The owner hit it on the board today. The
body is the one place a card talks, and it talks in the format the file
already is.

Agreed shape:

**The subset, from usage.** A scan of this board's own cards: bold and
inline code everywhere, multi-paragraph descriptions common, zero em,
links, or lists. Rendered: `` `code` ``, `**bold**`, `[text](https://…)`
with the scheme guard the repo already applies everywhere (anything not
http(s) stays literal text), and paragraphs split on blank lines. No raw
HTML ever — tokens become React nodes, never `dangerouslySetInnerHTML`.
Unmatched marks stay literal: a stray asterisk is prose, not a crash.

**The seams.** A pure `parseInlineMd(text) → MdToken[]` tokenizer beside
the other extracted-and-executed helpers, exercised by the node harness
like the filter language; a small renderer maps tokens to `<code>`,
`<strong>`, `<a>`. Applied to the dialog description (paragraphs), each
acceptance criterion, and each trail note. Faces stay title-only; raw
strings stay raw in data, export, and filters.

## Acceptance criteria
- [x] `**bold**`, `` `code` ``, and `[text](https://…)` render in the dialog's description, criteria, and trail notes; blank lines split description paragraphs
- [x] a non-http(s) link target stays literal text; no `dangerouslySetInnerHTML` exists in the component
- [x] unmatched `*`/`` ` `` marks render as the literal characters
- [x] `parseInlineMd` is executed by the node harness: code, bold, link, literal-fallback, and scheme-guard cases
- [x] raw markdown stays raw in kanban-data, boardToYaml, and filter matching

## Comments
- 2026-08-26 @claude: The boardToYaml criterion is unsatisfiable since the export writer retired with the single-format change; reword it against the move-command export when this card is reviewed.
- 2026-08-26 @claude: Owner hit the block gap on the personal board: a description list (- Baldas sala...) renders inline as one run. The dialog splits blank-line paragraphs but every block is a <p> + MdInline; list blocks need to become lists. Block pass incoming: pure parseMdBlocks (paragraphs, dash and numbered lists), executed under node like the inline grammar.
- 2026-08-27 @claude: Audit 2026-08-27: criterion 5's boardToYaml clause is moot, as the earlier comment predicted — the writer retired with the single-format change and its absence is itself pinned (tests/test_kanban_plugin.py:591). The surviving export path, the footer's moveCommand, carries only the card id and column id, so no markdown can leak there. Data (kanban-data.ts) and filter matching verified raw.

## Trail
- 2026-08-18 @claude: carded from owner direction — the dialog must render the markdown the cards are written in; subset drawn from the board's real usage.
- 2026-08-18 @claude (269d5eb22): shipped: parseInlineMd tokenizes code/bold/http-links with paragraphs on blank lines, tokens become React nodes (no innerHTML path); review reproduced the double-backtick mangle on this very card and it now parses as CommonMark quoting; adversarial ReDoS claim refuted at card scale
- 2026-08-26 @pguijas (2d83922e1): block grammar landed: parseMdBlocks (paragraphs, dash and numbered lists), executed pins, dialog consumes it
- 2026-08-27 @claude: audit: landed on this branch — MdInline over description/criteria/trail/comments, parseMdBlocks block grammar (owner's list gap closed by 2d83922e1), both grammars executed under node in test_kanban_filter_language.py, no innerHTML path, data and filters stay raw
