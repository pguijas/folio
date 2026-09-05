# Prototype brief — nested/decomposition views for the Folio kanban board

**These are throwaway prototypes.** Nothing here ships. They exist so the owner
can look at several answers side by side and pick one. Do not modify anything
outside `.artifacts/kanban-tree/`.

## The problem

The board (`/kanban`) renders cards in status columns. Cards can decompose into
subtasks, but nothing renders that. The owner wants a **nested table view** so a
task breaks into smaller tasks, and calls it central to how the board gets used.

## What already exists (do not redesign it)

`parent:` is a real, shipped field on every card:

- one card id, or empty
- validated at build: must be an existing id on the board, and not the card itself
- settable via `folio kanban add --parent <id>` and `folio kanban update --set parent=<id>`
- already a filter field, so `parent:some-id` filters today
- **no cycle detection beyond self-parent** — `a→b→a` passes the build, so every
  tree walk you write must be cycle-safe or it hangs the page

The real board has 36 cards and **none of them sets `parent:`**. The data file
ships an invented hierarchy so there is something to nest.

## Decided already (do not re-litigate)

- The view is **read + move**: you can see the tree, collapse and expand it, and
  move a card to another column. Moves stage locally and are then applied by
  copying `folio kanban move` commands — the site is static, it never writes.
- **Reparenting from the UI is out of scope.** Changing a card's parent stays a
  cardfile edit or a CLI call. Do not build drag-to-reparent.

## Your data

`board-data.js` sets `window.BOARD`. Load it with a plain
`` — **do not `fetch()` it**, these files are
opened over `file://` and fetch is blocked there.

```js
window.BOARD = {
  title: "Folio development",
  columns: [ { id, title, limit, cards: [ {
    id, title, description, status, statusTitle, parent,
    milestone, type, size, priority, assignee[], tags[], created,
    criteria[{text,done}], artifacts[{kind,target,label,href}],
    comments[{date,actor,text}], trail[{date,actor,ref,note}]
  } ] } ]
}
```

The hierarchy deliberately contains the cases that break naive implementations:

- **Depth 3**: `kanban-single-board-with-filters` → `the-card-dialog-reads-like-a-mail`
  → `the-dialog-renders-markdown`
- **A child in a different column than its parent**: `theme-contract-for-plugin-surfaces`
  is in Backlog, its parent `plugin-system-unification` is in In review. This is the
  case that makes "nested" and "kanban" disagree — your design has to answer it
  explicitly, not accidentally.
- 15 root cards with no children at all, which must not look broken or second-class.
- Cards with empty `milestone` / `type` / `size` / `assignee`. Do not render "—"
  noise across a whole column of blanks; decide what absent looks like.

## Non-negotiable output shape

**Three files**, all in `.artifacts/kanban-tree/`, named for your variant slug:

- `<slug>.html` — markup and the notes section
- `<slug>.css` — all styling, linked with `<link rel="stylesheet" href="<slug>.css">`
- `<slug>.js` — all behaviour, linked with ``

Relative `<link>` and `<script>` work fine over `file://`; only `fetch()` does not.

**Write them one at a time, in separate tool calls, and never attempt a single
write longer than about 400 lines.** A previous run of this task died because
agents tried to emit one enormous file in one call and the run was killed for
inactivity. Build up longer files with follow-up edits. Small, frequent writes.

- Opens correctly by double-clicking the `.html` (`file://`). No build step, no bundler.
- **No CDN, no external fonts, no network of any kind.** Use system font stacks.
  The real site uses Sora (body) and JetBrains Mono (code/labels); approximate
  with `ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif` and
  `ui-monospace, "SF Mono", Menlo, monospace`.
- Plain HTML + CSS + vanilla JS. No React, no framework.
- Works at 1440px and at 900px wide. It does not need to work on a phone.

## Visual language — match Folio, do not invent a look

Folio reads as a technical publishing system: quiet, exact, source-driven. Thin
rules, flat surfaces, **`--radius: 0` — square corners, this is not a rounded UI**.
No gradients, no shadows used as decoration, no icon packs, no emoji.

Copy these tokens verbatim and use `oklch()` directly:

```css
:root {
  --background: oklch(0.966 0.008 82);
  --foreground: oklch(0.155 0.007 82);
  --card: oklch(0.976 0.007 82);
  --muted: oklch(0.920 0.007 82);
  --muted-foreground: oklch(0.420 0.007 82);
  --accent: oklch(0.875 0.026 110);
  --border: oklch(0.740 0.007 82);
  --primary: oklch(0.155 0.007 82);
  --destructive: oklch(0.55 0.20 28);
  --warning: oklch(0.470 0.110 78);
}
```

Dark mode is first-class — support it with `prefers-color-scheme` or a toggle:

```css
--background: oklch(0.130 0.007 82);
--foreground: oklch(0.920 0.007 82);
--card: oklch(0.155 0.007 82);
--muted: oklch(0.210 0.007 82);
--muted-foreground: oklch(0.680 0.007 82);
--border: oklch(0.330 0.007 82);
```

Existing register worth carrying: small uppercase mono labels with wide tracking
(`font-mono, 11px, letter-spacing .14em`) for metadata like `FEATURE · PLUGIN
PLATFORM · 0.3`; the card title in semibold sans at normal size; counts as
`13/3` when a WIP limit is exceeded (and that overflow reads in `--destructive`).
Read `template/components/kanban-board.tsx` for the incumbent card face before
you design yours. The raw NUL byte discovered during this comparison has since
been replaced, so ordinary text tools read the file normally.

## Required behaviour, whatever the layout

1. **Collapse / expand** a parent, and a way to collapse or expand everything.
2. **Filter** by a text query over title and id, live. Filtering a tree has a real
   decision in it: when a child matches and its parent does not, does the parent
   stay as context, or does the child rise to the root? Pick one, make it look
   deliberate, and say which you picked in your notes.
3. **Move a card to another column**, staged locally, with a visible count of
   staged moves and a way to see the resulting `folio kanban move <id> <column>`
   commands. Staging must survive collapse/expand and filtering.
4. **Progress**: a parent's children carry status. Show how much of a parent is
   done, in whatever form your design argues for.
5. **Keyboard**: arrow keys or tab move between rows, and collapse/expand is
   reachable without a mouse. Visible focus.

## Also required: a notes panel in the page itself

At the top or in a collapsible footer, a short section titled "What this variant
argues" with:

- the one-sentence thesis of this layout;
- how you answered the cross-column child;
- how you answered tree filtering;
- what this design is bad at (be honest — the owner is comparing, and a variant
  that hides its weakness wastes the comparison).

## Rules of engagement

- Do not touch `template/`, `folio/`, `board/`, `docs/`, or `tests/`.
- Do not run `folio build` or start a server.
- Do not `git commit`.
- Build the whole thing. A prototype with three fake rows is useless; render all
  35 cards from the real data.
