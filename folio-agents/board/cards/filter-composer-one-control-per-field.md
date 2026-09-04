---
title: "The composer draws one control per field, and cards carry type and assignee"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-16
type: feature
---

The filter composer draws every field the same way: a column of tri-state
checkboxes. That shape is right for the two fields you scan (status,
priority) and wrong for everything else — a single-value field wants a
dropdown, an open list wants an input. And two facts a team board runs on,
who owns a card and what kind of work it is, barely exist: `assignee` is in
the format but invisible on the board, and type has no field at all.

The change, agreed with the owner (simple and plain as the rule; menu plus
data model, no browser write path):

**Data model.** `type: <value>` joins the card frontmatter — single value,
free vocabulary, the types that exist are the types cards use, exactly like
`milestone`. The loader carries it, the plugin emits it into
`lib/kanban-data.ts`, `folio kanban show` prints it, the cardfile docs
describe it. No vocabulary validation.

**The card.** The face's metadata line gains the type, and `@assignee`
shows when set; cards without them render unchanged. The dialog gains a
Type row beside the existing metadata.

**The composer.** One control per field, all derived from the parsed
expression and writing back through it — typed text and clicked controls
cannot disagree, because there is no second store. Status and priority stay
tri-state checkbox lists with predictive counts. Type, milestone, and
assignee become native selects: the board's values with counts, plus "any"
to clear the term. Tag becomes an input with the board's tags as
suggestions and removable chips; adding ORs into the tag term. Created
keeps its comparator and date. Whatever a control cannot draw (multi-value
in a select, negations, free text) stays listed as removable "Also" chips.
Fields with no values on the board do not render.

## Acceptance criteria
- [x] `type:` in frontmatter flows loader -> `lib/kanban-data.ts` -> board, prints in `folio kanban show`, and is documented in the cardfile section
- [x] the card face shows type in its metadata line and `@assignee` when set; cards without them render unchanged
- [x] the card dialog lists Type with the other metadata rows
- [x] status and priority stay tri-state checkbox lists with predictive counts
- [x] type, milestone, and assignee are single-select dropdowns of the board's values with counts, plus "any" to clear
- [x] tag is an input with suggestions and removable chips; adding a tag ORs into the tag term
- [x] every control derives from the parsed expression and rewrites it; no control holds state of its own
- [x] terms no control can draw stay as removable "Also" chips; valueless fields do not render
- [x] `type:x` filters through the expression language and the `?` reference lists it without a separate edit

## Comments
- 2026-08-27 @claude: Criterion 5 shipped as native selects (ccdc7ea07) and holds semantically today — board values with counts plus "any" — but the control is now PanelCombobox (SELECT_FIELDS at kanban-board.tsx:674, also grown to include source), upgraded by filter-composer-searchable-combobox. Deliberate supersession, recorded here so the ticked criterion is not read as "native select still exists".

## Trail
- 2026-08-16 @claude: carded from owner direction — design agreed in session: menu + data model, `type` as a free single-value field, one control per field in the composer, simplicity as the rule.
- 2026-08-16 @claude (ccdc7ea07): type field end to end (loader, data module, CLI, card, composer); composer redrawn one control per field; docs and template updated; suite green
- 2026-08-16 @claude (f202d4832): final whole-branch review: 0 critical; docs field list + composer semantics fixed, tag chips from term alternatives, dateTerm double-draw gone, rewrite helpers now executed by the language tests
- 2026-08-27 @claude: audit: type flows loader->data module->CLI->docs (test_card_type_normalizes_to_string, test_emitted_interface_carries_type, test_show_table_prints_type, formats.md:112); face, dialog and composer verified in kanban-board.tsx; landed on this branch
