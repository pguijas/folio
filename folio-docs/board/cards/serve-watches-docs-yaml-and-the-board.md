---
title: Serve watches docs.yaml
status: backlog
created: '2026-07-16'
tags: [core, dx]
type: feature
size: L
source: folio#feat/artifact-board-poc
---

The Docs server watches authored Python and Markdown, but a change to
`docs.yaml` still requires a manual restart. Configuration can change sources,
navigation, themes, and loaded plugins, so the correct response is a
debounced, announced full rebuild rather than pretending it is a one-page
incremental edit.

## Acceptance criteria
- [ ] Editing `docs.yaml` triggers a debounced full rebuild, announced in the output.
- [ ] The current server remains available until the rebuilt configuration is valid.
- [ ] Repeated editor writes collapse into one rebuild.

## Comments
- 2026-08-27 @claude: The board half of this card shipped via folio-serve-watches-the-board (hookspec pair watch_paths/on_watched_change), in the exact shape this card's 2026-08-20 trail agreed on. Not a duplicate to absorb: what remains is only the docs.yaml half — a debounced, announced full rebuild (measured 37s warm). The card should be retitled to "Serve watches docs.yaml" and the priority drops: the 0.4-blocking pain (editing cards 37 seconds at a time) is gone.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-20 @claude: given a shape — plugins declare what they watch; owner chose the general hook over a kanban special case
- 2026-08-30 @codex (board): narrowed to the remaining Docs configuration watcher; board watching belongs to the independent Agents product.
