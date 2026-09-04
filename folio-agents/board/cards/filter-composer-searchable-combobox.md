---
title: "The composer selects become searchable comboboxes"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-17
type: feature
size: M
source: folio#feat/artifact-board-poc
assignee: claude
---

The composer's four value pickers (type, milestone, assignee, source) are
native selects. The owner doesn't like them: no search when a field has
many values, and the OS look sits oddly in the rail. They become one custom
combobox — no new dependency, ARIA listbox pattern, search appearing only
when it earns its row.

Agreed shape:

**The control.** A `PanelCombobox` beside the other Panel* controls in
`kanban-board.tsx`; `PanelSelect` dies. Trigger button styled like the
select it replaces (h-7, border, current value or "any", chevron),
`aria-haspopup="listbox"` and `aria-expanded`. Open: an absolute panel
under the trigger — full width, border, shadow, max-height with its own
scroll, scrolled into view so it never hides under the rail's fold.
Options: **any** first (clears), then the board's values with
`value — count` in board order, and a typed value the board does not have
still drawn as an extra option. The active option is highlighted and
`aria-selected`.

**The search.** At 8+ options, an input at the top of the panel filters by
case-insensitive substring; ArrowDown moves from the input into the list.
Under 8, the list is direct — no input row.

**Keyboard and dismissal.** Enter/Space/ArrowDown open. Arrows move,
Enter picks, Escape closes and returns focus to the trigger WITHOUT
closing the rail (the handler stops propagation before the rail's own
Escape listener — fixing the parked "rail selects lack the Escape guard"
follow-up). Click outside closes. Picking closes and rewrites the
expression exactly as today: the `onSelect(value | null)` contract and the
composer invariant (the expression is the only filter state) do not change.

**What stays native.** The Created comparison select (3 fixed options) and
the dialog's Move-to select (focus must survive the card reparenting). The
"now the only menu on the board" comment at the Move-to select is updated,
because it stops being true.

## Acceptance criteria
- [x] type, milestone, assignee, and source render as the custom combobox; `PanelSelect` is gone from the component
- [x] options: "any" first, then `value — count` in board order; an off-board typed value still appears; picking rewrites the expression exactly as the select did
- [x] the search input appears only at 8+ options, filters by case-insensitive substring, and ArrowDown enters the list
- [x] keyboard: Enter/Space/ArrowDown open; arrows navigate; Enter picks; Escape closes, refocuses the trigger, and does not close the rail
- [x] click outside closes; the open panel has max-height, its own scroll, and scrolls into view on open
- [x] ARIA: `aria-haspopup="listbox"`, `aria-expanded`, `aria-selected` on the active option, the field label announced
- [x] the Created and Move-to selects stay native; the "only menu on the board" comment is rewritten
- [x] a pure `filterOptions(values, query)` helper is executed by the node harness; structure/ARIA string pins cover the rest
- [x] compact miniatures and the SSR export render exactly as before

## Comments
- 2026-08-27 @claude: Criterion 7 half-holds by supersession: Created is still a native select (kanban-board.tsx:1554), but Move-to was later converted to the same combobox pattern (2966-2980) — deliberate follow-on work, and the "only menu on the board" comment it demanded rewriting is gone with it. Recorded so the tick is not read as "Move-to is native today".

## Trail
- 2026-08-17 @claude: carded from owner direction — the native selects don't please; custom combobox with search at 8+ options; design approved in session.
- 2026-08-17 @claude (9ff993995): shipped: the four pickers are one custom combobox — search at 8+ values, opens on the current value, Escape and focus caged properly after the final review caught the delegation trap
- 2026-08-27 @claude: audit: PanelCombobox verified end to end (kanban-board.tsx:851-1149), filterOptions executed by the node harness (test_kanban_filter_language.py:403), structure pinned by test_the_composer_selects_are_searchable_comboboxes; Move-to later joined the combobox family (kanban-board.tsx:2969), superseding the stays-native clause; landed on this branch
