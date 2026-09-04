---
title: Cards carry icons
status: released
tags: [plugins, kanban]
type: feature
created: '2026-08-26'
milestone: "0.1"
---

Owner report from the personal board: after flattening tags to four
categories, the faces read as text only — an icon per category would make
the board scannable at a glance.

Design space, two shapes that compose:
1. A tag-to-icon map in board.yaml — the column set already lives there,
   category topology fits the same human-owned file, and every card with
   the tag wears the icon with no per-card work. The recommended v1.
2. A per-card `icon` frontmatter field as an override, for the card that
   is not its category.

V1 scope: the icon renders on the card face beside the title and in the
dialog header; unknown or empty values warn and render nothing (prose
warns, topology fails); the data module carries the resolved icon so the
component stays dumb. Emoji strings first — an icon-set dependency is a
heavier decision this card does not take.

## Acceptance criteria
- [x] A tags-to-icon map in board.yaml puts an icon on every face wearing the tag
- [x] Unknown values warn, never break the board
- [x] The formats page documents the map beside the column set

## Comments
- 2026-08-27 @claude: One docs overstatement: formats.md:49 says the card wears the icon "on its face and in its dialog", and the trail says "face + dialog render it" — but the component renders the icon only on the face (test_kanban_plugin.py:2035 pins exactly one render site; no card.icon in the dialog). Either render it in the dialog header or trim the docs clause.

## Trail
- 2026-08-26 @pguijas (c95c72734): icons map in board.yaml, resolved per card at normalize, face + dialog render it; shipped map-only, no per-card override
- 2026-08-27 @claude: audit: all three criteria verified — _resolve_card_icons (folio/plugins/kanban.py:1238), face pill (kanban-board.tsx:2755), warn tests (test_kanban_board.py:1531,1566), formats.md:36-49; landed on this branch
