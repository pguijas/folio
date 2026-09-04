---
title: Artifact viewer becomes a workspace
status: released
priority: high
tags: [plugins, kanban, ui]
source: folio#feat/kanban-artifact-viewer-integration
type: feature
size: L
created: '2026-08-29'
artifacts:
  - file: progressive-canvas.html
    label: "Progressive canvas (revised direction)"
  - doc: progressive-canvas-direction.md
    label: Progressive canvas direction
---

Opening a card should leave floating layers behind and turn the kanban into one continuous, resizable page. Each selection progresses after its parent: filters lead to the canvas, the card follows the canvas, and the artifact follows the card to the right when space allows or below when it does not. Stage 2 starts only after the owner confirms the responsive candidate.

## Acceptance criteria
- [x] Clicking a card adds it after the canvas rather than opening a floating dialog.
- [x] Filters lead into the canvas without displacing it.
- [x] Hairline separators resize surfaces without framed workspace windows.
- [x] Open card and artifact surfaces keep protected reading-size defaults and minimums.
- [x] An artifact opens farther right when space allows and otherwise continues below.
- [x] Filters, card, and artifact close by unwinding the progressive chain.
- [x] The artifact offers a reversible full-screen mode.
- [x] The URL restores the open card, artifact, and workspace composition.
- [x] The selected direction works with long documents and wide interactive prototypes.

## Comments
- 2026-08-29 @pguijas: Canvas is the center element, filters stay on the left, and the card is a right drawer. Use small dividing lines, not window-like panels; everything should resize and close.
- 2026-08-29 @pguijas: Do not open the artifact over or instead of the canvas. Each selection progresses forward: to the right when space allows, otherwise below, with a full-screen option for the artifact.
- 2026-08-29 @pguijas: Card and artifact are primary once opened; increase their default and minimum dimensions so neither starts or resizes too small.
- 2026-08-29 @pguijas: Open card and artifact surfaces can use their configured maximums by default; this viewport still leaves enough room for the kanban.

## Trail
- 2026-08-29 @codex: Stage 1 opened in an isolated worktree; comparing docked, resizable page compositions before product integration.
- 2026-08-29 @codex: owner fixed the page grammar to filters | canvas | card; two hairline-separated variants produced and their rendered URLs verified with HTTP 200.
- 2026-08-29 @codex: condensed the rejected variants into one responsive chain, filters → canvas → card → artifact; placement moves right or below without overlays and the artifact can enter full screen.
- 2026-08-29 @codex (feat/kanban-artifact-viewer-integration): Stage 2 integrated the progressive in-flow workspace, resizable hairlines, addressable unwind, and native artifact full screen; production build and full test suite passed.
- 2026-08-29 @codex (feat/kanban-artifact-viewer-integration): raised card and artifact defaults and resize floors, preserving canvas space by delaying the four-surface row to ultra-wide viewports; full suite passed.
- 2026-08-29 @codex (feat/kanban-artifact-viewer-integration): promoted card and artifact defaults to their configured maximums and moved the responsive cuts to 1536px/2560px so the canvas keeps its protected width; full suite passed.
- 2026-08-29 @codex (0ba9b9c58): owner accepted the progressive workspace and approved its merge into release/0.3.0.
- 2026-08-30 @codex (PR #39): implementation ported into the independent Folio for Agents product; the card and artifacts moved to its standalone board.
