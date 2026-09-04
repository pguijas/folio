# Plugins

*One extension point for everything Folio builds: components, data, pages, views, and CLI commands.*

Folio's plugin system is pluggy-based and released. First-party plugins ship inside Folio itself and go through the exact same hooks a third-party plugin would use — if you want to know whether the API can do something, the answer is usually "one of the bundled plugins already does it."

## What ships where

Roadmap, Kanban, and Landing Page are **default plugins**: loaded on every build, activated by a single key in `docs.yaml`, and completely inert without it. OpenAPI ships in the same package but is opt-in, so it loads only when `folio.plugins.openapi` is listed under `plugins:`. This site also loads two small project plugins of its own by file path.

All six, with what each one builds and where it lives, are listed in the [Plugin Catalog](./catalog).

## How activation works

```yaml
# docs.yaml — the default plugins need no plugins: entry
roadmap:
  phases:
    - id: "foundation"
      title: "Foundation"

kanban:
  source: board

landing:
  hero:
    headline: "Docs from source"
```

For a default plugin the config key **is** the switch: add it and the plugin builds its pages. Remove it and the plugin goes inert; the kanban plugin cleans its routes on the next build, and a clean build clears any route the others had already written. Every other plugin is listed under `plugins:` (a module name, an installed entry point, or a project-relative file path) and shares the same lifecycle, which is how the bundled OpenAPI plugin loads as well as any third-party one.

## Project plugins publish files too

A plugin does not have to render pages. The `emit_assets` hook writes into the workspace `public/` directory, and everything there passes through the static export untouched, so a small project plugin can publish a plain file at the site root.

This site does exactly that with `docs/plugins/agent_guide.py`, which writes [agent-guide.md](https://pguijas.github.io/folio/agent-guide.md): a briefing you point a coding agent at so it explains, installs, and troubleshoots Folio from this repository's facts instead of improvising. It covers the concept model, the real install commands and toolchain minimums, a set of symptom-to-command recipes, and the rule that the configuration reference is the authority on what `docs.yaml` accepts.

The guide teaches an agent to explain Folio. Operating a board is a separate protocol: [Operating a board](../kanban/agents), mirrored in the repo as `board/SKILL.md`.

## Write your own

The whole surface is documented in [Writing Plugins](./authoring): hooks, config-key ownership, typed data modules, routes, CLI commands, and failure isolation. The bundled plugins double as reference implementations: `folio/plugins/roadmap.py` for the full component + data + routes + CLI shape, `folio/plugins/landing.py` for config-key ownership, and `folio/plugins/kanban.py` for external data files.
