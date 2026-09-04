---
title: Board description renders
status: released
created: '2026-08-03'
tags: [bug, plugins]
type: bug
---

The optional Docs adapter preserves the board description from its `kanban:`
configuration and renders it on the public board. The equivalent historical
roadmap fix belongs to Folio Docs and is recorded on its own board.

## Acceptance criteria
- [x] normalize_kanban() preserves description
- [x] /kanban/ renders the configured description
- [x] regression tests cover the configure-to-register round trip

## Trail
- 2026-08-03 @claude: carded from the roadmap and kanban audit; the fix starts in this session.
- 2026-08-03 @claude (dbd563f22): both normalizers preserve the key, round-trip and public-page tests added; moved in-progress -> in-review. The rendered-page criterion closes on the next build.
- 2026-08-03 @claude (8d6dfd98b): verified on the rebuilt serve — both bands render their descriptions; last criterion closed.
- 2026-08-27 @claude: audit: fix re-verified — both normalizers keep description (roadmap.py:133-136, kanban.py:1208-1209), register_extensions reads it back into the band props (kanban.py:412-416, roadmap.py:72-74), round-trip pinned by test_kanban_configure_preserves_description and test_roadmap_plugin_configure_preserves_description; landed on this branch — in-review -> released
- 2026-08-30 @codex (board): retained the Kanban half on the Agents board; the historical roadmap half was recorded separately on the Docs board.
