---
title: The board takes the name and absorbs the roadmap
status: released
tags: [plugins, kanban, core]
created: '2026-08-28'
milestone: "0.2"
type: plan
size: S
assignee: claude
artifacts:
  - doc: panel-verdict.md
    label: Panel verdict
---

Decision card. The kanban plugin renames to **board** and the roadmap
plugin folds into it: one git-backed store, several views. Milestones
move out of `docs.yaml` into board data (a phase moving next → active
becomes a commit with history), `/roadmap` stays as a view of that
registry with its own visibility toggle, `folio roadmap` survives as a
command, a registry with zero cards is legal, and **kanban** demotes to
the name of the column view.

The name was chosen by a five-agent panel (three naming lenses, a merge
assessor, an adversary with kill authority) and confirmed by the owner
the same day: "folio board, ok, incluye el roadmap no?". `board` emerged
independently from all three lenses; the full option analysis, the kill
list, and the recorded counterarguments live in the panel verdict.

One rule travels with the name: the product today does not orchestrate
agents, so orchestration lives in the description sentence, never in the
noun, until `agents-claim-and-orchestrate` ships something real.

## Acceptance criteria
- [x] The merge question weighed with options and a firm verdict (merge with preserved surfaces), counterarguments recorded
- [x] The name attacked from three lenses with a kill list and a ranked top five
- [x] The winner is coherent with the merge (one store, several views) and with the 0.4 text "the roadmap reads from the board"
- [x] The owner confirmed the pick
- [x] Implementation carded separately: folio-board-the-rename-and-the-merge

## Trail
- 2026-08-28 @claude: panel ran (5 agents), adversary bet board, owner confirmed "folio board, ok, incluye el roadmap"; implementation carded, sequencing question recorded there
