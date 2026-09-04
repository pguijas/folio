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
again: the kanban plugin cleans its routes on the next build, and a
clean build clears any route the others had already written.

<CardGrid columns={2}>
  <FeatureCard
    title="Roadmap"
    description="Product phases from docs.yaml rendered as a release timeline, with an optional standalone /roadmap page and a CLI table. Activated by the roadmap: key."
    icon="workflow"
    href="/docs/plugins/roadmap"
  />
  <FeatureCard
    title="Kanban"
    description="A git-persisted project board: one Markdown file per card, moved by commit, operated through the folio kanban CLI. Activated by the kanban: key. Big enough to hold its own section of this guide."
    icon="dashboard"
    href="/docs/kanban"
  />
  <FeatureCard
    title="Landing Page"
    description="A public homepage in front of your docs: hero variants, CTAs, install commands, and a section catalog. Activated by the landing: key."
    icon="quickstart"
    href="/docs/plugins/landing"
  />
</CardGrid>

## Bundled, opt-in

In the package, off by default. Add the module name under `plugins:` and
it shares the exact lifecycle of the default three.

<CardGrid columns={2}>
  <FeatureCard
    title="OpenAPI"
    description="Add folio.plugins.openapi to plugins:, point openapi.sources at a spec file, and get a typed API reference page wired into the sidebar and search."
    icon="api"
    href="/docs/plugins/authoring#official-example-openapi"
  />
</CardGrid>

## Project plugins on this site

This site loads two plugins by file path. Both are small examples of the
`emit_assets` hook: they publish plain files without adding a docs page.
Their sources live in this repository under `docs/plugins/`.

<CardGrid columns={2}>
  <FeatureCard
    title="Agent Guide"
    description="Publishes agent-guide.md at the site root: a briefing you point a coding agent at, so it explains, installs, and troubleshoots Folio from this repository's facts. Source: docs/plugins/agent_guide.py."
    icon="ai"
    href="https://pguijas.github.io/folio/agent-guide.md"
  />
  <FeatureCard
    title="Install Script"
    description="Publishes install.sh at the site root, so the installer is one curl away instead of a raw.githubusercontent.com one-liner. Source: docs/plugins/install_script.py."
    icon="install"
    href="https://pguijas.github.io/folio/install.sh"
  />
</CardGrid>

## Loading

```yaml
# a docs.yaml that loads every plugin listed above
# (the default plugins need no plugins: entry)
roadmap:
  phases: [...]
kanban:
  source: board
landing:
  hero: {...}

# everything else is listed, bundled and project plugins alike
plugins:
  - "folio.plugins.openapi"
  - "./docs/plugins/agent_guide.py"
  - "./docs/plugins/install_script.py"
```

To put your own plugin in this list, start at
[Writing Plugins](./authoring). The bundled plugins double as reference
implementations, and the two project plugins above are the short form:
one file, one hook, one published artifact.
