---
title: The comboboxes share one escape cage
status: ideas
tags: [plugins, kanban]
created: '2026-08-27'
type: chore
milestone: "0.2"
---

kanban-board.tsx:1022-1023 claims the extraction of the two comboboxes'
shared cage is a carded follow-up — this is that card. Today StatusField
and PanelCombobox each carry their own copy of the Escape/refocus cage,
and the Space-picks drift caught between the two copies is exactly the
divergence a shared component would have prevented.

## Acceptance criteria
- [ ] One cage component owns open/close, Escape, and refocus for both comboboxes
