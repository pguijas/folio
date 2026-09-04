---
title: The quickstart opens on the board
status: released
tags: [plugins, kanban, cli]
type: bug
created: '2026-08-26'
milestone: "0.1"
---

Found by the first real from-scratch run on pguijas/kanban: following
start.md's five commands on a board-only repository ends on a page that
says "Welcome to the documentation", with the board tucked at /kanban.
The composition is structural, not bad luck: `folio init -y` always
configures `source.docs` and `source.python` and always writes the
`docs/index.md` stub, and `_board_home_page` abstains whenever either
source is configured or `docs/` exists (folio/plugins/kanban_cli.py:185).
The board-only front page can never trigger through the documented path.

The fix teaches the guard what `folio init -y` leaves behind: configured
Python paths count only when they exist on disk, and a docs tree whose one
page is the untouched init stub (`# <name>` + "Welcome to the
documentation.") counts as publishing nothing — the stub is replaced by
the board page and docs.yaml is not re-wired (its docs source already
points there). An edited stub, any second page, or real Python sources
keep the board at /kanban, exactly as before.

## Acceptance criteria
- [x] folio init -y followed by folio kanban init opens the site on the board
- [x] An edited stub, a second docs page, or an existing Python source path keeps the front page untouched
- [x] docs.yaml gains no duplicate source block when the stub is replaced
- [x] start.md tells the new truth in one sentence

## Trail
- 2026-08-26 @pguijas (a1c1b4b97): root cause: the front-page guard could not tell folio init's own scaffolding from a site; init stub now replaced, guards pinned
- 2026-08-26 @pguijas (63851bf7e): review round: nested stub no longer replaced, dotfiles no longer block detection; updated-verb wording adjudicated as-is
- 2026-08-27 @claude: audit: landed on this branch — stub replacement and every keep-your-front-page guard pinned by name in tests/test_kanban_cli.py (:622, :607, :663, :683, :707, :725), no duplicate docs source (kanban_cli.py:584-592), start.md:105 tells the new truth
