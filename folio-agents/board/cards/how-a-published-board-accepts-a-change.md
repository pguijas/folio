---
title: How a published board accepts a change
status: ideas
tags: [plugins, kanban]
created: '2026-08-25'
type: plan
milestone: "0.2"
source: folio#feat/artifact-board-poc
artifacts:
  - doc: board/cards/how-a-published-board-accepts-a-change/panel-verdict.md
    label: Panel verdict
---

A published board is read-only until you give it a write path. The dialog exports git commands, but those land nowhere: a GitHub Pages site has no repository to receive them. Three candidate paths exist, each with its cost and what it does to PRODUCT.md's "static forever" commitment.

The first path is a write-capable `folio serve`, a local or server-side development mode that commits changes directly. The second is opt-in repository and pull request links surfaced through the export dialog, returning the user to GitHub to apply the change. The third is an accepting deployment layer that receives exported moves and stages them as commits or pull requests. Each path addresses a different context: local work, manual review workflows, or hosted collaboration.

PRODUCT.md states "static forever" and "no server and no vendor in the serving path". If the chosen path contradicts those claims, PRODUCT.md must be amended deliberately before the feature lands. The staging area and Export moves implementation both depend on this decision.

Decided: paths one and three, as one component. An adversarial panel (three
designs, four judges — the verdict is attached) chose the write-capable
`folio serve` first: a stdlib API thread over the CLI's own operations, one
gesture one commit. The owner then directed that path three is the same
server standalone: a deployed board names its backend under `sync:` in
`docs.yaml`, and `folio kanban server` on a checkout receives the writes,
commits, and pushes. Path two (repository and pull request links) is
rejected for now. The staging area is removed, not replaced; the export
dialog goes with it. The implementation lives on one card, cut to the need:
`kanban-edits-from-the-browser`.

## Acceptance criteria
- [x] One path is chosen and recorded
- [x] PRODUCT.md is amended, or the chosen path is confirmed to preserve its current claims
- [x] The staging area's fate is decided: kept, removed, or replaced
- [x] Export moves implementation is directed or deferred
- [x] The init-stub's closing pointer is re-read against the final page set and verified (carried to kanban-edits-from-the-browser, where the final page set exists)

## Comments
- 2026-08-27 @claude: Audit 2026-08-27: two criteria verifiably open. PRODUCT.md is unamended (no commits since the decision; 'no server, no vendor in the path' at lines 15-16 and 86 stand as written) and no recorded confirmation covers the sync-backend half of the decision — the panel verdict's 'static export stays byte-identical' line confirms only the serve-integrated path. The init-stub closing pointer (board/SKILL.md's final 'kanban plugin documentation' line, kanban_cli.py:570) has not been re-read, and the final page set it must be read against waits on the staging/export removal that rides folio-serve-accepts-board-edits (backlog). The PRODUCT.md confirmation is doable now and its own body says it must land before the feature does.

## Trail
- 2026-08-26 @claude: panel verdict recorded and owner delta applied — serve write path first, configured sync backend second, PR links rejected; implementation carded on two children
