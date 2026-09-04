---
title: Roadmap description renders
status: released
created: '2026-08-03'
tags: [bug, plugins]
type: bug
---

The Folio Docs roadmap integration preserves its configured description and
renders it above the public roadmap instead of emitting a bare heading.

## Acceptance criteria
- [x] normalize_roadmap() preserves description
- [x] /roadmap/ renders the configured description
- [x] regression tests cover the configure-to-register round trip

## Trail
- 2026-08-03 @claude (dbd563f22): roadmap normalization and round-trip coverage landed as part of the former mixed band-description fix.
- 2026-08-03 @claude (8d6dfd98b): verified the description on the rebuilt public roadmap.
- 2026-08-30 @codex (board): extracted the Docs history from the former cross-product card during the hard board split.
