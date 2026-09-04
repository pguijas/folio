# Plugins

*One extension point for everything Folio builds: components, data, pages, views, and CLI commands.*

Folio's plugin system is pluggy-based and released. First-party plugins ship inside Folio itself and go through the exact same hooks a third-party plugin would use — if you want to know whether the API can do something, the answer is usually "one of the bundled plugins already does it."

## What ships where

Roadmap and Landing Page are **default plugins**: loaded on every build,
activated by one key in `docs.yaml`, and inert without it. OpenAPI ships in the
same package but loads only when `folio_docs.docs.integrations.openapi` is
listed under `plugins:`.

The complete set is listed in the [Plugin Catalog](./catalog).

## How activation works

```yaml
# docs.yaml — the default plugins need no plugins: entry
roadmap:
  phases:
    - id: "foundation"
      title: "Foundation"

landing:
  hero:
    headline: "Docs from source"
```

For a default plugin the config key **is** the switch: add it and the plugin
builds its pages. Every other plugin is listed under `plugins:`.

## Project plugins publish files too

A plugin does not have to render pages. The `emit_assets` hook writes into the workspace `public/` directory, and everything there passes through the static export untouched, so a small project plugin can publish a plain file at the site root.

This site does exactly that with `docs/plugins/agent_guide.py`, which writes [agent-guide.md](https://pguijas.github.io/folio/agent-guide.md): a briefing you point a coding agent at so it explains, installs, and troubleshoots Folio from this repository's facts instead of improvising. It covers the concept model, the real install commands and toolchain minimums, a set of symptom-to-command recipes, and the rule that the configuration reference is the authority on what `docs.yaml` accepts.

The board and its repository protocol belong to the independently installed
Folio for Agents product.

## Write your own

The whole surface is documented in [Writing Plugins](./authoring). The bundled
plugins double as reference implementations: `folio_docs/docs/integrations/roadmap.py`
for components, data, routes, and CLI, plus
`folio_docs/docs/integrations/landing.py` for config-key ownership.
