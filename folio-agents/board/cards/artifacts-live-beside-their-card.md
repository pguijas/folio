---
title: "Artifacts live beside their card"
status: released
priority: high
milestone: "0.1"
tags: [plugins, kanban]
created: 2026-08-20
type: feature
size: L
source: folio#feat/artifact-board-poc
---

A card can name what it produced, and now it can open it — for one kind of
target, in one place.

Two halves were broken. The link-out went first: `_resolve_repo_hrefs` was
deleted, so a `doc:` or `file:` target renders as the path it was written as
and nothing 404s. The second half was that a validated path is still only a
path — printing where a file is is not reaching it. That is closed for a card's
own directory: `board/cards/<id>/` is published verbatim at
`/_folio/kanban/<id>/`, and an artifact pointing into it is a link. The epic
`the-board-reads-as-a-tree` runs on it, six artifacts, all opening.

What remains is everything else the shape implies. `artifacts:` is still a
hand-maintained list of paths rather than a reading of the directory, and each
entry repeats the directory it is already in. A `doc:` pointing at a real
documentation page — `docs/guide/plugins/kanban/index.md` is attached to a card
today — stays unlinked even though the site publishes exactly that page. And
one card carries a `doc:` into `design/research/`, which no source publishes at
all, so the promise "a `doc:` artifact renders as a site page" is still not
true in general.

The docs side already solved this and the board never adopted it. A
documentation page keeps its assets as siblings and writes
`![alt](./kanban-card.png)`; `copy_page_asset` carries the file into the
content tree at the same relative path the author wrote. The comment on that
function states the stakes: without it the build does not lose the image, it
fails. The result is that one string works in the repository, in an editor, and
on the site.

Agreed shape:

**A card is a file until it needs to be a directory.** Two shapes could carry
that; B is what shipped:

```
A: the card moves in            B: the card stays put
board/cards/                    board/cards/
  agpl-license-position.md        agpl-license-position.md
  the-board-reads-as-a-tree/      the-board-reads-as-a-tree.md
    card.md                       the-board-reads-as-a-tree/
    prototypes-compared.md          prototypes-compared.md
    tree-table.html                 tree-table.html
```

A is one directory per card, unambiguous, and the entry point is `card.md` —
chosen over `index.md`/`README.md`, the docs convention, because a card
directory's entry is a card and not the index of a section, and because
`cards/*/card.md` is a trivial glob beside `cards/*.md`. B is the page-bundle
shape: the id names a file and a sibling directory, `cards/*.md` keeps finding
every card, and the loader needs no change at all.

B won on what it does not disturb. Every card on the board keeps its path, the
loader keeps its `cards/*.md` glob, and nothing that reads a card — the CLI's
line surgery, the editor's rollback, every existing test — has to learn a
second layout. A would have been a migration of 44 files to gain one property:
the directory and the card cannot drift apart. B pays for that property with a
check instead, and until that check exists the drift is real — nothing notices
a directory whose card was renamed or deleted. That is the open criterion
below, not a reason to have chosen A.

The id is the name on disk either way. Under B that is the existing rule
unchanged: the filename stem is the card id, and the directory borrows it.

**References are relative, and identical everywhere.** The body writes
`[the comparison](./prototypes-compared.md)`, and `artifacts:` writes
`tree-table.html`, not the project-relative path to it. The six entries on
`the-board-reads-as-a-tree` today repeat
`board/cards/the-board-reads-as-a-tree/` six times, and the tile prints all of
it: a card's own directory is the one place a target never needs to say where
it is. Validation resolves a sibling against the card, everything else against
the project, exactly as a markdown link already behaves.

**`.md` publishes through Folio.** Plugin API 1.1 adds `collect_docs`: a plugin
contributes a source path and route before page generation, then Folio treats
it exactly like a file under `source.docs`. A card's Markdown and MDX siblings
use that hook. They render at `<docs route>/kanban/<id>/<stem>/`, enter search,
the sitemap and `llms.txt`, get Markdown mirrors and local-image copying, and
participate in link validation and incremental cleanup. A leading `_` opts out
the way `_TEMPLATE.md` already means "not a card". Raw files still publish at
`/_folio/kanban/<id>/`, including the Markdown source needed by a bundle.

**`artifacts:` stops being a hand-maintained path list.** What sits in the
directory is that card's artifacts, derived rather than declared. The
frontmatter block survives for the things that are not files — `pr:`, `url:`,
`api:` — and for putting a label on a sibling.

**The layer over a plain bundle.** This is the shape a skill directory already
uses: a named entry point and siblings on relative paths, read on demand. The
addition is that ours is typed, validated, and published — a sibling is not
just a file an agent might open, it is a page in the site, a row in the search
index, and a line in `llms.txt`. That is the first bet in PRODUCT.md stated as
a file layout: what a session produces becomes a page instead of staying
scratch.

**Session scratch is not an artifact, and the line is drawn by hand.** The five
prototypes are attached, and the headless-browser scripts and screenshots that
verified them are not: those stayed in `.artifacts/`, outside the board,
uncommitted. The rule is whether a later reader would open it, and no
heuristic decides that — the session does, when it attaches. What the board
owes is that attaching is cheap and that nothing is attached by accident, which
is why a derived `artifacts:` reads one directory and not the tree below it.

## Acceptance criteria
- [x] Shape A or B is chosen and written down, with the reason.
- [x] Every existing card still loads unchanged.
- [x] A card's sibling directory is published, whole, with dotfiles and
      symlinks left behind, and cleared before each republish.
- [x] No repository URL is generated for a target that lives beside the card.
- [x] A non-markdown sibling is carried so relative links resolve, and is not
      rendered.
- [x] `SKILL.md` and the board guide describe the form, and stop promising a
      rendered page for artifacts that do not get one.
- [x] A card directory whose card is missing is reported, not ignored.
- [x] An artifact target may be written relative to the card, and the tile
      shows what was written.
- [x] A relative link from a card body to a sibling resolves in the repository
      and on the built site, from the same string.
- [x] A `.md` sibling renders as a page rather than being served as source, in
      the search index and in `llms.txt`; a `_`-prefixed one does not.
- [x] `artifacts:` is derived from the directory; the block remains for
      `pr:`/`url:`/`api:` and for labels.
- [x] A `doc:` target that names a published documentation page links to that
      page.
- [x] A `doc:`/`file:` target that resolves to no reachable page warns at build,
      naming the card and the path.
- [x] `folio kanban` can turn a file card into a directory card.
- [x] The card pointing at `design/research/` is correct afterwards, and the
      fate of that directory as a session-output convention is decided: it
      becomes card-local, becomes a doc source, or stays internal and unlinked.

## Comments
- 2026-08-27 @claude: Audit 2026-08-27: the eight unticked criteria are all confirmed open in code — (1) orphan card directories are silently skipped (_iter_card_files iterates known cards only, no check-time report); (2) artifact targets must still be project-relative (_owned_card_artifact resolves against project_root, kanban.py:328) and every entry on the epic repeats its directory; (3) a relative body link to a sibling renders as plain text (dialog markdown links http(s) only, kanban-board.tsx INLINE_MD); (4) artifacts: is still hand-listed frontmatter (kanban.py:1518); (5) a doc: naming a published docs page stays unlinked ('Only that directory', kanban.py:262); (6) no unreachable-target warning at build; (7) no CLI command converts a file card to a directory card; (8) kanban-single-board-with-filters still points doc: into unpublished design/research/. None of these live on the child artifacts-read-from-the-canvas, which covers only the reading half.
- 2026-08-27 @pguijas: Ruling 2026-08-27, closing the design/research question: the directory retires. Its one file, the SVAR/ReUI reference teardown, moved beside the card that cites it (kanban-single-board-with-filters, whose artifacts: entry is now a bare-name label carrier), and the recorded convention is two places, not three — session output a later reader would open is attached in the card's directory, and everything else stays untracked scratch; no repository directory holds publishable-but-unpublished documents.

## Trail
- 2026-08-20 @claude: found while attaching prototypes — every artifact resolved to a 404; owner directed the docs asset model, one abstraction level up
- 2026-08-20 @claude: repo links removed board-wide, so the 404 is gone and only reachability is left; shape B placed by hand on the epic, A vs B still open
- 2026-08-21 @claude: shape B shipped — card directories publish at /_folio/kanban/<id>/ and card-local artifacts open; markdown still served as source, artifacts: still hand-listed
- 2026-08-23 @codex (feat/artifact-board-poc): card Markdown and MDX now enter Folio's normal document pipeline; raw bundles remain intact, and ownership, symlink, collision, base-path, and warm-cleanup cases are pinned by tests
- 2026-08-24 @claude: every folder route above a published card document now resolves — a marker-tagged card index (its own index.md/README.md wins), a directory page at kanban/ when routes.docs is off, swept by marker through the new list_pages; found when /docs/kanban/<id>/ crashed the dev server under output: export
- 2026-08-29 @codex (release/0.3.0): all criteria verified on the release branch; reclassified as the 0.3 plugin/artifact pipeline it already ships with.
