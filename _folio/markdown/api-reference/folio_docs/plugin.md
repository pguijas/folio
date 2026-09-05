# folio_docs.plugin 

## Classes

A Markdown source contributed to Folio's normal document pipeline.

``unlisted`` delists the page from the docs sidebar and nothing else: it
still compiles at its route and enters search, the sitemap, ``llms.txt``,
and the Markdown mirrors. For plugin output that answers to a URL without
belonging to the documentation's own table of contents.

Namespace scanned by pluggy for decorated hook implementations.

### `__dir__` 

```python
def __dir__() -> Iterable[str]
```

**Returns:** `Iterable[str]` - 

### `page_exists` 

```python
def page_exists(route: str) -> bool
```

**Returns:** `bool` - 

### `read_page` 

```python
def read_page(route: str) -> str
```

**Returns:** `str` - 

### `write_page` 

```python
def write_page(route: str, content: str) -> None
```

**Returns:** `None` - 

### `remove_page` 

```python
def remove_page(route: str) -> None
```

**Returns:** `None` - 

### `list_pages` 

```python
def list_pages(prefix: str) -> list[str]
```

**Returns:** `list[str]` - 

### `register_route` 

```python
def register_route(route: str) -> None
```

**Returns:** `None` - 

### `copy_static_asset` 

```python
def copy_static_asset(relative: str, source: Path) -> None
```

**Returns:** `None` - 

### `remove_static_tree` 

```python
def remove_static_tree(relative: str) -> None
```

**Returns:** `None` - 

### `emitted_routes` 

```python
def emitted_routes() -> set[str]
```

**Returns:** `set[str]` - 

### `write_meta` 

```python
def write_meta(directory: str, meta_json: str) -> None
```

**Returns:** `None` - 

### `read_meta` 

```python
def read_meta(directory: str) -> str
```

**Returns:** `str` - 

### `write_llm_files` 

```python
def write_llm_files(llms_txt: str | None = None, llms_full_txt: str | None = None) -> None
```

**Returns:** `None` - 

### `config_keys` 

```python
def config_keys() -> ConfigKeyNames
```

**Returns:** `ConfigKeyNames` - 

### `configure` 

```python
def configure(config: PluginConfig, raw_config: RawConfig) -> None
```

**Returns:** `None` - 

### `register_extensions` 

```python
def register_extensions(registry: ExtensionRegistry, config: PluginConfig) -> None
```

**Returns:** `None` - 

### `register_components` 

```python
def register_components(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `collect_docs` 

```python
def collect_docs(config: PluginConfig) -> Iterable[PluginDocument]
```

**Returns:** [`Iterable[PluginDocument]`](/docs/api-reference/folio_docs/plugin#plugindocument) - 

### `post_build` 

```python
def post_build(site_dir: str) -> None
```

**Returns:** `None` - 

### `emit_assets` 

```python
def emit_assets(builder: AssetBuilder, config: PluginConfig) -> None
```

**Returns:** `None` - 

### `watch_paths` 

```python
def watch_paths(config: PluginConfig) -> Iterable[str]
```

**Returns:** `Iterable[str]` - 

### `on_watched_change` 

```python
def on_watched_change(builder: AssetBuilder, config: PluginConfig, path: str, change: str) -> bool
```

**Returns:** `bool` - 

### `register_cli` 

```python
def register_cli(app: object) -> None
```

**Returns:** `None` - 

A plugin raised while a fail-fast hook was being dispatched.

Carries the user-facing plugin label and the hook name so the top-level
build error attributes the failure to the offending plugin.

### `__init__` 

```python
def __init__(plugin_label: str, hook_name: str, original: BaseException) -> None
```

**Returns:** `None` - 

### `__init__` 

```python
def __init__(base_dir: Path | None = None) -> None
```

**Returns:** `None` - 

### `register` 

```python
def register(plugin: FolioPlugin, name: str | None = None) -> str | None
```

**Returns:** `str | None` - 

### `call_isolated` 

```python
def call_isolated(hook_name: str, *, policy: HookPolicy = 'fail_fast', on_warn: Callable[[str], None] | None = None, impl_guard: Callable[[], Callable[[], None]] | None = None, **kwargs: object) -> list[object]
```

Dispatch a hook one implementation at a time with failure isolation.

``policy='fail_fast'`` re-raises the first failure as a

**Returns:** `list[object]` - 

### `_reject_wrapper_hookimpls` 

```python
def _reject_wrapper_hookimpls(plugin: object, label: str) -> None
```

Refuse hookwrapper/wrapper hookimpls loudly at registration time.

folio's :meth:`call_isolated` invokes each hookimpl as a plain
function, which would silently turn a pluggy wrapper into a no-op
(an un-started generator). Fail at load instead.

**Returns:** `None` - 

### `_plugin_label` 

```python
def _plugin_label(impl: object) -> str
```

**Returns:** `str` - 

### `load_default_plugins` 

```python
def load_default_plugins() -> None
```

Register the first-party :data:`DEFAULT_PLUGINS`.

Bundled defaults are imported directly by module path — never through
the ``folio`` entry-point lookup used for ``plugins:`` entries — so an
installed distribution declaring an entry point named after a default
plugin (e.g. ``folio_docs.docs.integrations.landing``) can never shadow the
first-party module. A default plugin that fails to load degrades to a
warning instead of raising: builds and CLI startup of projects that
never asked for the plugin must not break because of it.

**Returns:** `None` - 

### `load_plugins` 

```python
def load_plugins(plugin_names: list[str], base_dir: Path | None = None) -> None
```

**Returns:** `None` - 

### `_register_plugin_module` 

```python
def _register_plugin_module(mod: object, name: str) -> None
```

**Returns:** `None` - 

## Functions

### `user_plugin_names` 

```python
def user_plugin_names(plugin_names: object) -> list[str]
```

Validated ``plugins:`` entries with default plugins removed.

``None`` (an empty ``plugins:`` key) means no entries. Any other non-list
value — e.g. the common YAML mistake ``plugins: my_plugin`` instead of a
one-item list — raises ``ValueError`` so the misconfiguration fails the
build loudly instead of silently skipping the user's plugins. Entries
naming a default plugin are dropped: defaults are always registered
exactly once, via :meth:`PluginManager.load_default_plugins`.

**Returns:** `list[str]` - 

### `_parse_api_version` 

```python
def _parse_api_version(value: object) -> tuple[int, int]
```

Parse an API version into ``(major, minor)``.

Accepts ``"1"``, ``"1.0"``, ``"1.0.0"``, or a bare int major; a missing
minor defaults to 0 and any patch component is ignored. Raises
``ValueError`` on anything else.

**Returns:** `tuple[int, int]` - 

### `check_plugin_api_version` 

```python
def check_plugin_api_version(declared: str | int | None, plugin_name: str, *, host_version: str = FOLIO_PLUGIN_API_VERSION) -> None
```

Validate a plugin's declared target API version against the host.

Refuses (raises ``ValueError``) on an incompatible major or an unparseable
version; warns when the plugin targets a newer minor than the host; allows
a missing declaration or an older/equal minor.

**Returns:** `None` - 

### `normalize_config_key_names` 

```python
def normalize_config_key_names(result: object) -> ConfigKeyNames
```

**Returns:** `ConfigKeyNames` - 

### `load_installed_cli_plugins` 

```python
def load_installed_cli_plugins(app: object) -> list[str]
```

Register commands contributed by installed Folio products.

CLI entry points are intentionally separate from build plugins. Installing
a product may extend the shared ``folio`` command, but it does not activate
that product in a documentation build or add config keys implicitly.
Failures degrade to warnings so one broken optional product cannot make the
core CLI unusable.

**Returns:** `list[str]` - 

### `_find_entry_point` 

```python
def _find_entry_point(name: str) -> object | None
```

Return the installed ``folio`` entry point matching ``name``, if any.

Entry-point plugins are only loaded when explicitly listed in ``plugins:``
(opt-in); installed packages are never auto-activated without consent.
When multiple installed distributions declare the same entry-point name,
the one from the alphabetically first distribution wins (deterministic)
and a ``UserWarning`` names all contenders.

**Returns:** `object | None` - 

### `_entry_point_dist_name` 

```python
def _entry_point_dist_name(entry_point: object) -> str
```

**Returns:** `str` - 

### `_module_is_importable` 

```python
def _module_is_importable(name: str) -> bool
```

**Returns:** `bool` - 

### `_is_file_plugin` 

```python
def _is_file_plugin(name: str) -> bool
```

**Returns:** `bool` - 

### `_module_name_for_path` 

```python
def _module_name_for_path(path: Path) -> str
```

**Returns:** `str` -
