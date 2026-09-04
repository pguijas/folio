---
title: "The composer is a full-height rail beside the board"
status: released
milestone: "0.1"
type: feature
tags: [plugins, kanban]
created: 2026-08-16
---

The composer opens as a popup under the filter bar, five columns wide. With
one control per field the grid lost its balance: a tall status list beside a
lone priority checkbox beside three floating selects, and Created wrapped
underneath. The owner's direction: the composer becomes a toggleable panel
occupying the full height of the board's left side, and the popup dies.

Agreed shape:

**Structure.** Below the filter bar the board area becomes a two-column
grid: a ~17rem composer rail and the board. Open, the board narrows;
closed, the rail's column is gone and the board takes the full width. The
filter bar stays above, spanning everything; the existing filter glyph at
its left edge is the toggle (`aria-expanded`/`aria-controls`). The rail is
sticky below the bar with its own scroll. Sections stack in one column —
status, priority, type, milestone, assignee, tag, created — with the
"Also" chips and "Clear the filter" at the foot. The controls themselves
(`PanelRow`, `PanelSelect`, `PanelTagInput`) do not change; the popup's
positioning (`absolute top-full`, the 52vh cap, the five-column grid) dies.

**Behavior.** Closed by default, no persistence. Escape inside the rail
closes it and returns focus to the toggle, as the popup did. Below `lg`
there is no room to push: the same panel renders as a fixed left drawer
(same width, shadow); click outside or Escape closes it. `/` keeps
focusing the expression field. This is layout only — the language, the
rewrite helpers, and the no-second-store invariant are untouched.

## Acceptance criteria
- [x] below the filter bar, an open rail (~17rem) and the board share a two-column grid; closed, the board takes the full width
- [x] the filter glyph in the bar toggles the rail, with aria-expanded and aria-controls
- [x] the rail is sticky below the bar and scrolls its own overflow
- [x] sections stack in one column, Also chips and Clear at the foot; every control unchanged
- [x] closed by default, no persisted state; Escape inside closes and returns focus to the toggle
- [x] below lg the rail is a fixed left drawer; click outside or Escape closes it
- [x] "/" still focuses the expression field; typed text and controls stay one expression
- [x] the popup positioning and its five-column grid are gone from the component
- [x] compact board miniatures render exactly as before
- [x] the composer paragraph in docs/guide/plugins/kanban/index.md describes the rail

## Comments
- 2026-08-27 @claude: The criteria describe the in-flow grid+sticky shape; the owner's later redirect (trail ba3eaae45) made the public board a viewport-height workspace where the rail is a full-height flex panel instead. Both shapes live in FilterPanel today (workspace flag), so the ticks read against the docs embed and the workspace mode is the deliberate successor, not a deviation.

## Trail
- 2026-08-16 @claude: carded from owner direction — full-height left rail replacing the popup; filter bar stays above; closed by default; drawer below lg.
- 2026-08-16 @claude (b1f9ff595): rail shipped: two-column grid on lg, fixed drawer below, popup positioning gone; controls untouched; suite green
- 2026-08-16 @claude (7a2d34273): final review fixes: rail clears the sticky navbar via --nextra-navbar-height calc, Escape no longer tears down the rail with the card dialog, rem breakpoint, conditional aria-controls, honest test names
- 2026-08-16 @claude (3283521fe): owner review: the rail now spans the full height — the filter bar narrows into the grid's right column; staging banner stays full-width above
- 2026-08-16 @claude (ca7daff27): owner review: the rail surface stretches to the board's foot; the controls follow the scroll inside it
- 2026-08-17 @claude (a0d490b80): review fix: the bar's render gate returns to compact-only, so the static page keeps the bar and its h1; stale docstring rewritten
- 2026-08-17 @claude (a28e88878): owner found the rail overflowing: the public view never defined --nextra-navbar-height, so the rail computed against 0px under a fixed 64px navbar; the view layout now declares 4rem beside its pt-16
- 2026-08-17 @claude (ba3eaae45): owner redirected after the sticky rounds: the public board is now an app workspace — viewport-height section under the navbar, rail as a fixed-height floating panel with its own scroll, canvas scrolls both axes; docs embeds keep the in-flow layout
- 2026-08-17 @claude (ad58b1dc3): owner: left margin asymmetric — the workspace now runs full-bleed, the rail truly touches the edge it was drawn for, and the canvas keeps 24px on both sides
- 2026-08-27 @claude: audit: grid/drawer/Escape/toggle verified (kanban-board.tsx:4441-4525, 1438-1480, 4207-4250), popup remnants gone (test_the_composer_is_a_rail_beside_the_board), docs index shows the rail; the workspace redesign (ba3eaae45) supersedes the sticky shell on the public board and the docs embed keeps it; landed on this branch
