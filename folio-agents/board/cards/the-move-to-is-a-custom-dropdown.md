---
title: "The Move-to is a custom dropdown"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-18
type: feature
size: S
source: folio#feat/artifact-board-poc
assignee: claude
---

The dialog's one control is the board's last native select. Owner call:
it becomes a custom dropdown like the composer's comboboxes — the OS
menu sits oddly in the redesigned dialog, and the parked "Move-to Escape
guard is theater" follow-up dies with the select that carried it.

Agreed shape:

**The trigger.** The drawn 40px box stays byte-for-byte the reading it
is today — dot, column title, chevron — but it is a real button now
(`role="combobox"`, APG select-only pattern), no transparent select on
top.

**The panel.** Absolute under the trigger, `role="listbox"`: one row per
column — title left, `n/limit` count right, over-limit count in warning
ink. Open seeds the active row to the current column. No search row:
columns are a handful by construction.

**Keyboard and dismissal.** The composer combobox's exact cage: arrows
move, Home/End jump, Enter/Space pick, Escape closes the panel — not the
dialog — via preventDefault + stopImmediatePropagation, with the
dialog's own document listener early-returning on `defaultPrevented`.
Trigger and rows preventDefault on mousedown; focusout closes; the panel
scrolls into view. Picking calls the same `onMove(index)` and refocuses
the trigger, which survives the card's reparenting because the dialog
never unmounts it.

## Acceptance criteria
- [x] the Move-to renders as a button-combobox with a listbox panel; no `<select>` remains in `StatusField`
- [x] rows show `title` and `n/limit`, over-limit in warning ink; open lands the active row on the current column
- [x] Escape closes the panel and leaves the dialog open; the dialog's document listener early-returns on `defaultPrevented`
- [x] picking moves the card, closes the panel, keeps focus on the trigger, and the sr-only announcement still fires
- [x] the Created comparison select in the composer stays native; docs stop calling the status field a native picker
- [x] pins: combobox trigger in the aside, listbox rows, the Escape cage, the dialog's defaultPrevented return

## Trail
- 2026-08-18 @claude: carded from owner direction — the dialog's native select joins the custom-dropdown family; supersedes the parked Move-to Escape-guard follow-up.
- 2026-08-18 @claude (f54481e81): shipped: the drawn 40px box is a real combobox with a listbox of columns and their WIP counts; Escape caged with the dialog belted on defaultPrevented; live probe caught the mouse-open focus hole, fixed in both dropdown families; re-review hardened the pins
- 2026-08-27 @claude: audit: landed on this branch — StatusField is a button-combobox with a column listbox (n/limit, over-limit in warning ink, active row seeded to the current column), the Escape cage and the dialog's defaultPrevented belt both pinned by test_card_column_is_a_field_you_set; the composer's Created comparison keeps the one surviving native select
