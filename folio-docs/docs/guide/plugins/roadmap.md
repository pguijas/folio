# Roadmap

The official `folio_docs.docs.integrations.roadmap` plugin renders source-defined phases as a release timeline; the view below is powered by the same data as the standalone `/roadmap/` route.

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
      milestone: "docs-0.1"
      project: "docs"
      title: "Foundation"
      status: "shipped"
      layer: "Source analysis"
      summary: "Parse Python source and docs into a static site."
      command: "folio build"
      features:
        - "Parser"
        - "Search"
```

The timeline is rendered from source: change phases in `docs.yaml`, commit the file, and rebuild the site to update this view. Give phases a `project` to render independent release sequences from one roadmap. A phase's optional `milestone` is the stable value cards use when two projects can both have a `0.1`.

Routes are opt-out: `routes.docs` (default `true`) publishes a generated `/docs/roadmap/` page when your sources do not already contain one, and `routes.public` (default `false`) adds the standalone `/roadmap/` page. The `folio roadmap` CLI command prints the configured phases as a table.

The optional top-level `description` is the page's own copy: the `/roadmap/`
page shows it under the title, above the releases. Releases are ordered by
version, never by status.

## Naming the projects

Give a phase a `project` and the plugin groups the roadmap by it. On the
standalone `/roadmap/` page each project becomes a card, and every card holds
that product's whole plan: the release list on the left, the release you pick
opened beside it. Projects are numbered independently, so two products that
ship separately each start at their own 0.1.

An optional `projects:` block names them. A `label` titles the card and a
`description` sits under it; without either, the project key is shown as
written.

```yaml
roadmap:
  routes:
    public: true
  projects:
    docs:
      label: "Folio Docs"
      description: "Everything that turns a repository into a published site."
    agents:
      label: "Folio for Agents"
  phases:
    - id: "foundation"
      project: "docs"
      version: "0.1"
      # ...
```

Every card is expanded by default, and each one can be collapsed to its
heading. `?product=<key>` opens one card and collapses the rest, which is the
link a product's own landing page should use:
`/roadmap/?product=agents`. A release is addressable too, scoped by project:
`/roadmap/#agents-0.2`.

Collapsing hides a card's releases; it does not drop them. Every release is in
the served HTML whatever the page is showing, so a crawler, a Markdown mirror
or a reader with JavaScript off still sees the whole roadmap.

Listing `folio_docs.docs.integrations.roadmap` under `plugins:` is harmless — default plugins are deduplicated against explicit entries — but unnecessary.

Internally, the plugin uses the same extension primitives available to custom plugins: it registers a `Roadmap` component for embedding, a `RoadmapPage` component for the standalone route, writes typed data, and creates the `/roadmap/` view with the required `folio_docs.public` layout.

## Live demo

This is Folio's own roadmap — the code tab shows the shape of the `roadmap:` section in this repository's `docs.yaml`, the preview tab is the component rendering the real data:

<PreviewCode title="Folio's release lines" defaultMode="preview">

```yaml
roadmap:
  routes:
    docs: false        # this guide page owns the docs demo
    public: true       # standalone /roadmap
  phases:
    - id: "docs-foundation"
      version: "0.1"
      milestone: "docs-0.1"
      project: "docs"
      title: "Foundation"
      status: "shipped"          # shipped | active | next | later
      layer: "Source analysis"
      summary: "Parse Python source into a documented site."
      command: "folio build"
      features: ["Parser", "API reference pages"]
    - id: "agents-context"
      version: "0.1"
      milestone: "agents-0.1"
      project: "agents"
      title: "Agent Context"
      status: "active"
      summary: "Publish grounded context for coding agents."
```

<Roadmap />

</PreviewCode>
