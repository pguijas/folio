---
title: Start a board
description: Initialize and operate a repository-native board with Folio for Agents.
---

# Start a board

Folio for Agents is complete without a documentation site. The board is a set
of files in git and the CLI is its validator and editor.

```bash
uv tool install folio-docs --with folio-agents
cd your-repository
folio board init
folio board add "Ship the first release"
folio board check
```

`init` creates a `board` branch by default, switches to it, and writes:

```text
agents.yaml
board/
  board.yaml
  cards/
    read-me-first.md
    _TEMPLATE.md
  SKILL.md
```

- `agents.yaml` points the CLI at the board.
- `board.yaml` declares the columns and WIP limits.
- Each Markdown file in `cards/` is one card. Its `status` field chooses the
  column, so unrelated card moves do not contend for one YAML list.
- `SKILL.md` is the repository-owned operating protocol for coding agents.

The command refuses to overwrite an existing board, config section, or branch.
Use `--no-branch` only when planning and implementation deliberately share a
history. Use `--commit` to create the initial `board: init` commit.

## Daily use

```bash
folio board
folio board move ship-the-first-release in-progress --commit
folio board trail ship-the-first-release --note "release checks pass" --ref abc1234 --commit
folio board move ship-the-first-release done --commit
```

Run `folio board check` in CI and before pushing board changes. It checks
the same cardfile rules used by every write command.

## Optional visual canvas

The browser board is an optional integration, not part of the Agents runtime.
Install it together with Folio Docs:

```bash
uv tool install folio-docs --with folio-agents
```

Then add the integration explicitly to the Docs project's `docs.yaml`:

```yaml
plugins:
  - folio_agents.integrations.kanban

kanban:
  source: board
  routes:
    public: true
    docs: false
```

`folio serve` now exposes `/kanban/`; `folio build` includes the same
canvas in the static export. Dragging only stages moves in the browser and
exports reviewed `folio board move` commands. It never writes the
repository remotely.

When planning lives on a separate branch, point the integration at that ref.
Folio creates a detached worktree without merging the board into the code
checkout:

```yaml
kanban:
  ref: board
  sources:
    docs: folio-docs/board
    agents: folio-agents/board
  routes:
    public: true
    docs: false
```

Each `sources` key becomes an independent canvas. A local branch is used when
available; CI fetches the branch from `origin` before creating the worktree.

Continue with [Board formats](./formats), the [CLI reference](./cli), or the
[agent protocol](./agents).
