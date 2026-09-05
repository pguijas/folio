# Folio for Agents

Folio for Agents is a meta-harness: a harness over the coding harnesses already
working in a repository. It gives Codex, Claude Code, and other tools one shared
work surface without replacing or orchestrating them.

```bash
uv tool install folio-docs --with folio-agents
folio board init
folio board
```

## What ships today

- A cardfile board stored as `board.yaml` plus one Markdown file per card.
- A repository-owned `SKILL.md` that teaches any agent how to operate it.
- Validated commands for adding, moving, updating, commenting on, and attaching
  artifacts to cards.
- Narrow git commits that keep planning history separate from code history.

The installed Agents product contributes `folio board` to the shared CLI. Board
commands require no server or Node.js runtime and never invoke a Docs build.

## Optional Docs integration

List `folio_agents.integrations.kanban` in `docs.yaml` when a Folio Docs site
should publish the board. This build integration remains explicit even though
the installed Agents product automatically contributes its CLI command.
The integration can read a dedicated board branch through a managed worktree,
including multiple product-owned boards as separate canvases.

Continue with [the board guide](./board/) or its
[agent protocol](./board/agents).
