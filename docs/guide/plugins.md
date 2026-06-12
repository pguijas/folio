# Plugins (Beta)

*Extend the build pipeline with custom components, data, views, and hooks.*

<Callout type="warning" title="Beta feature">
  Plugins are disabled in this release while the extension surface stabilizes. These notes are kept for future work and are not included in generated public docs.
</Callout>

## How Plugins Work

The plugin system is built on three concepts:

1. **Hook specifications** define the extension points (what plugins can do).
2. **Hook implementations** are functions you write that match a hook specification.
3. **The plugin manager** discovers and calls your implementations at the right time during the build.

When folio loads your plugin, it scans the module for functions decorated with `@hookimpl` and calls them at the appropriate stage of the build. During `folio build`, the same loaded plugin manager is used for config-key discovery, config normalization, extension registration, asset emission, and post-build hooks.

<HookMap
  hooks={[
    { stage: "Config keys", hook: "config_keys", description: "Declare plugin-owned top-level docs.yaml keys before validation." },
    { stage: "Configure", hook: "configure", description: "Normalize raw plugin config and store data on config.extra." },
    { stage: "Register UI", hook: "register_extensions", description: "Register components, typed data modules, layouts, and generated views." },
    { stage: "Emit assets", hook: "emit_assets", description: "Write generated files into the prepared site before the frontend build." },
    { stage: "Post-build", hook: "post_build", description: "Run after the static output directory is written." },
  ]}
/>

## Available Hooks

These are the hooks called by the current build pipeline. New plugins should use
`register_extensions` for UI work and data-backed views.

Typed plugins can import the public boundary types from Folio:

```python
from folio.extensions import ExtensionRegistry
from folio.plugin import AssetBuilder, ConfigKeyNames, PluginConfig, RawConfig
```

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

Build-wired. Read plugin-owned configuration from `raw_config` and store normalized data on `config.extra`. This keeps plugin data out of the core config model while making it available to later build hooks.

### `register_extensions`

```python
def register_extensions(self, registry: ExtensionRegistry, config: PluginConfig) -> None
```

Build-wired. Register components, layouts, data modules, and views. This is the preferred hook for custom UI, plugin-owned routes, and typed frontend data.

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

## Official Example: Roadmap

The first-party roadmap plugin shows the intended shape for plugin-owned data, CLI behavior, and generated routes:

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
      summary: "Parse source files into documentation."
      command: "folio build"
      features:
        - "Parser"
        - "Search"
```

The plugin declares `roadmap` as a config key, stores normalized data under `config.extra["roadmap"]`, emits `lib/roadmap-data.ts`, and can generate a standalone `/roadmap/` route. The docs route (`/docs/roadmap/`) is for explanation; the public route (`/roadmap/`) is for displaying the same real data outside the docs shell.

The implementation follows the four-primitives model: it registers the `Roadmap` component, writes typed roadmap data, and declares `/roadmap/` as a `folio.public` layout-backed view.

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

Register a custom React component for use in your documentation:

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

## Plugin Discovery via Entry Points

Entry-point-based plugin discovery (so plugins are automatically loaded when installed) is planned for a future release. Currently, all plugins must be explicitly listed in `docs.yaml`.

## Tips

- You can list as many plugins as you want. They are loaded in the order they appear in `docs.yaml`.
- Plugins that implement the same hook are all called -- pluggy handles the dispatch. The order follows plugin registration order.
- Keep plugins focused. A single plugin implementing one or two hooks is easier to maintain than a monolithic one.
- Test your plugin by creating a small test project with a minimal `docs.yaml` and running `folio build -v`.
