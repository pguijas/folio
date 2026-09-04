---
title: "The roadmap is the milestone registry"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-17
type: feature
size: S
source: folio#feat/artifact-board-poc
assignee: claude
---

`milestone` is free text and formats.md admits the debt: "a full registry
with validation is planned, not shipped". The registry already exists —
the roadmap's phases carry `version` — and `_resolve_roadmap_phases`
already joins the two halves. What's missing is the complaint when the
join fails.

Agreed shape (owner chose warning severity):

**The rule.** When the config declares a roadmap with at least one
versioned phase, a card whose `milestone` matches no phase version gets a
warning naming the card and the known versions — surfaced yellow by
`folio kanban check`, never breaking the build. The "future milestone the
roadmap has not reached yet" case stays legal, loudly. Boards without a
roadmap section (or with no versioned phases) stay exactly as free as
today: no warning, no coupling.

**The seams.** The check lives beside `_resolve_roadmap_phases`, which
already computes `by_version` — one loop, one `warnings.warn` per
unclaimed milestone. The `v`/`V` prefix stripping it already does applies.
formats.md's milestone row drops the "planned, not shipped" confession and
states the shipped rule.

## Acceptance criteria
- [x] with a versioned roadmap, a card milestone no phase claims warns naming the card and the known versions; `folio kanban check` shows it yellow and still exits green
- [x] a claimed milestone, a board without roadmap, and a roadmap without versions all stay silent
- [x] the build never breaks over a milestone
- [x] formats.md's milestone row documents the shipped rule instead of the "planned, not shipped" note
- [x] tests cover: unclaimed warns, claimed silent, no-roadmap silent, v-prefix versions still match

## Trail
- 2026-08-17 @claude: carded from owner direction — standardize milestone against the roadmap's versions, warning severity; queued behind the combobox card.
- 2026-08-17 @claude (982eebe24): shipped: unclaimed milestones warn grouped against the roadmap's versions; check replays the resolution and shows them yellow; docs drop the planned-not-shipped note
- 2026-08-27 @claude: audit verified all five criteria: registry warning at kanban.py _resolve_roadmap_phases, check replays it yellow and exits 0 (test_check_warns_yellow_on_unclaimed_milestones_and_stays_green), formats.md:122 states the shipped rule — landed on this branch in 982eebe24
