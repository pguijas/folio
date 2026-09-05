# folio_docs.config 

## Classes

### `__post_init__` 

```python
def __post_init__() -> None
```

**Returns:** `None` - 

### `resolve_paths` 

```python
def resolve_paths(base: Path) -> Config
```

**Returns:** [`Config`](/docs/api-reference/folio_docs/config#config) - 

## Functions

### `_normalize_project_repo_ref` 

```python
def _normalize_project_repo_ref(value: Any) -> str
```

**Returns:** `str` - 

### `resolve_output_dir` 

```python
def resolve_output_dir(base: Path, output_dir: str, *, source_paths: Sequence[str] = ()) -> Path
```

Resolve ``output:`` and refuse anything the build would destroy.

A successful export ends in ``shutil.rmtree(output_dir)`` followed by a
copy, and ``folio clean`` removes the same path. Containment inside the
project is therefore not enough: an output that *is* a source directory,
or that contains one, deletes the very files the build just read. Callers
that know the configured sources should pass them as ``source_paths``.

**Returns:** `Path` - 

### `resolve_theme_package_path` 

```python
def resolve_theme_package_path(base: Path, theme_package_path: str, output_dir: str) -> str
```

Resolve theme.package against the project root with containment checks.

Delegates to :func:`folio_docs.paths.resolve_contained_dir` (the same guard used
for ``template.path``): the path is resolved relative to the project root
and rejected if it escapes the project directory (absolute paths or ``..``
traversal) or lands inside the ``.build`` or output directories. Existence
is not required here because ``folio_docs.build`` validates it later.

**Returns:** `str` - 

### `_load_config_plugins` 

```python
def _load_config_plugins(plugin_names: Any, base_dir: Path) -> PluginManager
```

Load first-party default plugins, then the project's `plugins:` entries.

Default plugins are loaded for every build via ``load_default_plugins``
(imported directly, never through entry-point lookup; a broken default
degrades to a warning instead of failing the build); a project listing one
of them explicitly does not register it twice. A non-list ``plugins:``
value raises ``ValueError`` so the misconfiguration fails loudly.

**Returns:** [`PluginManager`](/docs/api-reference/folio_docs/plugin#pluginmanager) - 

### `plugin_config_keys` 

```python
def plugin_config_keys(pm: PluginManager) -> set[str]
```

Collect the extra config keys declared by loaded plugins.

Shared by config loading and the CLI (version-matrix sync) so both treat
an invalid ``config_keys()`` result the same way: warn and skip.

**Returns:** `set[str]` - 

### `_split_components` 

```python
def _split_components(raw_components: Any) -> tuple[list[str], list[dict[str, Any]]]
```

**Returns:** `tuple[list[str], list[dict[str, Any]]]` - 

### `_normalize_component_spec` 

```python
def _normalize_component_spec(entry: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_resolve_component_specs` 

```python
def _resolve_component_specs(specs: list[dict[str, Any]], base: Path) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_disabled_known_config_keys` 

```python
def _disabled_known_config_keys(raw: dict[str, Any]) -> set[str]
```

**Returns:** `set[str]` - 

### `_theme_string` 

```python
def _theme_string(raw_value: Any) -> str
```

**Returns:** `str` - 

### `_theme_preview` 

```python
def _theme_preview(raw_preview: Any) -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_theme_swatch` 

```python
def _theme_swatch(raw_value: Any, path: str) -> str
```

**Returns:** `str` - 

### `_theme_text` 

```python
def _theme_text(raw_value: Any, path: str) -> str
```

**Returns:** `str` - 

### `_theme_href` 

```python
def _theme_href(raw_value: Any, path: str) -> str
```

Sanitize a URL/path value, rejecting unsafe schemes (e.g. javascript:).

Builds on :func:`_theme_text` (unsafe-character rejection), then requires
either an ``http(s)``/``mailto`` URL or a scheme-less relative path. Any
other scheme (``javascript:``, ``data:``, ``vbscript:``, ...) is rejected.

**Returns:** `str` - 

### `_repo_url` 

```python
def _repo_url(raw_value: Any, path: str) -> str
```

Validate a repository URL without restricting it to web schemes.

Unlike :func:`_theme_href` (which guards values rendered as ``<a href>``),
repository URLs commonly use ``ssh://``, ``git://``, ``git+https://``, the
scp-style ``git@host:path`` form, or plain strings, all of which are
accepted verbatim. Only schemes that could execute script or read local
files (``javascript:``, ``data:``, ``vbscript:``, ``file:``) are rejected.

**Returns:** `str` - 

### `_theme_radius` 

```python
def _theme_radius(raw_value: Any) -> str
```

Validate theme.radius against the fixed radius scale.

The template maps the configured radius onto a fixed index scale; any
value outside the scale would silently render as the 0.5rem default, so
unknown values are rejected up front. Legacy named values (``none``,
``sm``, ``md``, ``lg``, ``full``) are accepted as aliases for the scale
values so configs written against older docs keep building.

**Returns:** `str` - 

### `_theme_bool` 

```python
def _theme_bool(raw_value: Any, path: str) -> bool | None
```

**Returns:** `bool | None` - 

### `_validate_theme_css_value` 

```python
def _validate_theme_css_value(value: Any, path: str) -> str
```

**Returns:** `str` - 

### `_theme_css_vars` 

```python
def _theme_css_vars(raw_vars: Any, path: str) -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_theme_tokens` 

```python
def _theme_tokens(raw_tokens: Any) -> dict[str, dict[str, str]]
```

**Returns:** `dict[str, dict[str, str]]` - 

### `_theme_header` 

```python
def _theme_header(raw_header: Any) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_theme_variant_id` 

```python
def _theme_variant_id(raw_id: Any, path: str) -> str
```

**Returns:** `str` - 

### `_theme_variant_option` 

```python
def _theme_variant_option(raw_option: Any, path: str) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_theme_variants` 

```python
def _theme_variants(raw_variants: Any) -> dict[str, dict[str, Any]]
```

**Returns:** `dict[str, dict[str, Any]]` - 

### `_theme_tune` 

```python
def _theme_tune(raw_tune: Any) -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_theme_package_path` 

```python
def _theme_package_path(raw_theme: Any) -> str
```

**Returns:** `str` - 

### `_template_path` 

```python
def _template_path(raw_template: Any) -> str
```

**Returns:** `str` - 

### `_template_overlay_path` 

```python
def _template_overlay_path(raw_template: Any) -> str
```

Validate the opt-in ``template.overlay_path`` partial-override key.

``template.overlay_path`` layers user-owned files on top of the bundled
template (user wins, missing files fall back to the bundled template). It is
mutually exclusive with ``template.path`` (a full replacement): configuring
both is ambiguous, so the overlay is ignored with a warning and the full
replacement wins. See ``docs/guide/theming/custom-templates.md``.

**Returns:** `str` - 

### `_template_params` 

```python
def _template_params(raw_template: Any) -> dict[str, Any]
```

Validate ``template.params`` against its documented contract.

``template.params`` is an arbitrary JSON-serializable mapping that Folio
emits verbatim into ``lib/folio-template.ts`` as ``folioTemplateParams``;
Folio never interprets the values. The contract is:

- absent (``template`` not a mapping or no ``params`` key) -&gt; ``{}``
- ``null`` -&gt; ``{}``
- a non-mapping value (list, string, number, ...) -&gt; ``{}`` with a warning,
  because the template can still build with empty params
- a mapping that is not JSON-serializable -&gt; a clear ``ValueError``, because
  it cannot be emitted into ``folio-template.ts`` and would break the build

See ``docs/guide/theming/custom-templates.md`` for the full contract.

**Returns:** `dict[str, Any]` - 

### `_template_docs_route_base` 

```python
def _template_docs_route_base(raw_template: Any) -> str
```

**Returns:** `str` - 

### `normalize_docs_route_base` 

```python
def normalize_docs_route_base(value: Any) -> str
```

**Returns:** `str` - 

### `normalize_base_path` 

```python
def normalize_base_path(value: Any) -> str
```

**Returns:** `str` - 

### `load_config` 

```python
def load_config(path: Path) -> Config
```

**Returns:** [`Config`](/docs/api-reference/folio_docs/config#config) - 

### `_config_mapping` 

```python
def _config_mapping(raw: dict[str, Any], key: str) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_config_string_list` 

```python
def _config_string_list(value: Any, key: str) -> list[str]
```

**Returns:** `list[str]` - 

### `load_config_with_plugins` 

```python
def load_config_with_plugins(path: Path, plugin_base_dir: Path | None = None) -> tuple[Config, PluginManager]
```

**Returns:** `tuple[Config, PluginManager]` -
