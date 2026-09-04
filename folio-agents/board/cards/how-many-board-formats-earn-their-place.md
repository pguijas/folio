---
title: How many board formats earn their place
status: released
tags: [plugins, kanban]
type: task
created: '2026-08-25'
artifacts:
  - file: board/cards/how-many-board-formats-earn-their-place/board-formats-debate.html
    label: The four positions
milestone: "0.1"
---

The plugin ships three board declarations: inline `columns:` in docs.yaml, a
single-file `source: board.yaml`, and the cardfile directory. Only the
cardfile is operable; the other two are read-only render paths. Their code
cost is small (two branches on a shared loader, `folio/plugins/kanban.py`
1077-1157), but the surface cost is paid by every reader: a three-row
comparison table, per-page caveats that write commands need cardfile, a
migration recipe kept alive as the target of a CLI refusal, and an export
button that changes meaning between formats.

A four-seat panel argued keep-all-three, retire-the-board-file,
cardfile-only, and a no-side map of which user segment needs which format;
the exhibit beside this card lays the positions out side by side.

**Decided 2026-08-25: cardfile only.** The owner picked the third seat over
the judge's first rank: one format is the product's identity — you modify
cards as files, it is clean, and it is simple. The known costs are accepted:
the ten-line inline taste dies (`folio kanban init --no-branch` is the one
command replacing it) and a display-only board becomes a small cardfile
directory. Observed blast radius is zero: every real board is already a
cardfile.

## Acceptance criteria
- [x] A decision is recorded on this card: cardfile is the only board format
- [x] The inline `columns:` and single-file `source:` loader branches become fail-loud errors pointing at `folio kanban init` and the migration recipe
- [x] The legacy and coexistence tests retire with the branches they guard (10 retired, 20 rewritten; the CLI gained the check-matches-build refusals)
- [x] formats.md becomes a single-format page: comparison table and External board file section go, the migration recipe survives as the path in from hand YAML
- [x] cli.md refusal wording, the index non-features list, and the why-folio FAQ (`docs/guide/why-folio.md` Export YAML answer, already drifted) stop naming retired formats
- [x] The export button keeps one meaning: Export moves
- [x] Docs describe only what exists at every step of the retirement (anchor floor held at exactly 13; the generated API reference greps clean)

## Comments
- 2026-08-25 @pguijas: cardfile only. You modify cards as files, it is clean, and it is simple. The judge ranked it second; the identity argument outweighs the ten-line taste.

## Trail
- 2026-08-25 @pguijas (fc4eb2e0a): four-seat panel argued the count; judge ranks retiring the board file first; exhibit attached
- 2026-08-25 @pguijas (8495d10d7): owner decided cardfile only; criteria now carry the retirement plan
- 2026-08-26 @pguijas (eaad44466): retirement landed: loader, CLI gate, export, docs
- 2026-08-27 @claude: audit verified the retirement end to end: fail-loud loaders (folio/plugins/kanban.py:1183-1324) pinned by tests (test_kanban_plugin.py:144,152; test_kanban_cli.py:291,333), single-format formats.md keeping the migration recipe, refusal wording in cli.md:27, Export moves as the button's one meaning (kanban-board.tsx:4347), anchor floor held (test_kanban_docs.py:55)
