# Writing Plugins

*Extend the build pipeline with custom components, data, views, and hooks.*

**Not available in this release**

  Project plugins are not in Folio 0.3. They return with the sidecar protocol:
  a plugin is a separate process, written in any language, that `folio` starts
  for the build and talks to over NDJSON JSON-RPC on stdio. This page documents
  the hooks and primitives that surface ships with; the built-in integrations
  already run on them.

## How Plugins Work

The plugin system is built on three concepts:

1. **Hook specifications** define the extension points (what plugins can do).
2. **Hook implementations** are the handlers a plugin provides for the hooks it needs.
3. **The plugin host** inside `folio` calls those implementations at the right time during the build.

During `folio build`, the host calls `config_keys`, `configure`, `register_extensions`, `collect_docs`, `emit_assets`, and `post_build`, in that order. During `folio serve` it also watches the directories a plugin names in `watch_paths` and calls `on_watched_change` for a change under one of them.

## Available Hooks

These are the hooks called by the build pipeline. New plugins should use
`register_extensions` for UI work and data-backed views.

Every hook that reads configuration receives the resolved config: `project` (`name`, `version`, `repo`, `url`), `output_dir`, `project_dir`, and the `extra` map. `configure` gets it mutably, together with the raw `docs.yaml` mapping, and stores the plugin's normalized section in `extra` under its own key; later hooks read it back from there.

An error from `configure`, `register_extensions`, or `collect_docs` stops the build as `Plugin '<name>' failed in hook '<hook>': <message>`. An error from `emit_assets`, `on_watched_change`, or `post_build` becomes a warning with the same text plus `(skipped)`, and the build goes on.

## Extension Model

Folio keeps customization simple by using four primitives:

- **Component** — a named React export that can be exposed to MDX pages or plugin views.
- **Data** — JSON-serializable values emitted as typed frontend modules.
- **Layout** — a route shell with named slots. Views must choose a layout.
- **View** — a route composed from a layout, slot blocks, components, and data.

Plugins should prefer the extension registry over writing arbitrary files. Folio owns import generation, route placement, and build safety.

### `config_keys`

Build-wired. Declare top-level `docs.yaml` keys that belong to your plugin. Folio uses this before validation so plugin-owned configuration does not produce unknown-key warnings.
Return the key names as a list; a plugin that owns no key returns an empty one.

### `configure`

Build-wired. Read plugin-owned configuration from the raw `docs.yaml` mapping and store normalized data on `extra`. This keeps plugin data out of the core config model while making it available to later build hooks. `project_dir` is set before this hook runs, so resolve relative paths from your plugin's config against it rather than the process working directory.

### `register_extensions`

Build-wired. Register components, layouts, data modules, and views. This is the preferred hook for custom UI, plugin-owned routes, and typed frontend data.

### `collect_docs`

Build-wired. Return Markdown or MDX files that should become ordinary Folio documentation pages. Each document carries a source path and a clean relative route, for example `reports/quality.md` under the project directory published at `reports/quality`.

Folio parses the source and puts it through the same page generation, sidebar, local-image copying, link validation, search, sitemap, Markdown mirror, `llms.txt`, and incremental manifest as files under `source.docs`. A route collision with a project document or another plugin fails before either page is written. Use `emit_assets` instead for files that should be served verbatim.

An `unlisted` document keeps every surface except the sidebar: the page still compiles at its route and enters search, the sitemap, the Markdown mirror, and `llms.txt`, but never appears in the docs navigation — a folder holding only unlisted pages is hidden with it. Use it for plugin output that answers to a URL without belonging to the documentation's table of contents.

### `watch_paths` and `on_watched_change`

Serve-wired. `watch_paths` returns directories `folio serve` should watch besides the sources; a path that is not an existing directory is ignored. `on_watched_change` receives the asset builder, the changed path, and whether it was added, modified, or deleted, and returns `true` when it handled the change. The plugin registry is built once when `folio serve` starts, so this hook can rewrite pages and assets, but data modules written by `register_extensions` refresh only on the next start.

### `post_build`

Build-wired. Run actions after the build completes; the hook receives the path of the generated output directory. Common uses include copying additional assets, generating sitemaps, or running link checkers.

### `emit_assets`

Build-wired. Write generated files into the prepared site before search, dependency checks, and the static build run. Use this for generated MDX pages or public assets. Prefer `register_extensions` for typed data modules and layout-backed views.

The hook receives the asset builder, which offers these operations:

- `write_page(route, content)` -- write an MDX page into the content directory. The route is recorded as a live page automatically, so a successful `write_page` needs no separate `register_route` call.
- `page_exists(route)` -- report whether a page for the route is already on disk (for example, persisted from a prior warm build).
- `read_page(route)` / `remove_page(route)` -- read or delete a page in the content directory. Together with a marker string embedded in your generated content, these carry the warm-build contract: refresh a page only when it still carries your marker, and never touch a user-authored page at the same route.
- `list_pages(prefix)` -- routes of the pages currently on disk under a content-directory prefix. Use it when your plugin generates a variable set of pages: on a warm build, list your namespace, and remove the marker-tagged pages whose source of truth no longer exists.
- `register_route(route)` -- record a route as a live page so the link checker treats internal links to it as valid. Call this for every page your plugin owns even when you skip `write_page` because the page persists from a prior build; otherwise links to your page are flagged as broken on warm builds. Only register a route once the page is guaranteed to exist on disk -- write the page first, or confirm with `page_exists` -- because a registered route with no page passes link checking and then 404s on the deployed site.
- `read_meta(directory)` / `write_meta(directory, meta_json)` -- read and write the `_meta.ts` sidebar file for a content directory. `read_meta` returns the raw file text (an empty string when the file does not exist). Always merge your entry into the existing content instead of rewriting the file: `_meta.ts` files written by the sidebar generator contain nested object entries (folder titles, collapse state) that must be preserved.
- `copy_static_asset(relative, source)` -- copy one source file into the workspace `public/` directory at a containment-checked relative path so the static site serves it verbatim.
- `remove_static_tree(relative)` -- remove an owned subtree below `public/` before republishing it on a warm build. It refuses the public root and escaping paths.
- `emitted_routes()` -- the set of routes recorded via `write_page`/`register_route` in this build.
- `write_llm_files(llms_txt, llms_full_txt)` -- override the generated `llms.txt` / `llms-full.txt` files.

## Dividing Work Between the Build Hooks

Three hooks split a plugin's output surface, and a plugin may use more than one:

- **`register_extensions` owns everything typed and registry-managed:** components, typed data modules, layouts, and views. Folio generates the imports, the TypeScript modules, and the view routes for you, and validates names and references at registration time.
- **`collect_docs` owns Markdown and MDX source files:** Folio turns them into normal documentation pages and includes every standard generated surface.
- **`emit_assets` owns raw or programmatically generated files in the prepared site:** verbatim public assets and pages that do not exist as Markdown source files.

A typical shape: `register_extensions` registers a component and writes the typed data it renders; `collect_docs` contributes authored Markdown that uses it; `emit_assets` publishes any raw bundle the page links to. The roadmap integration pairs the first with a layout-backed view; the OpenAPI example below pairs it with programmatically generated pages.

## Official Example: Roadmap

The built-in roadmap integration shows the intended shape for plugin-owned data and generated routes. It is compiled into `folio`, and the `roadmap:` config key is what activates it — without the key the integration emits nothing:

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
      summary: "Parse source files into documentation."
      command: "folio build"
      features:
        - "Parser"
        - "Search"
```

The integration declares `roadmap` as a config key, stores normalized data under `extra["roadmap"]`, emits `lib/roadmap-data.ts` and `lib/roadmap-projects.ts`, and can generate a standalone `/roadmap/` route. The docs route (`/docs/roadmap/`) is for explanation; the public route (`/roadmap/`) is for displaying the same real data outside the docs shell.

The implementation follows the four-primitives model: it registers the `Roadmap` component, writes typed roadmap data, and declares `/roadmap/` as a `folio.public` layout-backed view.

### The dedicated-page contract

Plugins that need a standalone page should follow the grammar the roadmap
view uses, so every plugin page feels like one product:

- Declare the view on the `folio.public` layout. Its band renders the Home
  link, optional sibling cross-links (a `links` prop), the title, and an
  optional `description` — and a `narrow` prop switches the page from full
  width to a centered document column.
- Open the content with the `ViewHeaderRule` component (mono micro-label,
  hairline, metadata or controls on the right) — the rule the roadmap's
  "Releases" row uses.
- Cross-link a sibling view only after checking its route is actually
  enabled in `extra`, so a disabled integration never produces a dead
  link.

## Official Example: OpenAPI

The [OpenAPI integration](/docs/plugins/openapi) is the reference for the `register_extensions` / `emit_assets` division of labor. It is compiled into `folio`; its `openapi:` section activates it:

```yaml
openapi:
  sources:
    - path: "specs/petstore.yaml"
      title: "Petstore"
      route: "api-reference/petstore"
```

Walking through its hooks in build order:

1. **`config_keys`** declares `openapi` as a plugin-owned top-level key, so it does not trigger unknown-key warnings.
2. **`configure`** loads and normalizes each spec and stores the result under `extra["openapi"]`. Relative `path` values are resolved against the project directory, so builds work from any working directory, and a path that resolves outside the project directory fails the build.
3. **`register_extensions`** registers the `OpenApiReference` component and writes a typed data module (`lib/openapi-data.ts`) whose hand-authored TypeScript interfaces type the exported constant.
4. **`emit_assets`** writes one MDX page per source, merges a `_meta.ts` sidebar entry for it without disturbing the entries the sidebar generator wrote, and registers each route -- even when the page already exists from a prior warm build -- so internal links to the page stay valid.

## Registering components

For a single component file (or a directory of them), the [`components:` key in `docs.yaml`](/docs/configuration#components) is how a site adds its own React components — a plugin is for a component that needs data modules, layouts, views, or other hooks alongside it. A plugin registers a component from `register_extensions` with:

- `name` -- the JSX name pages use. Must be a valid JavaScript identifier.
- `import_path` -- the module path the generated import uses (for example `@/components/__folio_components/interactive-demo`).
- `export_name` -- the export to import when it differs from `name`.
- `expose_mdx` -- expose the component to MDX pages without imports (on by default).
- `source_path` -- a component source file copied into the build. Relative paths are resolved against the project directory, not the process working directory.
- `props` -- a mapping of prop names to TypeScript type strings. This is documentation metadata; it does not by itself validate props or publish the component anywhere.
- `required` -- mark the component as part of the template contract: custom templates must wire it in their `mdx-components.tsx`, and template validation fails when it is missing.
- `category` -- a free-form taxonomy label. It plays no role in the MDX component contract.
- `contract` / `source_label` -- mark the component as part of the published MDX component contract (`folioMdxComponents`); `source_label` carries the contract `source` string. Contract membership is explicit: declaring `props` alone does not add a component to the contract. A flagged plugin or config component joins the builtins in both places the contract is published: the `lib/folio-mdx-contract.ts` module written for the template, and the [`/_folio/contract.json`](#the-published-authoring-contract) file in the exported site.

After registering, a component is available in any MDX page without import statements:

```mdx
# Architecture

<ArchitectureDiagram layers={["transport", "aggregation", "model"]} />
```

### Name collisions and shadowing builtins

Registering a component whose name matches a Folio builtin (for example `Callout` or `Timeline`) is allowed: the config or plugin component shadows the builtin and the build emits a warning noting the override. Registering the same name twice from config or plugins is an error that names both origins.

## The published authoring contract

Every build writes `/_folio/contract.json` into the exported site. It answers, for this project, the three questions an agent otherwise has to guess at: which components a page may use, which top-level `docs.yaml` keys the project accepts, and which docs pages the build emitted.

Source batches refresh this contract during `folio serve`. An unchanged payload
keeps its file bytes and modification time; `generatedAt` records the last
semantic contract change, rather than every save or build invocation.

Abridged — a real build lists every component, every accepted key, and every route:

```json
{
  "folioVersion": "0.3.0-a1",
  "mdxContractVersion": "1.1",
  "generatedAt": "2026-07-28T09:12:04Z",
  "instructions": "Ignore fields you do not recognise; later Folio releases add them. mdxContractVersion versions the components list only.",
  "components": [
    {
      "name": "ParamTable",
      "required": true,
      "source": "api-reference",
      "props": {
        "args": "Array<{ name: string; type: string; default?: string; description?: string | null; href?: string }>"
      }
    }
  ],
  "configKeys": ["components", "deploy", "output", "project", "roadmap"],
  "routes": ["/docs/", "/docs/api-reference/", "/docs/plugins/authoring/"]
}
```

- `components` -- the MDX component contract for this build: the Folio builtins plus every config or plugin component flagged as `contract`. The same set Folio writes into `lib/folio-mdx-contract.ts` for the template.
- `configKeys` -- the core Folio keys unioned with the keys the active integrations claim through their `config_keys` hook. Any other top-level key warns when `docs.yaml` is read: `plugins`, `i18n` and `versions` as ignored in this release, anything else as an unknown key.
- `routes` -- the docs URLs this build emitted, integration-owned pages included.
- `instructions` -- one line, addressed to the reader: tolerate fields you do not know. Later Folio releases add fields, and a reader that rejects unknown ones breaks on the next upgrade.

Read the payload defensively. `mdxContractVersion` versions the components list, and `folioVersion` moves with every release, so neither signals a change to the envelope itself. Treat unknown fields as additions rather than errors.

The file is written during the build, from that build's configuration and active integrations, and it describes the site published next to it. Read it as a snapshot of that build, not as a view of the repository as it stands now.

Folio publishes it through the workspace `public/` directory, which the Next static export carries through unchanged, so the path is the same on every deployment: `https://<site>/_folio/contract.json`. A plugin can publish a file the same way from `emit_assets` with `copy_static_asset`.

## Publishing a plugin

Add the topic `folio-plugin` to the public repository. A plugin catalog is on the roadmap, and that topic is the only signal it will use: no listing request, no review queue, no account. Nothing indexes the topic today, so adding it now costs one click and is the whole publishing step when the catalog arrives.

Before you publish, read [Trust & Safety](/docs/plugins/trust). A plugin runs inside its users' builds, and this publishing convention carries no vetting by design.
