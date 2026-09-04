# Folio

Folio is a family of two independent open-source products:

- [Folio Docs](folio-docs/README.md) generates documentation as HTML for
  people and Markdown for agents.
- [Folio for Agents](folio-agents/README.md) is a repository-native
  framework for exchanging and managing artifacts and work.

They can be installed, versioned, and released separately. This monorepo keeps
repository policy, automation, legal files, and contributor infrastructure at
the root. Folio Docs owns the single frontend template; Folio for Agents adds
its board component through the optional integration.

Both products meet through one command. Folio Docs provides the `folio` CLI
host, and installed products add their command groups; Folio for Agents adds
`folio board`.

The repository publishes one Folio site from both products. Their roadmap
tracks and release versions stay independent inside that site:

```bash
uv run folio serve --port 4341
```

The configured kanban is read from the independent `board` branch through a
managed worktree, so the unified site includes both product canvases without
bringing planning files into the release branch.
