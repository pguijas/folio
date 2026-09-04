---
title: A board-only site opens on the workspace
status: released
tags: [plugins, kanban]
type: feature
created: '2026-08-26'
milestone: "0.1"
---

Owner report from pguijas/kanban: the front page is "not a unique kanban
page — it is the main doc one, with two panels on both sides". Correct: the
board-only home is a docs page holding the component, so it renders inside
the docs chrome (sidebar, table of contents), while the full-bleed
workspace view lives at /kanban (the public view, layout folio.public,
workspace mode — folio/plugins/kanban.py:370-386).

Direction: on a board-only site the front page should BE the workspace.
The routing investigation decides the mechanism: the public view registered
at "/" (routes.public accepting a path?), or whatever the landing plugin
does to own the root. The docs route still needs at least one page to
build, so the stub page's role changes rather than disappears.

## Acceptance criteria
- [x] On a board-only site, / renders the workspace view: no sidebar, no table of contents, full-bleed board
- [x] /kanban keeps working (or redirects) so existing links survive
- [x] A site with real docs keeps its front page; the board stays at /kanban
- [x] folio kanban init produces this by default for the board-only case

## Trail
- 2026-08-26 @pguijas (b512db8d3): workspace front page landed: path routes, depth-aware views, truthful docs index, forwarding /kanban, init writes it
- 2026-08-27 @claude: audit: all four criteria re-verified in the repo — routes.public path view with workspace mode (folio/plugins/kanban.py:400-446), /kanban RedirectPage preserving query and hash (kanban.py:448-468, test_redirect_page_component_exists_and_preserves_query_and_hash), init writes public: "/" only for board-only sites (kanban_cli.py:603; test_kanban_cli.py:592, 653); landed on this branch — in-review -> released
