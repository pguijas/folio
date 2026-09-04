---
title: "Cards carry assignees, a source, and a size"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-17
type: feature
size: L
source: folio#feat/artifact-board-poc
assignee: [peter, claude]
---

A card can name one assignee, and nothing says where the work lives or how
big it is. The owner wants three more dimensions: several people on one
card, a source (the repo or branch the work belongs to — one branch per
project, for example), and a size. Assignee and tags already exist; this
card completes the set.

Agreed shape:

**`assignee` accepts a list.** The same key, two forms: `assignee: ana`
still works, `assignee: [ana, bo]` joins it. The loader normalizes both to
a list — trimmed strings, duplicates dropped, order preserved — and the
emitted TypeScript changes `assignee: string` to `assignee: string[]`. No
new `assignees` key.

**`size` is a closed scale.** `size: M`, case-insensitive, normalized to
uppercase. Anything outside S / M / L / XL is a hard loader error — the
same treatment as an unknown status: `folio build` stops and
`folio kanban check` goes red naming the file and the allowed values. The
one closed field in the model, by the owner's explicit choice.

**`source` is free text.** `source: folio#feat/x`, a URL, a repo name —
a free scalar with the same treatment as `type` (non-scalars warned and
ignored).

**The card.** The face's bottom line shows every assignee (`@ana @bo`) and
the size as a small bordered chip (`M`, `XL`). Source stays off the face —
the metadata line already carries type · phase · milestone. The dialog
gains Size and Source rows (a source starting with `http(s)://` renders as
a link) and the Assignee row joins the list. Cards without the new fields
render exactly as before.

**The composer.** `size` joins `CHECK_FIELDS` — tri-state checkboxes like
status and priority, only the values in use, in scale order S→XL, with
counts. `source` joins `SELECT_FIELDS`. Assignee keeps its select; a card
with two assignees counts for both values. The filter language does not
change — `size:m,l` and `-source:none` fall out of `FILTER_FIELDS`; URLs
with colons take quotes, which the language already has.

**The CLI.** `update --set` accepts `size` (validated against the scale),
`source`, and `assignee=ana,bo` (comma split, as `add --tags` already
does). The `show` table gains a Size column; source is not a column.

## Acceptance criteria
- [x] `assignee: ana` and `assignee: [ana, bo]` both load; the emitted interface says `assignee: string[]`; duplicates dropped, order preserved
- [x] a size outside S/M/L/XL fails the loader naming the file and the allowed values; check goes red; lowercase input normalizes to uppercase
- [x] `source` is carried as a free scalar; non-scalar warned and ignored
- [x] the card face shows `@ana @bo` and a size chip; cards without the fields render unchanged
- [x] the dialog shows Size and Source rows; an `http(s)://` source is a link; Assignee joins the list
- [x] size filters as tri-state checkboxes in scale order S→XL with counts; source is a select with counts plus "any"
- [x] a card with two assignees matches a filter on either one and counts for both in the composer
- [x] `update --set size=xxl` is rejected; `--set source=…` and `--set assignee=ana,bo` work; the show table has a Size column
- [x] docs cover the three fields: formats.md field list, the composer paragraph in index.md, cli.md, and the commented lines in _TEMPLATE.md
- [x] existing pins move from `assignee: string` to `assignee: string[]`; the filter-language tests execute multi-assignee values and the S→XL order

## Trail
- 2026-08-17 @claude: carded from owner direction — several assignees per card, a free source field, and a closed S/M/L/XL size; design approved in session.
- 2026-08-17 @claude (a3859e2b6): shipped: assignee lists, free source, and the closed size scale — loader to composer to CLI, docs and skill updated, v1 export byte-identity pinned by an executed test
- 2026-08-27 @claude: audit: all ten criteria verified against the repo — loader and normalizer (kanban.py:1419-1501, kanban_board.py:228-234), emitted assignee: string[] (kanban.py:57), face and dialog (kanban-board.tsx:2753-2792, 3337-3366), composer scale order (SIZE_ORDER), CLI (kanban_cli.py:907-922; test_kanban_cli.py:850/858/871), docs (formats.md:109-111, cli.md:184-198, _TEMPLATE.md:9-10); landed on this branch — in-review -> released
