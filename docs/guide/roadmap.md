# Roadmap

This page documents the official `folio.plugins.roadmap` plugin and renders the same source-defined data that powers the standalone `/roadmap/` route.

<Callout type="warning" title="Experimental feature">
  The roadmap plugin is disabled in this release while the plugin extension surface stabilizes. These notes are kept for future work and are not included in generated public docs.
</Callout>

Enable it in `docs.yaml`:

```yaml
plugins:
  - "folio.plugins.roadmap"

roadmap:
  routes:
    docs: true
    public: true
  phases:
    - id: "foundation"
      version: "0.1"
      title: "Foundation"
      status: "shipped"
      layer: "Source analysis"
      summary: "Parse Python source and docs into a static site."
      command: "folio build"
      features:
        - "Parser"
        - "Search"
```

The board is visualization-only in the browser. Change phases in `docs.yaml`, commit the file, and rebuild the site to update this view.

Internally, the plugin uses the same extension primitives available to custom plugins: it registers a `Roadmap` component, writes typed data, and creates the `/roadmap/` view with the required `folio.public` layout.

## Product Direction

Folio's public roadmap favors workflows that make generated docs easier to adopt in real projects:

- Framework guides for common Python stacks, starting with FastAPI.
- Theme presets that currently stay token-based while layout-level theme presets mature behind explicit components and plugin APIs.
- Layout-level theme work should introduce component families such as `ThemeLanding` and `ThemeDocsLayout`, selected through `docs.yaml`, MDX/frontmatter, and a component registry instead of hardcoded imports.
- Organic Editorial remains the default token preset while structural landing/docs-layout variants mature separately.
- Practical quality gates that match real projects, including documented coverage thresholds instead of a one-size-fits-all default.
