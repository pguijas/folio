---
title: Sidebar order belongs to the directory
status: backlog
tags: [core, dx]
created: '2026-08-25'
type: feature
milestone: "0.3"
---

The `_DOC_PAGE_ORDER` nesting introduced with the kanban section's nested ordering is a hardcoded stopgap in the site builder. Every section's order is controlled from one central file, so plugin authors and project users cannot order their own documentation sections without modifying core code. A real per-directory ordering mechanism is needed, either through frontmatter or a `_meta`-like file convention, so each directory controls its own sidebar placement.

AGENTS.md carries a registration rule instructing agents to register pages in `_DOC_PAGE_ORDER` inside the parent entry's children list. That rule needs the general fix: once directories can declare their own order, the registration instruction can reference the mechanism instead of the hardcoded structure.

## Acceptance criteria
- [ ] A per-directory ordering mechanism is implemented via frontmatter or a meta file
- [ ] Plugins and users can control sidebar order for their own sections
- [ ] The hardcoded `_DOC_PAGE_ORDER` is removed or replaced with the general mechanism
- [ ] AGENTS.md's registration rule is updated to reference the new ordering system

## Comments
- 2026-08-27 @claude: Still real: the central order now lives in folio/generator/sidebar.py:157, not the site builder — the card body should name sidebar.py. AGENTS.md:188 still carries the registration rule this card wants generalized.
