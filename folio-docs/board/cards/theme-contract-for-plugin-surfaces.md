---
title: Theme contract for plugin surfaces
status: backlog
created: '2026-07-16'
tags: [theming, plugins]
milestone: "0.3"
source: folio#31
---

Presets, tokens, and theme packages must restyle plugin pages (landing, boards) the same way they restyle docs pages. Today plugin surfaces can drift from the active theme; this card defines the token contract plugin pages may rely on so a theme change propagates everywhere without plugin-specific overrides.

PR #31 explored a Studio preset, full landing compositions, and example
overlays before the current theme boundary settled. Its 149-file implementation
is deleted; the reusable outcome is this small contract, rebuilt from current
tokens and proven by one maintained reference package.

## Acceptance criteria
- [ ] preset switch restyles landing, roadmap, and kanban with no plugin-specific overrides
- [ ] contract documents the token set plugin pages may rely on
- [ ] theme packages apply without forking templates

## Comments
- 2026-08-27 @claude: Re-milestoned off shipped 0.3: nothing here is started. Not release-blocking for 0.4 (Project OS), so the July high comes off; the case for keeping it near-term is that plugin surfaces multiplied on this branch (board, drawer, dialogs) and each one was styled by hand, which is exactly the drift this contract exists to stop.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-29 @codex (PR #31): stale implementation and branch deleted; the theme-system idea remains here for a focused rebuild from current main.
