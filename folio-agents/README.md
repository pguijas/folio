# Folio for Agents

Folio for Agents is a repository-native meta-harness: it gives the coding
tools already working in a checkout one durable board, one operating protocol,
and reviewable artifacts without replacing those tools.

```bash
uv tool install folio-docs --with folio-agents
folio board init
folio board
```

The board is Markdown in git. `agents.yaml` points at it, `board.yaml` declares
its columns, and every file below `board/cards/` is one card. The Agents package
registers `folio board` in the shared CLI. Board commands do not invoke the Docs
builder, Node.js, a server, or an account.

Install the optional Docs integration when a Folio Docs site should publish the
board:

```bash
uv tool install folio-docs --with folio-agents
```

Folio for Agents keeps its own roadmap track, version, and release cycle. The
monorepo's root `docs.yaml` publishes that track beside Folio Docs in one site.

## License

AGPL-3.0-only. See [LICENSE](LICENSE).
