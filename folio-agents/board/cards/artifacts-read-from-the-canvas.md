---
title: "Artifacts read from the canvas"
status: released
priority: high
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-24
type: feature
size: L
source: folio#feat/artifact-board-poc
parent: artifacts-live-beside-their-card
artifacts:
  - doc: board/cards/artifacts-read-from-the-canvas/canvas-reading-compared.md
    label: Four readers compared
  - doc: board/cards/artifacts-read-from-the-canvas/where-card-pages-publish.md
    label: Where card pages publish
  - file: board/cards/artifacts-read-from-the-canvas/reading-overlay.html
    label: Reading overlay (recommended)
  - file: board/cards/artifacts-read-from-the-canvas/reading-rail.html
    label: Reading rail
  - file: board/cards/artifacts-read-from-the-canvas/dialog-reader.html
    label: Dialog reader
  - file: board/cards/artifacts-read-from-the-canvas/board-reader-page.html
    label: Board reader page
---

The build publishes what a card produced; reading it still means leaving the
board. A `doc:` artifact opens a compiled page at `/docs/kanban/<id>/<stem>/`
wearing full documentation chrome, and a "Kanban" folder sits in the docs
sidebar between "Migrating from Sphinx" and "Source Code" as if board working
papers were part of the documentation's teaching order. A `file:` artifact
opens raw in a new tab. The owner's verdict names both halves: artifacts must
be readable from the canvas, and card pages indexing into /docs is weird.

Four readers were built in full against the real 44-card board, verified in a
headless browser, and compared: an overlay that takes the viewport above the
dimmed board, a right rail beside still-live columns, a reading pane inside
the card dialog, and a board-owned page at `/kanban/<card>/<artifact>`. The
comparison recommends the overlay. The demo card decided it: this board
attaches long documents and full-width prototypes, both want the whole
viewport, and the overlay is the only in-place reader that grants it — while
also being the cheapest to build inside the existing board component and the
only in-place reader whose URL is applied on hash change rather than only
at load.

The route half has its own note. Of the six surfaces a card page reaches
today, five are right: the route is the durable address, search is how a
reader finds "swimlanes" in a comparison, the sitemap lists what is
published, llms.txt and the Markdown mirrors are what agents fetch. The one
leak is the docs sidebar, and the fix is a delist, not a migration: an
unlisted flag carried from `PluginDocument` into the sidebar generator's
`{"display": "hidden"}`, the same value it already uses for nested index
pages. Moving pages under board chrome would rebuild five surfaces to change
a breadcrumb; dropping compilation would delete the address, the search hit,
and the agent copy.

The decision is the owner's, by looking: every prototype opens from this
card's artifact band, and the comparison says what each is bad at.

## Acceptance criteria
- [x] Four canvas readers prototyped against the real board, browser-verified, and compared, with a recommendation.
- [x] A published artifact opens and reads on the board itself, without leaving `/kanban`.
- [x] Card pages leave the docs sidebar; route, search, sitemap, llms.txt, and Markdown mirrors keep them.
- [x] The reading position is a URL that restores on load and applies on hash change.
- [x] An artifact with no published target renders as the path it is, never a dead link.
- [x] The shipped reader is re-checked against a document that actually contains tables; the comparison's table verdicts rest on a probe.

## Comments
- 2026-08-27 @pguijas: Owner direction, 2026-08-27: artifacts must not be listed in the docs — /docs/kanban/ stops indexing them — and reading happens without leaving the kanban, as a drawer sliding from the left. The drawer takes the rail prototype's place; the delist follows the card's own analysis (hidden from the sidebar, pages keep their routes).

## Trail
- 2026-08-24 @claude: carded from owner direction — artifacts readable from the canvas, card pages out of the docs index; four readers built and verified, overlay recommended, decision open
- 2026-08-27 @claude: shipped — owner chose a left drawer over the recommended overlay; the drawer reads compiled pages styled and runs prototypes sandboxed at full width, the position is a URL, dead targets stay plain text; the docs delist landed as the card's own hidden-subtree analysis plus a /docs/kanban/ forward to the board; the table verdict rests on a real probe through the compiled pipeline, both themes
- 2026-08-29 @codex (release/0.3.0): all criteria verified on the release branch; reclassified as the 0.3 board reader surface it already ships with.
