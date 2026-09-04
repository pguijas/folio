---
title: A route move leaves warm workspaces dirty
status: backlog
tags: [core, dx]
type: bug
milestone: "0.3"
created: '2026-08-27'
---

When a plugin's document routes change (the kanban guide's promotion moved
compiled card pages from `kanban/<id>/` to `kanban/cards/<id>/`), a warm
`.build/` keeps the old world's leftovers: the stale `_meta.ts` survives
after its pages were cleaned (Nextra rejects the dangling key and the build
fails), copied page assets linger, and old-route compiled pages stay because
core cleanup keys on sources, which still exist. A cold build or
`folio build --clean` is fine; the first warm build after pulling the change
is not. The plugin-side marker sweep migrates the plugin's own generated
pages across a route change — the gap is core's: cleanup should notice a
compiled page or `_meta.ts` whose route no longer maps to any source.

Found during the kanban docs promotion, 2026-08-27; CI builds cold and never
sees it, checkouts that serve warm see it exactly once per route change.

## Acceptance criteria
- [ ] A warm build across a plugin route change completes without `--clean`
- [ ] Stale `_meta.ts` files and copied assets are swept with their pages
- [ ] A test moves a route in a warm workspace and builds twice
- [ ] A deleted or renamed card leaves no ghost directory: a warm workspace never keeps a `_meta.ts` whose source card is gone

## Trail
- 2026-08-28 @claude: second instance, different trigger — not a route move but card deletion/rename (folio-serve-accepts-board-edits git-mv'd, a-published-board-syncs absorbed): the warm workspace kept `_meta.ts`-only ghost dirs under kanban/cards/, Nextra threw its dangling-key runtime error on the owner's live serve; cleaned by hand, root cause unchanged (cleanup never notices generated files whose source vanished)
