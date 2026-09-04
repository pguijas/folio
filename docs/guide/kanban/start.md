---
title: Start a board
description: Initialize a board with folio kanban init, understand the board branch, and publish it as a static site.
---

# Start your own board

Nothing here needs a plugin author or a documentation site. This is the
whole path to a board of your own: the shed, the thesis, the side project
nobody else will ever read.

<Steps>
  <Step title="Initialize a repository">
    ```bash
    git init
    ```

    A board lives in a repository.
  </Step>

  <Step title="Create docs.yaml">
    ```bash
    folio init -y
    ```

    Creates docs.yaml and a docs page.
  </Step>

  <Step title="Initialize the board">
    ```bash
    folio kanban init
    ```

    Creates a `board` branch, board/, and config.
  </Step>

  <Step title="Add your first card">
    ```bash
    folio kanban add "Fix the kitchen light"
    ```
  </Step>

  <Step title="Start the server">
    ```bash
    folio serve
    ```

    The board is at /kanban.
  </Step>
</Steps>

`folio kanban init` creates a **`board` branch and switches to it**, then
writes the board and its config entry:

<FileTree tree={`
board/
  board.yaml
  cards/
    read-me-first.md
    _TEMPLATE.md
  SKILL.md
docs.yaml
`} />

- `board.yaml` — the column set: Backlog, In progress with a limit of
  three, and Done. Membership is not listed there; a card's own `status`
  decides which column it is in, which is why two people editing different
  cards can never conflict in that file.
- `read-me-first.md` — one starter card that documents the format
  by being it. Delete it when you have your own.
- `_TEMPLATE.md` — the copy-me starting point for a hand-made
  card. Files starting with `_` are never cards.
- `SKILL.md` — an in-repo copy of the operating protocol, so an agent
  with the repository checked out has the protocol before it has the docs site.
- `docs.yaml` gains a `kanban:` section, published at `/kanban`. It is
  appended as text rather than round-tripped through a YAML parser, so
  comments and hand formatting in your config survive untouched.

It refuses rather than overwrites, and it refuses before writing anything: an
existing board directory, an existing `kanban:` section, an existing `board`
branch, or (unless `--no-branch` is given) no git repository at all each stop
the command with the working tree untouched. `--branch` picks another name.

<Callout type="tip" title="Why a branch">
A card moves several times a week, and none of those moves belongs between
two commits of a feature, so its own branch keeps board churn out of
`git log` on your default branch. The cost: the board is not in your working
tree on the default branch, so the build that renders it runs from the board
branch. `--no-branch` scaffolds on the current branch instead, when you want
planning and implementation in one pull request.
</Callout>

From there the board is yours and it is just files. `git add board/` and the
history of your work is your commit history, which is the whole reason the
board is a directory of Markdown rather than rows in a database. Every card
carries its own trail, so `folio kanban trail <id> --note "..."` records what
happened and when, in the file and the diff.

**A repository can be nothing but a board.** If your project has no Python and
no docs, `init` sets `public: "/"` so the site opens on the workspace view
of the board — full width, no sidebar — and writes `docs/index.md` as a
short page about the board, so the docs route has real content instead of a
second copy of it. The untouched page `folio init` scaffolds counts as no
docs: running the two commands back to back, as the steps above do, still
opens on the board, and the old `/kanban/` address forwards to the front
page with any filter intact. In a project that already publishes something,
`init` writes no page and the board sits at `/kanban` beside what is already
there.

## Publishing it

`folio serve` is enough while the board is yours alone. To put it somewhere,
the board is a page of an ordinary Folio site: `folio build` writes `_site/`,
and anything that serves static files serves it. There is no board server,
nothing to keep running.

Two things decide what you get:

```yaml
kanban:
  source: board
  routes:
    public: true       # the standalone board at /kanban; a path moves it
    docs: false        # and/or a page inside the docs tree
```

Routes are opt-out. `routes.docs` (default `true`) publishes a generated
`/docs/kanban/` page when your sources do not already contain one, and
`routes.public` (default `false`) adds the standalone board: `true` puts it
at `/kanban/`, a path puts it there instead, and `"/"` makes it the front
page. When the board lives somewhere else, `/kanban/` stays a forwarding
address, so a shared link keeps working. Turning
`routes.docs` off removes the board page but not the compiled card documents:
while any card publishes documents, `/docs/kanban/` stays resolvable as a plain
directory of the publishing cards.

`folio init` writes a GitHub Pages workflow, so a repository with a board and
that workflow publishes on every push. See [Deployment](/docs/deployment/) for
the other targets.

### From a board branch

Push the `board` branch, and the Pages workflow builds the site from it:

```bash
git push -u origin board
```

The board never builds links to whoever hosts the repository; a ref renders as
the identifier it was written as, and `git show` takes it from there.

What does open is what the board itself publishes. A card can keep a directory
beside its file, `board/cards/<id>/`: Folio compiles the Markdown and MDX in it
as documentation pages, and serves the rest as raw files under
`/_folio/kanban/<id>/`. An artifact pointing into the directory links to your
own site rather than somebody else's. See
[Card directories](/docs/kanban/formats#a-cards-directory).

There are two ways to change a published board:

1. **From a clone.** `folio kanban move`, `add`, `trail` and the rest, then
   push. This is the only path with validation: the CLI refuses an edit that
   would break the board, and `folio kanban check` is the same gate the build
   runs.
2. **From the published board itself.** Drag a card and use **Export moves**,
   then review and run the commands it gives you. The board stages the moves in
   your browser and tells you so; nothing a visitor does reaches your repository.

The published site is a static export with no server; a deployment that
accepts a change and applies it as a commit is [roadmap 0.4](/roadmap).

If the board should not be public, leave `routes.public: false` and keep it on
`folio serve` locally. A private board is still a board: the files are the
product, the site is a view of them.
