# Roadmap

The official `folio.plugins.roadmap` plugin renders source-defined phases as a release timeline; the view below is powered by the same data as the standalone `/roadmap/` route.

The roadmap plugin ships with Folio as a first-party default plugin: it is loaded on every build, with no `plugins:` entry and no environment variable required. It stays inert until a `roadmap:` section appears in `docs.yaml` — the config key is the activation switch.

Activate it in `docs.yaml`:

```yaml
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

The timeline is rendered from source: change phases in `docs.yaml`, commit the file, and rebuild the site to update this view.

Routes are opt-out: `routes.docs` (default `true`) publishes a generated `/docs/roadmap/` page when your sources do not already contain one, and `routes.public` (default `false`) adds the standalone `/roadmap/` page. The `folio roadmap` CLI command prints the configured phases as a table.

Listing `folio.plugins.roadmap` under `plugins:` is harmless — default plugins are deduplicated against explicit entries — but unnecessary.

Internally, the plugin uses the same extension primitives available to custom plugins: it registers a `Roadmap` component, writes typed data, and creates the `/roadmap/` view with the required `folio.public` layout.

## Live demo

This is Folio's own roadmap — the code tab shows the shape of the `roadmap:` section in this repository's `docs.yaml`, the preview tab is the component rendering the real data:

<PreviewCode title="Folio's release track" defaultMode="preview">

```yaml
roadmap:
  routes:
    docs: false        # this guide page owns the docs demo
    public: true       # standalone /roadmap
  phases:
    - id: "foundation"
      version: "0.1"
      title: "Foundation"
      status: "shipped"          # shipped | active | next | later
      layer: "Source analysis"
      summary: "Parse Python source into a documented site."
      command: "folio build"
      features: ["Parser", "API reference pages"]
    # ... one entry per phase
```

<Roadmap />

</PreviewCode>
