# Kanban reference teardown — SVAR React Kanban and ReUI Kanban

Researched 2026-08-04 for the board redesign. Both libraries were read at the
source, not the marketing page. The question was narrow: what should folio's
board take, and should it take a dependency.

## What they are

**SVAR React Kanban** (`@svar-ui/react-kanban`) — a widget from XB Software,
the shop behind the SVAR suite (Gantt, DataGrid, Calendar). The free edition
is MIT; a separately sold PRO build adds undo/redo, export, and lazy column
loading. The React port is very new: one published version (2.6.0, June 2026),
14 GitHub stars, no issue history. The battle-tested original is the Svelte
package. Note the package name `wx-react-kanban` does not exist; that was the
pre-rename scope.

**ReUI Kanban** (reui.io, Keenthemes) — not an npm package but a shadcn-style
copy-paste registry: `npx shadcn@latest add @reui/kanban` drops a ~950-line
MIT file into your components directory. Built on dnd-kit v6
(`@dnd-kit/core` + `/sortable` + `/utilities`). The kanban is in the free
tier; the polished "Kanban Board" blocks are paid.

## Styles

**SVAR** ships compiled CSS with two entry points (12 KB kanban-only,
108 KB for the full widget suite). Theming is 224 `--wx-*` custom properties
supplied by a `<Willow>` / `<WillowDark>` wrapper, plus ~20 kanban-specific
tokens (`--wx-kanban-column-bg`, `--wx-kanban-drop-placeholder-bg`,
`--wx-kanban-priority-high-bg`…). Semantic class names are documented as
stable (`wx-card`, `wx-column`, `wx-over-limit`, `wx-drop-placeholder`) but
every rule sits at (0,2,0) specificity behind build-generated hash classes,
so overrides need escalated selectors. The default skin: Open Sans 14px, 3px
card radius, sky-blue primary, hairline column headers — closer to a 2019
Trello than to current Jira or Linear. Dark mode changes the brand hue from
blue to violet.

**ReUI** is almost unstyled by design: the component carries layout classes
only (`grid auto-rows-fr gap-4 sm:grid-cols-3`, `flex flex-col gap-2`,
opacity and cursor states). All visual identity comes from the surrounding
shadcn Card/Badge/Avatar. Its default "nova" style is `rounded-xl`, a 1px
**ring** rather than a border (`ring-1 ring-foreground/10`), padding driven by
a `--card-spacing` variable, and no shadow anywhere. Every structural node
carries `data-slot`, plus `data-dragging`, `data-disabled`, `data-value` —
clean CSS hooks that let a theme restyle the board without touching source.

Neither skin is a starting point for folio: proposal.html is sharp corners,
flat cards on 1px borders, recessed lanes, no foreign hues. The anatomy
underneath is what is worth reading.

## Functionality worth naming

SVAR has the deeper feature set: named store actions with an `intercept()`
veto seam, a card editor with `placement="sidebar" | "modal" | "inline"`,
filters as a `Map<string, predicate>` where each entry is removable by tag,
regrouping by any field via `columnAccessor` as a `{get, set}` pair, WIP
limits that tint the column, column collapse to a rail, card and column
virtualization, and a REST data provider.

ReUI is a drag layer plus layout, and honest about it: no filtering, no
search, no selection, no card detail, no WIP limits. What it does carry is
the right persistence API — `onValueChange` for live preview and
`onValueCommit(value, meta)` firing once per completed drag with
`meta.previousValue`, built for optimistic update and rollback — plus
sensor constraints tuned so cards stay clickable (10px mouse distance,
250ms touch long-press).

Two defects in ReUI worth recording because they are patterns to avoid, both
verified in its source: card keyboard drag is broken as shipped (the item
spreads dnd-kit's `attributes` while the handle spreads `listeners`, so a
keydown on the focused item never reaches the activator), and the column
drag handle is `opacity-0` until hover with no `focus-visible` counterpart,
so a keyboard user can focus an invisible control.

## Dependency verdict: keep the hand-rolled drag

Do not adopt either as a dependency.

1. The problem people reach for dnd-kit to solve is not a drag problem.
   Our drag breaks under filtering because a drag source is a
   `{columnIndex, cardIndex}` pair resolved against the visible board, not
   because HTML5 drag-and-drop is inadequate. dnd-kit fixes it as a side
   effect of being id-keyed; so does refactoring to a card id, which our own
   export path (`folio kanban move <id> <column>`) already speaks.
2. Sortable's core value is unusable here. Intra-column order is computed by
   the Python loader and the CLI writes only `status:`; column order lives in
   a committed `board.yaml` with no command to rewrite it. Both reorder
   gestures would be theatre.
3. The keyboard argument does not survive contact — see the ReUI defect
   above. Our explicit move buttons are more discoverable for a four-column
   board; they only lack an announcement.
4. Touch is the one genuine gap (HTML5 drag does not fire on touch), and it
   does not need a library: SVAR's pointer-event implementation is a ~200-line
   recipe we can own.
5. ReUI pins dnd-kit v6, the legacy line; the maintainer's rewrite is a
   separate package. Adopting v6 today buys a migration tomorrow, in a file
   folio redistributes to every user.

SVAR as a dependency is worse: 14 runtime dependencies including an 833 KB
core, for a 27-card board, in a template every folio user carries.

## What to take

Ordered by user value. None of these needs a dependency.

1. **Address cards by id, not by index.** The root cause of our worst
   limitation: because a drag source is a pair of array indices resolved
   against the visible board, we disable drag and the move buttons whenever a
   filter is active. Filtering a board and then moving what you found is the
   most natural thing a user does, and today it is forbidden. The same defect
   lets the open dialog re-point at a different card, since the selection is
   also an index pair and the dialog has no focus trap. Fix: one uid per
   card, moves by uid, and the localStorage overlay becomes a
   `Record<uid, columnId>` — which also survives a baseline edit that merely
   adds a card, where today the whole overlay is discarded.
2. **A drop placeholder at the actual landing position.** Today the only drop
   feedback tints the whole target column, while the move always appends to
   the end, so a card teleports to the bottom of a long backlog. SVAR's
   in-flow placeholder is honest about the landing slot. ReUI's live reflow is
   the other honest option, but we must not copy it: we have no write-back for
   intra-column position, so a gesture implying "third from top" would lie.
3. **Move buttons visible on coarse pointers, and a real focus ring.** Our
   move buttons are hover-revealed, and HTML5 drag does not fire on touch —
   so on a phone the only way to move a card is a control that is invisible
   and still hit-testable. A `pointer-coarse` variant and a proper
   `focus-visible` outline fix both.
4. **An `aria-live` region announcing moves and filter results.** A screen
   reader user pressing the move button gets no feedback today. The best
   accessibility value per line available, and the one idea worth taking from
   dnd-kit without taking dnd-kit.
5. **Undo the last move.** Our only escape from a mis-drop is "Reset to
   source", which discards every staged move. One snapshot per mutation turns
   a destructive control into a recoverable one. Take the idea from ReUI's
   `previousValue` snapshot, not from SVAR, whose undo is PRO.
6. **Filters as a facet record with predicates.** Our filter function takes
   three positional arguments and is called from eight sites; every new facet
   edits all of them. SVAR's per-tag predicate map extends to assignee,
   priority, or blocked-by without touching the call sites, and matches the
   removable token pills the redesign already specifies.
7. **`data-slot` attributes on every structural node.** Folio ships this
   component into users' repositories, and "Theme contract for plugin
   surfaces" is a live backlog card whose whole point is that themes must
   restyle plugin pages without forking them. Right now the only styling seam
   is editing the component. ReUI gets this right for about eight attributes.

## Bigger ideas, each needing its own card

- **Pointer-event drag** replacing HTML5 drag, for touch support. SVAR's
  implementation is the recipe: 4px threshold, `touch-action: none`, a fixed
  ghost preserving the measured size and grab offset, `elementFromPoint` hit
  testing, a suppressed synthetic click on drop, Escape to cancel.
- **Group the board by a field other than status.** SVAR's `columnAccessor`
  `{get, set}` pair is the best structural idea in either library: the same
  cards regroup by milestone or assignee, with `set` writing the field back on
  drop. Blocked on a write path — `folio kanban move` only writes `status:`.
- **Column collapse to a rail.** Our backlog holds two thirds of the cards
  while two columns are empty, so density is genuinely lopsided.
- **Named actions with an interceptor seam.** Every mutation as a named,
  typed action with one place to observe and one to veto. It would let WIP
  limits stop being purely advisory, and give the export path, the undo
  stack, the announcer, and the overlay a single seam.

## What to reject outright

In-browser card creation and editing (SVAR's editor, add-card, context menu):
it contradicts the file-backed board by design. Card files are hand-authored
Markdown that a YAML round-trip would destroy, which is why every mutation is
verified line surgery run by the CLI in the repo. The browser captures intent
and exports commands; that boundary is the product, not a limitation. Also
rejected: the REST provider and dynamic loading (no server), virtualization
(27 cards, and it breaks in-page find), drag-to-reorder within a column or
between columns (no honest destination), and either default skin.

## Licensing

Both are MIT with no copyleft and no attribution banner, so ideas and
techniques carry no obligation. Copying code verbatim does carry the notice
requirement, and this template is redistributed into users' repositories where
it currently has zero third-party notices — so for anything taken, write it
against our own data model rather than pasting. SVAR PRO is out of bounds:
the licence forbids SaaS and permits redistribution only "as long as it
doesn't compete with SVAR", which is a live risk for a product whose model is
redistributing a template.
