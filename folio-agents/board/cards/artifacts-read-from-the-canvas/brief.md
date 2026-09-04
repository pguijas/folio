# Prototype brief — reading a card's artifacts from the canvas

**These are decision prototypes.** Nothing here ships as written. They exist so
the owner can look at several answers side by side and pick one. Everything
lives in `board/cards/artifacts-read-from-the-canvas/`; do not modify anything
outside it.

## The problem

A card can attach what it produced, and the build publishes it. But reading an
artifact means leaving the board. A `doc:` artifact opens a compiled page at
`/docs/kanban/<id>/<stem>/` — full documentation chrome, sidebar, breadcrumbs,
a place in the docs tree that has nothing to do with the documentation. A
`file:` artifact opens the raw published file in a new tab. Either way the
canvas is gone: the column you were scanning, the dialog you were reading, the
filter you had typed.

The owner's direction, verbatim in spirit: artifacts must be readable from the
canvas, and card pages indexing into `/docs` is weird. These prototypes answer
the first half. A sibling note (`where-card-pages-publish.md`) answers the
second.

## What already exists (do not redesign it)

- The board at `/kanban` renders status columns; clicking a card opens a
  dialog styled as a mail: header, description, criteria, comments, trail, and
  an artifact band at the foot (tinted kind icon, label, mono target path).
- `artifacts:` entries are typed: `doc`, `file`, `pr`, `api`, `url`. A target
  inside the card's own directory gets an `href` at build time; everything
  else keeps `href: ""` and renders as a plain path, deliberately not a link.
- The board already writes its filter to the URL (`/kanban/?q=...`); state
  that survives a reload and can be pasted into a report is an established
  habit, not a novelty.
- The site is static. Nothing writes; nothing needs a server.

## Your data

`board-data.js` sets `window.BOARD` — the real board, 44 cards, converted from
the build's own generated data module. Card shape:

```js
{ id, title, description, status?, tags[], assignee[], type, size, source,
  priority, parent, blocked_by[], created, milestone,
  artifacts[{kind, target, label, href}],
  criteria[{text,done}], comments[{date,actor,text}],
  trail[{date,actor,ref,note,href}], file }
```

`reader-data.js` sets `window.READER`: a map from artifact `target` to what a
reader can show. `type: "markdown"` entries carry pre-rendered `html`;
`type: "html"` entries carry a relative iframe `src`. **An artifact whose
target has no READER entry cannot open — render it as the path it is, visibly
not a link.** That rule is real: the board holds a `doc:` into
`design/research/` and one into `docs/guide/` that nothing publishes, and a
bare `pr: 23`.

Load both with plain `<script src>` tags — **no `fetch()`**, these files open
over `file://` where fetch is blocked.

The card that matters for the demo is `the-board-reads-as-a-tree`: one
markdown artifact (a long comparison document with tables and code) and five
HTML prototypes that embed live. Make sure the whole demo path works on it.

## Non-negotiable output shape

Three files, named for your variant slug: `<slug>.html`, `<slug>.css` (linked
stylesheet), `<slug>.js` (deferred script). Opens by double-clicking the HTML.
No build step, no CDN, no external fonts, no network. Plain HTML + CSS +
vanilla JS. Works at 1440px and at 900px.

Write files in pieces — never attempt a single write longer than about 400
lines; build long files up with follow-up edits.

## Visual language — match Folio, do not invent a look

Folio reads as a technical publishing system: quiet, exact, source-driven.
Thin rules, flat surfaces, `--radius: 0` — square corners. No gradients, no
decorative shadows, no icon packs, no emoji. Body in a system sans stack,
labels and paths in mono, small uppercase mono labels with wide tracking
(`11px, letter-spacing .14em`) for metadata.

Copy these tokens verbatim:

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

Dark is first-class (toggle Auto/Light/Dark like the sibling prototypes):

```css
--background: oklch(0.130 0.007 82);
--foreground: oklch(0.920 0.007 82);
--card: oklch(0.155 0.007 82);
--muted: oklch(0.210 0.007 82);
--muted-foreground: oklch(0.680 0.007 82);
--border: oklch(0.330 0.007 82);
```

Read `../the-board-reads-as-a-tree/tree-table.html` and its CSS for the
register in practice (page head, notes panel, theme toggle), and
`../the-board-reads-as-a-tree/tree-rail-detail.js` for a detail-pane
precedent. Do not copy their layout; copy their manners.

## Required behaviour, whatever the layout

1. **The canvas is real.** Render the actual board (columns, all 44 cards)
   and open a card the way the board does. A minimal dialog is fine (title,
   metadata line, description, artifact band); the artifact band is the
   subject, so it is not minimal.
2. **A markdown artifact reads well.** Comfortable measure, working headings,
   tables, code blocks, in both themes. The comparison document is ~8k of
   rendered HTML; pagination is not required, good typography is.
3. **An HTML artifact embeds live** (iframe), with a visible way to open it
   full, in its own tab, for when embedding is not enough.
4. **A closed door looks closed.** No READER entry: the tile renders kind,
   label, and mono path, and is not clickable. Never a dead link.
5. **Walk the band.** Previous/next moves through the artifacts of the card
   being read without going back to the dialog.
6. **Esc unwinds one level at a time**: reader to card, card to board.
   Focus returns to the element that opened what you just closed.
7. **The reading position is a URL.** Opening an artifact writes it to the
   query or hash; loading that URL reopens board, card, and artifact. The
   board already does this for filters; reading joins it.
8. **Keyboard end to end**, visible focus throughout.
9. **Both themes**, via the same Auto/Light/Dark toggle as the sibling
   prototypes.

## Also required: a notes panel in the page itself

A collapsible section titled "What this variant argues" with: the
one-sentence thesis; what happens to the compiled `/docs/kanban/...` page if
this variant wins (does a deep link still need it, and as what); and what this
design is bad at — be honest, the owner is comparing, and a variant that hides
its weakness wastes the comparison.

## Rules of engagement

- Do not touch anything outside `board/cards/artifacts-read-from-the-canvas/`.
- Do not run `folio build`, start a server, or `git commit`.
- Build the whole thing: all cards render, every artifact case handled — a
  prototype with three fake cards is useless.
