---
title: Board formats
description: The cardfile format and its complete card schema.
---

# Board formats

A board is a directory of cards. The complete card schema is documented below. The [write commands](/docs/kanban/cli) and the [agent protocol](/docs/kanban/agents) are built for this format.

## Cardfile board

Point `source:` at a **directory** and the board becomes a cardfile board, the format built for boards that agents and humans operate together through git:

```yaml
kanban:
  source: board          # a directory, not a file
```

<FileTree tree={`
board/
  board.yaml
  SKILL.md
  cards/
    _TEMPLATE.md
    ship-kanban-plugin.md
`} />

The board directory contains the column set in `board.yaml` (human-owned, changes rarely), an in-repo copy of the session protocol in `SKILL.md`, and the card files under `cards/`. Files starting with `_` are not cards.

### board.yaml

`board.yaml` holds the column set, and optionally an icon per tag:

```yaml
title: "Folio development"
icons:                   # optional; tag -> icon, worn by every card with the tag
  core: "⚙️"
columns:
  - id: backlog          # optional; defaults to the slugified title
    title: Backlog
  - title: In progress
    limit: 3             # optional WIP limit; must be a positive integer
  - title: Done
```

- `title` is optional; `kanban.title` in `docs.yaml` overrides it when both are set.
- Each column needs a `title`. `id` defaults to the slugified title. Duplicate column ids fail the build.
- `limit` must be a positive integer; an invalid value is warned about and ignored (no limit).
- `icons` maps a tag to an icon (an emoji string); a card wears the icon of its first mapped tag, on its face and in its dialog. A malformed map warns and renders nothing.
- Column order in `board.yaml` is column order on the board. Column order is also meaning: the last column is where blockers count as resolved. Unknown keys are silently ignored.

There is **no index of cards** anywhere. Column membership is derived per card from its `status` frontmatter, which is what makes cross-card merge conflicts structurally impossible.

### Card files

Every card is one Markdown file in `cards/`. The **filename stem is the card id**: a permanent lowercase slug (`ship-kanban-plugin.md` is card `ship-kanban-plugin`, forever). A filename that is not already a slug fails the build. Files whose name starts with `_` or `.` are ignored (so `_TEMPLATE.md`, editor lock files, and other stray editor files like `.goutputstream-*` never break a build), as is anything that is not `.md`.

Machine state lives in the frontmatter, prose in the body:

```markdown
---
title: "Ship kanban plugin"
status: in-progress               # a column id; this IS the column membership
priority: high                    # low | normal | high
parent: plugins-epic              # optional; must be a card id on the board
blocked_by: [registry-refactor]   # optional; ids must exist
tags: [plugins]
assignee: pedro
size: M
source: folio#feat/board
type: bug
link: https://example.com/issues/42
created: 2026-07-10
milestone: "0.6"                  # optional; quote it (bare 0.6 is a YAML float)
order: 200                        # optional explicit rank; the ordering exception
artifacts:                        # typed attachments, one line each
  - doc: docs/research/kanban-design.md
  - file: folio/plugins/kanban.py#L80
  - pr: 23
  - url: https://example.com/spec
    label: External spec
---

The description is markdown prose before the first `##` heading.

## Acceptance criteria
- [x] board renders
- [ ] docs written

## Trail
- 2026-07-10 @pedro: card created
- 2026-07-12 @claude (abc1234): loader landed; moved to in-progress
```

### Frontmatter keys

The complete set. Required:

| Key | Rule |
| --- | --- |
| `title` | Non-empty string. Missing or empty fails the build. |
| `status` | Non-empty string; must be a column id declared in `board.yaml`. Anything else fails the build. |

Optional (a bare `key:` with no value is YAML null and treated as absent):

| Key | Rule |
| --- | --- |
| `tags` | List of strings; non-string entries are filtered, a non-list value becomes an empty list. |
| `assignee` | One name or a list: `assignee: ana` and `assignee: [ana, bo]` both work. Names are stripped; duplicates collapse. |
| `size` | The one closed vocabulary: `S`, `M`, `L`, or `XL` (any case in the file; the board shows uppercase). Anything else fails the build naming the file. |
| `source` | Where the work lives: a branch, `repo#branch`, or a URL. Free string like `type`; a URL renders as a link in the card dialog. |
| `type` | Plain string, stripped. Free vocabulary for the kind of work (`bug`, `plan`, `feature`); the types that exist are the types cards use. |
| `link` | URL string; scheme-checked like every other href in `docs.yaml`. `http(s)`, `mailto`, and relative paths are accepted; anything else, `javascript:` and `data:` included, fails the build. |
| `priority` | `low`, `normal`, or `high` (case-insensitive). Any other value warns and is treated as `normal`. |
| `order` | Numeric rank, the explicit-ordering exception. A non-numeric value warns and the card is treated as unranked. |
| `created` | ISO date `YYYY-MM-DD`, used for sorting. Any other value silently sorts last, as if the card were newest. |
| `milestone` | Free string naming the release the card belongs to (quote it in YAML). |
| `parent` | Must be an existing card id on this board, and not the card itself; otherwise the build fails. |
| `blocked_by` | Must be a list; every entry must be an existing card id and not the card itself; otherwise the build fails. A blocker is open until its card sits in the last-listed column. |
| `artifacts` | List of one-line artifact entries (below); anything malformed fails the build. |

When the config declares a versioned roadmap, a milestone matching a phase `version` lets phase pages deep-link a filtered board, and one no phase claims draws a warning, never a failure.

### Artifacts

Five kinds: `doc`, `api`, `file`, `pr`, `url`. The committed form is a one-line single-key map, with an optional sibling `label:` on any kind.

**A card with a directory does not list its files.** What sits at the top level of `board/cards/<id>/` is that card's artifact list, derived at load: one entry per regular file, sorted by name — `.md` and `.mdx` become `doc`, everything else `file`. Dotfiles, `_`-prefixed names, subdirectories, and symlinks are skipped, the same lines publishing draws. The frontmatter block remains for what is not a file, and for labels:

```yaml
artifacts:
  - doc: prototypes-compared.md      # names a sibling: this line adds the label
    label: Five layouts compared
  - doc: docs/guide/kanban/index.md
  - pr: 23
  - api: folio.plugins.kanban.normalize_kanban
  - url: https://example.com/spec
    label: External spec
```

A `doc:` or `file:` entry naming a top-level sibling — as the bare name, as `./name`, or as the full project-relative path older boards carry — attaches its label to the derived entry instead of adding a second one. Derived entries come first, name-sorted; the remaining frontmatter entries follow in written order.

**Targets read the way a markdown link reads.** A relative `doc:`/`file:` target resolves against the card's directory first, then the project root. Every artifact records what was written beside where it resolved, and the tile shows what was written: `plan.md`, not a repetition of the directory the card already stands in.

Validation is fail-fast on shape, and warns on reachability:

- Each entry must be a mapping with exactly one kind key (plus the optional `label:`); anything malformed fails the build.
- `pr:` must be a positive integer.
- `url:` targets pass the shared href scheme policy: `javascript:` and `data:` fail the build.
- `api:` targets only need to be a non-empty string; symbol existence is not validated yet.
- A `doc:`/`file:` target may carry a `#L12`-style fragment, stripped before checking. An absolute path or one escaping the project directory fails the build. One that resolves to no file **warns**, naming the card and the written target, and the tile renders unlinked — a stale path in one card is prose, not board topology.

Three kinds of artifact open. A `url:` opens because it was written as a URL; the href is recomputed at build time and never trusted from input, so it cannot smuggle a `javascript:` past the scheme policy. A `doc:` or `file:` opens when it points inside the card's own directory, described next. And a `doc:` naming a file under a `source.docs` directory opens the documentation page the site builds from it; a `doc:` whose file exists but whose page nothing publishes warns at build, because `doc:` promised a page.

Everything else renders as an unlinked tile showing its target. The board builds no URLs for whoever happens to host the repository: that assumed one host and produced a dead link for anything not committed there. Attaching a file is also not a license to publish an arbitrary part of the project.

### A card's directory

A card may keep a directory beside its markdown file, named for the card (see [the index](/docs/kanban/#the-card) for how published artifacts open):

<FileTree tree={`
board/cards/
  the-board-reads-as-a-tree.md
  the-board-reads-as-a-tree/
    prototypes-compared.md
    tree-table.html
    tree-table.css
`} />

The card file sits beside its directory. The directory holds what the card produced — and its top level **is** the card's artifact list, derived as described above, so putting a file there and attaching it are one act. A label goes on in the frontmatter, by the sibling's bare name:

```yaml
artifacts:
  - file: tree-table.html
    label: Tree table (chosen)
```

The build owns every file in that directory. Markdown and MDX become Folio pages under the configured docs route; other files are served verbatim at `/_folio/kanban/<card-id>/`. A derived artifact therefore is a link the reader can follow.

The rules are short:

- **The whole directory is published, not only what `artifacts` names.** The files reference each other, and a page without its stylesheet opens as nothing.
- **Markdown and MDX are compiled by Folio.** `report.md` becomes `<docs route>/kanban/cards/<card-id>/report/`, with the project theme, search entry, sitemap entry, Markdown mirror, `llms.txt` entry, link validation, local-image copying, and incremental rebuild tracking. A leading `_` opts out of compilation.
- **Compiled pages stay out of the docs sidebar.** A card's output answers to its URL and stays findable through search, the sitemap, `llms.txt`, and the Markdown mirror; the sidebar is the documentation's own table of contents, and board working papers are not part of it.
- **Every folder route above a document resolves.** Compiled documents sit below `<docs route>/kanban/cards/<card-id>/`, and readers reach those URLs by trimming a longer one or from a breadcrumb, so none of them 404s.
  - An `index.md` or `README.md` in a folder (the card's directory or any subdirectory) becomes that folder's page.
  - A folder that ships neither gets a generated index: the card's status line and first paragraph, then one tile per document and per attached artifact. A published prototype opens; an unpublished target stays an unlinked tile.
  - The generated page carries the plugin's marker and steps aside: for a card-authored index the moment one appears, for a documentation page of yours that already owns the folder's URL, and entirely when the documents are gone.
  - `<docs route>/kanban/cards/` itself resolves to a directory of the publishing cards while anything publishes.
  - With `routes.docs: false` the parent resolves too: `<docs route>/kanban/` forwards to the public board, query and hash intact. A board published nowhere gets a directory of the cards that publish documents instead of the board page the configuration turned off.
- **Everything else stays a raw bundle.** HTML, CSS, JavaScript, images, and the original source files are copied under `/_folio/kanban/<card-id>/` without rewriting, so an HTML prototype keeps loading its sibling assets.
- **Dotfiles and dot-directories stay behind.** `.verify/`, `.cache/` and friends are session scratch by convention.
- **Ownership is exact.** An artifact cannot use `../` to claim another card's directory.
- **Symlinks are refused, not followed.** That includes the card directory itself and files below it, so a link out of the project cannot publish a file the project does not contain.
- **The top level is the band on the card.** Only the directory's top level derives artifacts; a subdirectory still publishes (a prototype keeps its assets) but is not listed, so curation is placement.
- **A directory whose card is missing is reported.** The filename stem names the directory; a card renamed or deleted leaves its directory orphaned and unpublished, and the build and `folio kanban check` warn, naming it.
- **Nothing else about the card changes.** The card is still `board/cards/<id>.md`, still found by the same glob, and a card without a directory is unaffected.

What belongs in a card directory and what does not is a session convention, not a build rule: [What a session leaves behind](/docs/kanban/agents#what-a-session-leaves-behind).

### Body structure

- **Description** — everything before the first `##` heading.
- **`## Acceptance criteria`** — bullet lines of the form `- [ ] text` or `- [x] text` become checkboxes. Lines that do not match are silently skipped.
- **`## Trail`** — one line per work session, oldest first, matching this grammar:

```
- YYYY-MM-DD @actor (ref): note
```

The `(ref)`, a commit sha or `PR #n`, is optional. The reader is tolerant: a line that misses the grammar warns at build time and still renders as an ordinary note (whose inline markdown renders like any other, per the dialog section). The writer (`folio kanban trail`) is strict: the date must be `YYYY-MM-DD`, the actor a single token, the ref free of parentheses and newlines, the note non-empty.

A ref renders as the identifier it was written as, in mono, and the board builds no link from it. A sha is already an address and `git show` takes it; guessing which host would answer for it is how the board ended up printing dead links.

This is also the reason `artifacts` has no `commit` kind and does not need one. Git is the source of output history, and a ref that has already been written down once should not have to be written twice.

- **`## Comments`** — the card's conversation, one line per comment, the trail's grammar minus the ref:

```
- YYYY-MM-DD @actor: text
```

The trail records what happened; comments argue about it. Same tolerance contract: a line that misses the grammar warns at build time and still joins the thread as prose. The writer (`folio kanban comment`) is strict: date, single-token author, non-empty text with whitespace collapsed. The dialog draws the thread as its own band above the artifacts.

## Ordering inside a column

Cards sort deterministically by `(has-rank, rank, priority, created, id)`:

1. Cards with a numeric `order` come first, sorted by rank ascending.
2. Unranked cards follow, by priority (`high`, `normal`, `low`),
3. then by `created` date (older first; missing or malformed dates last),
4. then by id, lexicographically.

`order` is the rare explicit-ordering exception; everything else is computed, so reordering never has to touch another card's file.

## Validation

The contract: a typo in a note must never break a build; a typo in board topology must never silently ship a wrong board. `folio kanban check` and `folio build` apply exactly the same rules.

**Fails the build** (and `check` exits 1):

- `board.yaml` missing, unparseable, or without a `columns:` list
- a column without a title
- duplicate column ids
- a missing `cards/` directory
- a card filename that is not a slug
- missing, unparseable, or non-mapping frontmatter
- a missing `title` or `status`
- a `status` that is not a column id
- a `size` that is not `S`, `M`, `L`, or `XL`
- a dangling or self-referential `parent`
- a `blocked_by` that is not a list, or that contains a dangling or self-referential id
- an `artifacts` value that is not a list
- a malformed artifact entry
- a non-positive `pr:` number
- a `doc:` or `file:` path that is absolute or escapes the project directory
- a `url:` artifact or a card `link` failing the href scheme policy

**Warns only** (build and `check` succeed):

- a column over its WIP limit
- an invalid `limit` value in `board.yaml` (ignored)
- a trail line that misses the grammar (kept, rendered as plain text)
- an unknown `priority` (treated as `normal`)
- a non-numeric `order` (treated as unranked)
- a milestone no roadmap phase claims (only when the config declares a versioned roadmap)
- a `doc:` or `file:` target that resolves to no file (the tile renders unlinked)
- a `doc:` whose file exists but whose page nothing publishes (build only — `check` runs without the site's source configuration)
- a card directory whose card is missing (nothing publishes it)

## Migrating to cards

A board is a directory of cards. If your board lives in one block of YAML written by hand — a `columns:` list with `cards:` under it, in `docs.yaml` or a file of its own — turning it into cards is mechanical:

1. Create a directory (`board/`) with a `board.yaml` holding only your `columns:` list (titles, ids, limits); delete the `cards:` entries.
2. Write one `cards/<slug>.md` per card: the title and any fields into the frontmatter, the description into the body, and `status` set to the id of the column the card was in.
3. Point `kanban.source` at the directory and run `folio kanban check`.
