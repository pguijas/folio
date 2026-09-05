# folio_docs.docs.integrations.openapi 

## Functions

### `config_keys` 

```python
def config_keys() -> list[str]
```

**Returns:** `list[str]` - 

### `configure` 

```python
def configure(config: Any, raw_config: dict[str, Any]) -> None
```

**Returns:** `None` - 

### `register_extensions` 

```python
def register_extensions(registry: Any, config: Any) -> None
```

**Returns:** `None` - 

### `emit_assets` 

```python
def emit_assets(builder: Any, config: Any) -> None
```

**Returns:** `None` - 

### `normalize_openapi` 

```python
def normalize_openapi(raw_openapi: Any, *, project_dir: Path) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `normalize_source` 

```python
def normalize_source(raw_source: Any, *, project_dir: Path) -> dict[str, Any] | None
```

**Returns:** `dict[str, Any] | None` - 

### `get_openapi` 

```python
def get_openapi(config: Any) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `public_source_data` 

```python
def public_source_data(source: dict[str, Any]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `docs_page_mdx` 

```python
def docs_page_mdx(source: dict[str, Any]) -> str
```

**Returns:** `str` - 

### `_existing_page` 

```python
def _existing_page(builder: Any, route: str) -> str | None
```

Return the page content currently on disk, or None when unknown.

Builders are not required to expose ``read_page``; when it is missing the
content is treated as unknown so the page gets rewritten, which keeps warm
builds from serving stale pages.

**Returns:** `str | None` - 

### `_write_route_meta` 

```python
def _write_route_meta(builder: Any, route: str, title: str) -> None
```

**Returns:** `None` - 

### `_merge_meta_entry` 

```python
def _merge_meta_entry(builder: Any, directory: str, slug: str, title: str, *, hidden_index: bool = False) -> None
```

Insert or replace a single ``_meta.ts`` entry non-destructively.

Only the plugin's own entry (and, when requested, a missing hidden
``index`` entry) is touched; every other line — including nested object
entries written by the sidebar generator — is preserved verbatim.

**Returns:** `None` - 

### `_meta_entry_lines` 

```python
def _meta_entry_lines(meta: dict[str, Any]) -> list[str]
```

Serialize entries with folio's exact ``_meta.ts`` formatting.

**Returns:** `list[str]` - 

### `_escape_meta_key` 

```python
def _escape_meta_key(key: str) -> str
```

**Returns:** `str` - 

### `_has_top_level_key` 

```python
def _has_top_level_key(body: list[str], key: str) -> bool
```

**Returns:** `bool` - 

### `_brace_delta` 

```python
def _brace_delta(line: str) -> int
```

Net brace/bracket depth change, ignoring braces in string literals.

**Returns:** `int` - 

### `_load_spec` 

```python
def _load_spec(raw_source: dict[str, Any], *, project_dir: Path) -> Any
```

**Returns:** `Any` - 

### `_normalize_route` 

```python
def _normalize_route(raw_route: Any, title: str) -> str
```

**Returns:** `str` - 

### `_source_label` 

```python
def _source_label(raw_source: dict[str, Any]) -> str
```

**Returns:** `str` - 

### `_servers` 

```python
def _servers(spec: dict[str, Any]) -> list[str]
```

**Returns:** `list[str]` - 

### `_operations` 

```python
def _operations(spec: dict[str, Any]) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_schemas` 

```python
def _schemas(spec: dict[str, Any]) -> list[str]
```

**Returns:** `list[str]` - 

### `_string_list` 

```python
def _string_list(value: Any) -> list[str]
```

**Returns:** `list[str]` - 

### `_escape_mdx_attr` 

```python
def _escape_mdx_attr(value: str) -> str
```

**Returns:** `str` - 

### `_escape_mdx_text` 

```python
def _escape_mdx_text(value: str) -> str
```

Backslash-escape characters MDX treats as syntax in body text.

Braces open ES expressions, angle brackets open JSX elements, and
backticks open code spans; a raw backslash could form escapes itself.

**Returns:** `str` -
