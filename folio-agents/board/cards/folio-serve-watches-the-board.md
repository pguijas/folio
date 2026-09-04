---
title: folio serve watches the board
status: released
tags: [plugins, kanban, core]
type: bug
created: '2026-08-26'
milestone: "0.1"
---

Found live on pguijas/kanban: with `folio serve` running, `folio kanban add`
wrote a card and thirty seconds later the served board still did not have
it — kanban-data.ts kept its startup timestamp. The watcher list is
`python_sources + doc_sources` (folio/build.py:1141-1145) and the watch
filter admits only .py/.md under those trees (folio/watcher.py:423-430);
the board directory is never watched, so every card edit during a serve
session requires a restart.

Design decision the fix carries: the watcher is generic and kanban is a
plugin, so either the plugin system grows a watch surface (a hookspec pair:
watch paths + on-change handler, which any plugin could use) or the watcher
hardcodes the kanban source dir as a special case. The handler must
re-normalize the board and re-run the plugin's emit path (kanban-data.ts,
board pages, card documents) plus the search index; board.yaml is .yaml, so
the suffix filter needs widening for the board tree.

## Acceptance criteria
- [x] A card added or edited while `folio serve` runs appears on the served board without a restart
- [x] A board.yaml column change propagates the same way
- [x] The mechanism is decided deliberately: a plugin watch surface, the hookspec pair watch_paths + on_watched_change, kanban the first implementer; the watcher stays generic

## Trail
- 2026-08-26 @pguijas (8e48ab99f): hookspec pair landed; live proof on pguijas/kanban: card added mid-serve, data regenerated in 4s, no restart; the first attempt missed the data module and the hardened test now demands it
- 2026-08-27 @claude: audit: hookspec pair (folio/plugin.py:240-247), generic dispatch and yaml-admitting filter (folio/watcher.py:52-76,470-475), kanban handler re-emits the data module (kanban.py:510-573), pinned by test_a_card_change_reloads_the_board_while_serving; landed on this branch
