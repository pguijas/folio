---
title: Plugin Authoring
---

# Plugins

*Extend the build pipeline with custom components, data, views, and hooks.*

Plugins are enabled by default: list them under the `plugins:` key in `docs.yaml` and folio loads them for every build.

## How Plugins Work

The plugin system is built on three concepts:

1. **Hook specifications** define the extension points (what plugins can do).
2. **Hook implementations** are functions you write that match a hook specification.
3. **The plugin manager** discovers and calls your implementations at the right time during the build.

When folio loads your plugin, it scans the module for functions decorated with `@hookimpl` and calls them at the appropriate stage of the build. During `folio build`, the same loaded plugin manager is used for config-key discovery, config normalization, document collection, extension registration, asset emission, and post-build hooks.

<HookMap
  hooks={[
    { stage: "Config keys", hook: "config_keys", description: "Declare plugin-owned top-level docs.yaml keys before validation." },
    { stage: "Configure", hook: "configure", description: "Normalize raw plugin config and store data on config.extra." },
    { stage: "Collect docs", hook: "collect_docs", description: "Add Markdown sources to Folio's normal page pipeline." },
    { stage: "Register UI", hook: "register_extensions", description: "Register components, typed data modules, layouts, and generated views." },
    { stage: "Emit assets", hook: "emit_assets", description: "Write generated files into the prepared site before the frontend build." },
    { stage: "Post-build", hook: "post_build", description: "Run after the static output directory is written." },
    { stage: "CLI", hook: "register_cli", description: "Add plugin-owned commands to the folio CLI application." },
  ]}
/>

## Available Hooks

These are the hooks called by the current build pipeline. New plugins should use
`register_extensions` for UI work and data-backed views.

Typed plugins can import the public boundary types from Folio:

```python
from folio.extensions import ExtensionRegistry
from folio.plugin import AssetBuilder, ConfigKeyNames, PluginConfig, PluginDocument, RawConfig
```

`PluginConfig` exposes `project_name`, `version`, `output_dir`, `project_dir`, and the mutable `extra` mapping where plugins store their normalized configuration.

## Extension Model

Folio keeps customization simple by using four primitives:

- **Component** — a named React export that can be exposed to MDX pages or plugin views.
- **Data** — JSON-serializable values emitted as typed frontend modules.
- **Layout** — a route shell with named slots. Views must choose a layout.
- **View** — a route composed from a layout, slot blocks, components, and data.

Plugins should prefer the extension registry over writing arbitrary files. Folio owns import generation, route placement, and build safety.

### `config_keys`

```python
def config_keys(self) -> ConfigKeyNames
```

Build-wired. Declare top-level `docs.yaml` keys that belong to your plugin. Folio uses this before validation so plugin-owned configuration does not produce unknown-key warnings.
Return a list or tuple of key names; a single string is rejected because it is ambiguous.

### `configure`

```python
def configure(self, config: PluginConfig, raw_config: RawConfig) -> None
```

Build-wired. Read plugin-owned configuration from `raw_config` and store normalized data on `config.extra`. This keeps plugin data out of the core config model while making it available to later build hooks. `config.project_dir` is set before this hook runs, so resolve relative paths from your plugin's config against it rather than the process working directory.

### `register_extensions`

```python
def register_extensions(self, registry: ExtensionRegistry, config: PluginConfig) -> None
```

Build-wired. Register components, layouts, data modules, and views. This is the preferred hook for custom UI, plugin-owned routes, and typed frontend data.

### `collect_docs`

```python
def collect_docs(self, config: PluginConfig) -> Iterable[PluginDocument]
```

Build-wired. Return Markdown or MDX files that should become ordinary Folio documentation pages. Each `PluginDocument` carries a source `Path` and a clean relative route:

```python
from pathlib import Path

from folio.plugin import PluginDocument, hookimpl

@hookimpl
def collect_docs(config):
    return [
        PluginDocument(
            source=Path(config.project_dir) / "reports" / "quality.md",
            route="reports/quality",
        )
    ]
```

Folio parses the source and puts it through the same page generation, sidebar, local-image copying, link validation, search, sitemap, Markdown mirror, `llms.txt`, and incremental manifest as files under `source.docs`. A route collision with a project document or another plugin fails before either page is written. Use `emit_assets` instead for files that should be served verbatim.

`PluginDocument(..., unlisted=True)` keeps every surface except the sidebar: the page still compiles at its route and enters search, the sitemap, the Markdown mirror, and `llms.txt`, but never appears in the docs navigation — a folder holding only unlisted pages is hidden with it. For plugin output that answers to a URL without belonging to the documentation's table of contents; the kanban plugin publishes card documents this way.

### `register_components`

```python
def register_components(self, registry: ExtensionRegistry) -> None
```

Build-wired compatibility hook for older MDX-only component plugins. It receives the same extension registry as `register_extensions`; prefer `register_extensions` in new plugins so components, data, layouts, and views are registered in one place.

### `post_build`

```python
def post_build(self, site_dir: str) -> None
```

Build-wired. Run actions after the build completes. The `site_dir` parameter is the path to the generated output directory. Common uses include copying additional assets, generating sitemaps, or running link checkers.

### `emit_assets`

```python
def emit_assets(self, builder: AssetBuilder, config: PluginConfig) -> None
```

Build-wired. Write generated files into the prepared site before search, dependency checks, and the static build run. Use this for generated MDX pages or public assets. Prefer `register_extensions` for typed data modules and layout-backed views.

The `builder` implements the `AssetBuilder` protocol:

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

### `register_cli`

```python
def register_cli(self, app: object) -> None
```

Add plugin-owned commands to the folio CLI. `app` is the `typer.Typer` application; add commands with `@app.command(...)`. This is the hookspec first-party plugins use for their commands (the roadmap plugin registers `folio roadmap` through it), and it is dispatched for project plugins too.

The hook runs when the CLI starts up, before command-line arguments are parsed. Because the command table is finalized at startup, project plugins listed in `docs.yaml` contribute CLI commands only when you run `folio` from inside the project directory (where `docs.yaml` is resolvable from the current working directory). Running from outside the project still loads project plugins for build hooks; only their extra CLI commands need the project cwd. A plugin that fails during `register_cli` is skipped with a warning -- it never takes down the CLI.

<Callout type="info" title="Postponed annotations sharp edge">
  Type annotations on a command defined inside `register_cli` are evaluated against the plugin module's globals when the command runs. Under `from __future__ import annotations`, any name used in a command signature (for example `Path`) must be imported at the top of the plugin module -- importing it only inside `register_cli` fails at dispatch time with a `NameError`.
</Callout>

## Dividing Work Between the Build Hooks

Three hooks split a plugin's output surface, and a plugin may use more than one:

- **`register_extensions` owns everything typed and registry-managed:** components, typed data modules, layouts, and views. Folio generates the imports, the TypeScript modules, and the view routes for you, and validates names and references at registration time.
- **`collect_docs` owns Markdown and MDX source files:** Folio turns them into normal documentation pages and includes every standard generated surface.
- **`emit_assets` owns raw or programmatically generated files in the prepared site:** verbatim public assets and pages that do not exist as Markdown source files.

A typical shape: `register_extensions` registers a component and writes the typed data it renders; `collect_docs` contributes authored Markdown that uses it; `emit_assets` publishes any raw bundle the page links to. The kanban plugin uses all three, on the same extension primitives available to any custom plugin: it registers a `KanbanBoard` component, writes typed data to `lib/kanban-data.ts`, and creates the `/kanban/` view with the required `folio.public` layout. See the OpenAPI example below for programmatically generated pages.

## Writing a Plugin

A plugin is a Python module or class that implements one or more hooks. Here is a step-by-step guide.

### Step 1: Import the hook decorator

```python
from folio.plugin import hookimpl
```

### Step 2: Write your hook implementations

You can write plugins as either a class or a plain module. Both approaches work equally well.

**Class-based plugin:**

```python
from folio.extensions import ExtensionRegistry
from folio.plugin import PluginConfig, hookimpl

class MyPlugin:
    @hookimpl
    def post_build(self, site_dir: str) -> None:
        print(f"Build complete! Output at: {site_dir}")

    @hookimpl
    def register_extensions(self, registry: ExtensionRegistry, config: PluginConfig) -> None:
        registry.register_component(
            "MyCustomCard",
            import_path="@/components/__folio_components/custom-card",
            source_path="docs/components/custom-card.tsx",
        )
```

**Module-based plugin:**

```python
from folio.plugin import hookimpl

@hookimpl
def post_build(site_dir: str) -> None:
    print(f"Build complete! Output at: {site_dir}")
```

### Step 3: Register the plugin in your config

Add the plugin to the `plugins` list in `docs.yaml`:

```yaml
plugins:
  - "my_plugin_package"
```

First-party default plugins (currently `folio.plugins.roadmap`, `folio.plugins.kanban`, and `folio.plugins.landing`) are loaded automatically before any `plugins:` entries and do not need to be listed; listing one anyway is harmless because default plugins are deduplicated against explicit entries. Default plugins stay inert until their config key (for example `roadmap:`, `kanban:`, or `landing:`) appears in `docs.yaml`.

## Official Example: Roadmap

The first-party roadmap plugin shows the intended shape for plugin-owned data, CLI behavior, and generated routes. It is a **default plugin**: Folio loads it on every build without a `plugins:` entry (listing it explicitly is deduplicated, not an error), and the `roadmap:` config key is what activates it — without the key the plugin emits nothing:

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

The plugin declares `roadmap` as a config key, stores normalized data under `config.extra["roadmap"]`, emits `lib/roadmap-data.ts`, and can generate a standalone `/roadmap/` route. The docs route (`/docs/roadmap/`) is for explanation; the public route (`/roadmap/`) is for displaying the same real data outside the docs shell.

The implementation follows the four-primitives model: it registers the `Roadmap` component, writes typed roadmap data, and declares `/roadmap/` as a `folio.public` layout-backed view.

### The dedicated-page contract

Plugins that need a standalone page should follow the grammar the first-party
roadmap and kanban views share, so every plugin page feels like one product:

- Declare the view on the `folio.public` layout. Its band renders the Home
  link, optional sibling cross-links (`props={"links": [...]}`), the title,
  and an optional `description` — and `props={"narrow": True}` switches the
  page from board width to a centered document column.
- Open the content with the `ViewHeaderRule` component (mono micro-label,
  hairline, metadata or controls on the right) — the rule the roadmap's
  "Release track" row and the board's "Board" row both use.
- Cross-link a sibling view only after checking its route is actually
  enabled in `config.extra`, so a disabled plugin never produces a dead
  link.

## Official Example: OpenAPI

The first-party OpenAPI plugin is the reference for the `register_extensions` / `emit_assets` division of labor:

```yaml
plugins:
  - "folio.plugins.openapi"

openapi:
  sources:
    - path: "specs/petstore.yaml"
      title: "Petstore"
      route: "api-reference/petstore"
```

Walking through its hooks in build order:

1. **`config_keys`** declares `openapi` as a plugin-owned top-level key, so it does not trigger unknown-key warnings.
2. **`configure`** loads and normalizes each spec and stores the result under `config.extra["openapi"]`. Relative `path` values are resolved against the project directory, so builds work from any working directory.
3. **`register_extensions`** registers the `OpenApiReference` component and writes a typed data module (`lib/openapi-data.ts`). The `type_source` parameter of `registry.write_data_module` carries the hand-authored TypeScript interfaces, and `type_annotation` types the exported constant.
4. **`emit_assets`** writes one MDX page per source, merges a `_meta.ts` sidebar entry for it without disturbing the entries the sidebar generator wrote, and registers each route -- even when the page already exists from a prior warm build -- so internal links to the page stay valid.

## Registering Plugins

There are two ways to specify a plugin in `docs.yaml`:

### Module path

Use a dotted Python module path. The module must be importable from the environment where you run folio (i.e., it needs to be installed or on `PYTHONPATH`).

```yaml
plugins:
  - "my_plugin_package"
  - "my_plugin_package.extras"
```

### File path

Use a relative file path starting with `./` to load a plugin directly from a file. In CLI commands, the path is resolved from the active project directory, either the current directory, the positional directory argument, or `--project-dir`; when using `load_config()` directly, it is resolved from the directory containing the config file.

```yaml
plugins:
  - "./plugins/my_plugin.py"
```

**Security note:** File paths must resolve to a location within the plugin base directory. Paths that resolve outside that directory are rejected with a `ValueError`.

## Example: Post-Build Hook

This plugin copies a `CNAME` file into the output directory after every build, which is useful for GitHub Pages custom domains:

```python
# plugins/github_pages.py
import shutil
from pathlib import Path
from folio.plugin import hookimpl

@hookimpl
def post_build(site_dir: str) -> None:
    cname_src = Path("CNAME")
    if cname_src.exists():
        shutil.copy2(cname_src, Path(site_dir) / "CNAME")
        print(f"Copied CNAME to {site_dir}")
```

Register it in `docs.yaml`:

```yaml
plugins:
  - "./plugins/github_pages.py"
```

## Example: Custom Components

Register a custom React component for use in your documentation. For a single component file (or a directory of them), the [`components:` key in `docs.yaml`](../configuration#components) is lighter than a plugin — reach for a plugin when the component needs data modules, layouts, views, or other hooks alongside it.

```python
# plugins/components.py
from folio.extensions import ExtensionRegistry
from folio.plugin import PluginConfig, hookimpl

@hookimpl
def register_extensions(registry: ExtensionRegistry, config: PluginConfig) -> None:
    registry.register_component(
        "InteractiveDemo",
        import_path="@/components/__folio_components/interactive-demo",
        source_path="docs/components/interactive-demo.tsx",
    )
    registry.register_component(
        "ArchitectureDiagram",
        import_path="@/components/__folio_components/architecture-diagram",
        source_path="docs/components/architecture-diagram.tsx",
    )
```

After registering, these components are available in any MDX page without import statements:

```mdx
# Architecture

<ArchitectureDiagram layers={["transport", "aggregation", "model"]} />
```

### `register_component` parameters

- `name` -- the JSX name pages use. Must be a valid JavaScript identifier.
- `import_path` -- the module path the generated import uses (for example `@/components/__folio_components/interactive-demo`).
- `export_name` -- the export to import when it differs from `name`.
- `expose_mdx` -- expose the component to MDX pages without imports (default `True`).
- `source_path` -- a component source file copied into the build. Relative paths are resolved against the project directory, not the process working directory.
- `props` -- a mapping of prop names to TypeScript type strings. This is documentation metadata; it does not by itself validate props or publish the component anywhere.
- `required` -- mark the component as part of the template contract: custom templates must wire it in their `mdx-components.tsx`, and template validation fails when it is missing.
- `category` -- a free-form taxonomy label. It plays no role in the MDX component contract.
- `contract` / `source_label` -- mark the component as part of the published MDX component contract (`folioMdxComponents`); `source_label` carries the contract `source` string. Contract membership is explicit: declaring `props` alone does not add a component to the contract. A flagged plugin or config component joins the builtins in both places the contract is published: the `lib/folio-mdx-contract.ts` module written for the template, and the [`/_folio/contract.json`](#the-published-authoring-contract) file in the exported site.

### Name collisions and shadowing builtins

Registering a component whose name matches a Folio builtin (for example `Callout` or `Timeline`) is allowed: the config or plugin component shadows the builtin and folio emits a `UserWarning` noting the override. Registering the same name twice from config or plugins is still an error -- the second registration raises a `ValueError` that names both origins.

## The published authoring contract

Every build writes `/_folio/contract.json` into the exported site. It answers, for this project, the three questions an agent otherwise has to guess at: which components a page may use, which top-level `docs.yaml` keys the project accepts, and which docs pages the build emitted.

Abridged — a real build lists every component, every accepted key, and every route:

```json
{
  "folioVersion": "0.3.0",
  "mdxContractVersion": "1.0",
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

- `components` -- the MDX component contract for this build: the Folio builtins plus every config or plugin component registered with `contract=True`. The same set Folio writes into `lib/folio-mdx-contract.ts` for the template.
- `configKeys` -- the core Folio keys unioned with the keys the loaded plugins claim through their `config_keys` hook. Anything outside this list produces an unknown-key warning when `docs.yaml` is read.
- `routes` -- the docs URLs this build emitted, plugin-owned pages included.
- `instructions` -- one line, addressed to the reader: tolerate fields you do not know. Later Folio releases add fields, and a reader that rejects unknown ones breaks on the next upgrade.

Read the payload defensively. `mdxContractVersion` versions the components list, and `folioVersion` moves with every release, so neither signals a change to the envelope itself. Treat unknown fields as additions rather than errors.

The file is written during the build, from that build's configuration and plugin set, and it describes the site published next to it. Read it as a snapshot of that build, not as a view of the repository as it stands now.

Folio publishes it through the workspace `public/` directory, which the Next static export carries through unchanged, so the path is the same on every deployment: `https://<site>/_folio/contract.json`. Your own plugin can publish a file the same way from `emit_assets`, by writing into `Path(builder.build_dir) / "public"`.

## Error Handling

If a plugin fails to load, folio raises a `RuntimeError` with a descriptive message:

```
RuntimeError: Failed to load plugin 'my_broken_plugin': No module named 'my_broken_plugin'
```

Common causes of plugin load failures:

- **Module not found:** The Python module is not installed or not on `PYTHONPATH`. Make sure the package is installed in the same environment as folio.
- **Import error:** The plugin module has a syntax error or missing dependency.
- **Path outside project directory:** A file-path plugin (starting with `./`) resolves to a location outside the project/config directory.
- **Missing hookimpl decorator:** Functions without the `@hookimpl` decorator are ignored silently -- they won't cause an error, but they won't be called either.
- **Hookwrapper implementations:** folio dispatches hooks one implementation at a time with per-plugin failure isolation, so pluggy's `@hookimpl(hookwrapper=True)` (and `wrapper=True`) implementations are not supported. They are rejected loudly at load time rather than silently skipped.

### Hook failure policies

Hook failures during a build are isolated per plugin and attributed to the plugin under the name you used in `plugins:`. Two policies apply:

- **Fail fast** (`configure`, `collect_docs`, `register_components`, `register_extensions`): the first failing plugin aborts the build with `Plugin '<name>' failed in hook '<hook>': <error>`. These hooks shape configuration, source ownership, and the registry, where continuing would silently corrupt output.
- **Warn and skip** (`config_keys`, `emit_assets`, `post_build`, `register_cli`): a failing plugin is reported as a warning and skipped, and the build continues with the remaining plugins.

## Plugin Discovery via Entry Points

Installed packages can expose plugins through the `folio` entry-point group:

```toml
# pyproject.toml of the plugin package
[project.entry-points.folio]
my_plugin = "my_plugin_package.plugin"
```

Entry-point plugins are strictly opt-in: installing a package never activates its plugin. List the entry-point name in `plugins:` to load it:

```yaml
plugins:
  - "my_plugin"
```

Resolution rules for a name in `plugins:`:

- The name is first matched against installed `folio` entry points; only when no entry point matches is it imported as a dotted module path.
- If a name matches both an installed entry point and an importable module, the entry point wins and folio emits a `UserWarning` naming the distribution that shadowed the module.
- If multiple installed distributions declare the same entry-point name, the alphabetically first distribution wins (deterministically) and a `UserWarning` names all contenders.

## Declaring a Plugin API Version

The Python hook API is versioned independently of the emitted MDX component contract; the current host version is `1.1`. A plugin can declare the API version it targets with a module-level (or class-level) constant:

```python
FOLIO_PLUGIN_API = "1.1"
```

- Accepted forms are `"1"`, `"1.0"`, and `"1.0.0"` -- a missing minor defaults to `0`, and any patch component is ignored. A bare integer (`FOLIO_PLUGIN_API = 1`) also works.
- A missing declaration is allowed; the plugin loads without a version check.
- A different major version refuses to load the plugin with a `ValueError`.
- A newer minor than the host emits a warning but still loads the plugin.

## Publishing a plugin

A Folio plugin is an ordinary Python distribution. There is no `folio-plugin.toml`, no submission form, and no registry account: the packaging metadata is the manifest.

### Step 1: Declare the entry point

The name on the left of the `=` is literally the string a user pastes into `plugins:`, so choose it as carefully as you would choose the distribution name:

```toml
# pyproject.toml of the plugin distribution
[project.entry-points.folio]
petstore = "petstore_folio.plugin"
```

```yaml
# docs.yaml of a project that uses it
plugins:
  - "petstore"
```

Installing the distribution does not activate the plugin; only the `plugins:` entry does.

### Step 2: Add the `folio-plugin` GitHub topic

Add the topic `folio-plugin` to the public repository. A plugin catalog is on the roadmap (Ecosystem, 1.0), and that topic is the only signal it will use: no listing request, no review queue, no account. Nothing indexes the topic today, so adding it now costs one click and is the whole publishing step when the catalog arrives.

### Step 3: Optionally declare catalog metadata

A `[tool.folio.plugin]` table lets a catalog entry be built from the distribution itself instead of a hand-maintained list. Folio reads none of it during a build, and every field is optional:

```toml
[tool.folio.plugin]
requires_folio = ">=0.2.1"
summary = "API reference pages from an OpenAPI spec."
docs = "https://example.com/petstore-folio"
config_keys = ["petstore"]
```

- `requires_folio` -- a [PEP 440](https://peps.python.org/pep-0440/#version-specifiers) version specifier for the Folio versions the plugin supports. This is catalog metadata, not an install constraint: declare the real dependency in `project.dependencies` as well.
- `summary` -- one sentence, in the same register as a PyPI summary.
- `docs` -- the URL of the plugin's own documentation.
- `config_keys` -- the top-level `docs.yaml` keys the plugin owns. Keep the list in step with what your `config_keys` hook returns; it is what tells a reader which keys appear in their config because of your plugin.

Before you publish, read [Trust & Safety](./trust). A plugin runs inside its users' builds, and this publishing convention carries no vetting by design.

## Tips

- You can list as many plugins as you want. They are loaded in the order they appear in `docs.yaml`.
- Plugins that implement the same hook are all called — pluggy handles the dispatch. The order follows plugin registration order.
- Keep plugins focused. A single plugin implementing one or two hooks is easier to maintain than a monolithic one.
- Test your plugin by creating a small test project with a minimal `docs.yaml` and running `folio build -v`.
