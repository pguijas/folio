---
title: "The card dialog reads like a mail"
status: released
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-18
type: feature
size: M
source: folio#feat/artifact-board-poc
assignee: claude
artifacts:
  - url: https://github.com/pguijas/folio/blob/feat/split-docs-and-agents/folio-agents/docs/board/index.md
    label: Board guide — the dialog section
---

The dialog opens on `board/cards/<id>.md` — a mono file path presiding
over the strip that should identify the card — while the artifacts, the
one thing a card produces, sit as grey chips at the bottom of the rail.
The owner wants the hierarchy inverted, designed over HTML mockups in
session: the card reads like a mail, attachments at the foot.

Agreed shape:

**The header.** The title presides, `Esc` / a pen icon-button (edit) /
the close button at the right edge, all three 28px tall. The path leaves
the header and becomes the `Card` field in the rail — still the link,
now with the file glyph, sitting with the other facts.

**The attachments band.** A full-width strip under the body grid, above
the footer: `Artifacts · N` with a paperclip, then one tile per artifact
— a kind-tinted icon square (doc blue, pr green, url warm, api gold,
file ink), the label, and the full target in mono. A dashed ghost tile
teaches the gesture: `folio kanban attach <id> --doc <path>`, shown
whenever moves are live; with no artifacts the band is the ghost alone.
`ArtifactChip` dies.

**Colour and marks.** Section labels get their small glyphs (check for
criteria, clock for trail, paperclip for artifacts), tags take a soft
accent tint, and the status value carries a column dot. Priority keeps
its existing ends-of-the-scale treatment. The footer keeps only the
staged-move export line; editing lives in the header now.

## Acceptance criteria
- [ ] the dialog header carries the title with Esc, edit pen, and close at one height; the path renders as the linked `Card` field in the rail
- [x] artifacts render as a full-width band at the dialog's foot: kind-tinted icon tiles with label and mono target; `ArtifactChip` is gone
- [x] the band teaches `folio kanban attach <id> --doc <path>` when moves are live, and renders the ghost alone when the card has no artifacts
- [ ] the footer carries only the staged-move export line; static exports keep the edit pen in the header
- [x] docs stop claiming the header shows the path and describe the attachment band
- [x] component pins cover: title in header, Card field link, ArtifactTile, the attach hint, and the footer condition

## Comments
- 2026-08-27 @claude: Audit 2026-08-27: criteria 1 and 4 are superseded, not unmet. The edit pen was removed after this card shipped (it opened the repository host's web editor — the wrong place; tests/test_kanban_plugin.py:1074-1076 now pins PenGlyph absent) and the Card field is deliberately plain text, not a link (:1078-1082 pins no card.fileHref anchor). The load-bearing halves of both criteria — title presides with Esc/close at one height, path lives in the rail, footer carries only the staged-move line — are all shipped and pinned. Reword the two clauses or accept them as superseded.

## Trail
- 2026-08-18 @claude: carded from owner direction — dialog oriented to attaching artifacts, designed over HTML mockups iterated in session (title presides, mail-style attachment band, kind colours).
- 2026-08-18 @claude (1895a736c): shipped: title presides the header with Esc/pen/close, the path is the rail's linked Card field, artifacts close the dialog as a mail-style band (kind-tinted tiles + attach ghost on cardfile boards); review wave fixed labelled-PR numbers, band scroll, and the missing pins; docs + screenshot regenerated
- 2026-08-27 @claude: audit: landed on this branch — title/Esc/close header, Card field in the rail, ArtifactTile band with attach ghost, single-condition footer, docs describe the band; pinned by test_the_card_dialog_names_its_column_once, test_the_card_dialog_attaches_artifacts_like_a_mail, test_card_dialog_prints_the_command_it_will_export
