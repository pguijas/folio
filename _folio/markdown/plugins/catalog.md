# Plugin Catalog

*Every plugin in the Folio package and on this site, in one place.*

Plugins arrive in three ways, and this page lists all of them: **default
plugins** ship inside Folio and wake up when their config key appears in
`docs.yaml`, **bundled opt-in plugins** ship in the same package but load
only when listed under `plugins:`, and **project plugins** are plain
Python files in your repository, loaded by path. All three go through the
same hooks.

## Default plugins

Loaded on every build, completely inert without their key. Add the key
and the plugin builds its pages. Remove it and the plugin goes inert
again. A clean build clears any route they had already written.

- **[Roadmap](/docs/plugins/roadmap)**: Product phases from docs.yaml rendered as a release timeline, with an optional standalone /roadmap page and a CLI table. Activated by the roadmap: key.

- **[Landing Page](/docs/plugins/landing)**: A public homepage in front of your docs: hero variants, CTAs, install commands, and a section catalog. Activated by the landing: key.

## Bundled, opt-in

In the package, off by default. Add the module name under `plugins:` and
it shares the exact lifecycle of the default plugins.

- **[OpenAPI](/docs/plugins/authoring#official-example-openapi)**: Add folio_docs.docs.integrations.openapi to plugins:, point openapi.sources at a spec file, and get a typed API reference page wired into the sidebar and search.

## Project plugins on this site

This site loads two plugins by file path. Both are small examples of the
`emit_assets` hook: they publish plain files without adding a docs page.
Their sources live in this repository under `docs/plugins/`.

- **[Agent Guide](https://pguijas.github.io/folio/agent-guide.md)**: Publishes agent-guide.md at the site root: a briefing you point a coding agent at, so it explains, installs, and troubleshoots Folio from this repository's facts. Source: docs/plugins/agent_guide.py.

- **[Install Script](https://pguijas.github.io/folio/install.sh)**: Publishes install.sh at the site root, so the installer is one curl away instead of a raw.githubusercontent.com one-liner. Source: docs/plugins/install_script.py.

## Loading

```yaml
# a docs.yaml that loads the Docs plugins listed above
# (the default plugins need no plugins: entry)
roadmap:
  phases: [...]
landing:
  hero: {...}

# everything else is listed, bundled and project plugins alike
plugins:
  - "folio_docs.docs.integrations.openapi"
  - "./docs/plugins/agent_guide.py"
  - "./docs/plugins/install_script.py"
```

To put your own plugin in this list, start at
[Writing Plugins](./authoring). The bundled plugins double as reference
implementations, and the two project plugins above are the short form:
one file, one hook, one published artifact.

The board publisher is owned and versioned by Folio for Agents. Install
`folio-agents[docs]` and list `folio_agents.integrations.kanban` explicitly when
a Docs site should render that product's board.
