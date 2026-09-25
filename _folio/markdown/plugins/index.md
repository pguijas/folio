# Plugins

*One extension point for everything Folio builds: components, data, pages, and views.*

Folio's built-in integrations are compiled into the `folio` binary and share one set of hooks — if you want to know whether the surface can do something, the answer is usually "one of the built-ins already does it."

## What ships where

Landing Page, Roadmap, and OpenAPI are **built-in integrations**: present in
every build, activated by their own section in `docs.yaml`, and inert without
it.

The complete set is listed in the [Plugin Catalog](/docs/plugins/catalog).

## How activation works

```yaml
# docs.yaml — each section is its integration's switch
roadmap:
  phases:
    - id: "foundation"
      version: "0.1"
      title: "Foundation"
      status: "shipped"
      layer: "Source analysis"
      summary: "Source in, documented site out."

landing:
  hero:
    headline: "Docs from source"
```

The config key **is** the switch: add it and the integration builds its
pages, remove it and the integration goes inert. There is no `plugins:` list.

A file the site serves verbatim from its root needs no integration at all:
list it under [`public:`](/docs/configuration#public). Folio's own `docs.yaml`
serves `install.sh` that way.

## Project plugins

Not available in this release. Plugins loaded from your own repository return
with the sidecar protocol: a plugin is a separate process, written in any
language, that `folio` starts for the build and talks to over stdio. The hooks
it will implement are documented in [Writing Plugins](/docs/plugins/authoring), and what
running one means for your machine in [Trust & Safety](/docs/plugins/trust).
