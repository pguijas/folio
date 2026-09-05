# folio_docs.docs.sidebar 

## Functions

### `_meta_value_to_ts` 

```python
def _meta_value_to_ts(value: Any, *, indent: int = 2) -> list[str]
```

**Returns:** `list[str]` - 

### `_meta_to_ts` 

```python
def _meta_to_ts(meta: dict[str, Any]) -> str
```

Convert a meta dict to a TypeScript `export default { ... }` string.

**Returns:** `str` - 

### `meta_to_ts` 

```python
def meta_to_ts(meta: dict[str, Any]) -> str
```

Public wrapper for rendering a Nextra ``_meta.ts`` from a meta dict.

Exposed for plugins that emit their own ``_meta.ts`` entries (e.g. the
openapi plugin) so they share Folio's exact serialization.

**Returns:** `str` - 

### `_build_module_tree` 

```python
def _build_module_tree(modules: list[ModuleIR]) -> dict
```

Build a nested tree from dotted module names.

Returns a dict where keys are path segments and values are either
nested dicts (intermediate nodes) or None (leaf modules).

**Returns:** `dict` - 

### `_title_case` 

```python
def _title_case(slug: str) -> str
```

Convert a slug to a human-readable title.

**Returns:** `str` - 

### `_sidebar_title` 

```python
def _sidebar_title(title: Any, fallback: str) -> str
```

Normalize a page title for Nextra sidebar metadata.

**Returns:** `str` - 

### `_folder_meta` 

```python
def _folder_meta(title: str, *, default_collapsed: bool) -> str | dict[str, Any]
```

**Returns:** `str | dict[str, Any]` - 

### `_generate_meta_from_tree` 

```python
def _generate_meta_from_tree(tree: dict, path_prefix: str, result: dict[str, str], *, include_index: bool = False, default_collapsed: bool = False) -> None
```

Recursively generate _meta.ts files from a module tree.

**Returns:** `None` - 

### `_order_for_dir` 

```python
def _order_for_dir(path: tuple[str, ...]) -> list[tuple[str, str]]
```

Declared page order for a directory, as (slug, title) pairs.

Walks `_DOC_PAGE_ORDER` one path segment at a time, so a directory at any
depth orders its pages. Returns [] for a path nothing declares.

**Returns:** `list[tuple[str, str]]` - 

### `_generate_doc_meta` 

```python
def _generate_doc_meta(docs: list[MarkdownResult], *, default_collapsed: bool = False) -> tuple[dict[str, Any], dict[str, str]]
```

Generate ordered doc page entries for the root and subdirectory _meta.ts.

Returns (root_meta, extra_meta_files) where:
- root_meta: dict of slug -&gt; title for the root _meta.ts
- extra_meta_files: dict of path -&gt; ts_content for subdirectory _meta.ts files

**Returns:** `tuple[dict[str, Any], dict[str, str]]` - 

### `_move_entries_to_end` 

```python
def _move_entries_to_end(meta: dict[str, Any], slugs: tuple[str, ...]) -> None
```

**Returns:** `None` - 

### `_apply_nav_order` 

```python
def _apply_nav_order(meta: dict[str, Any], nav: list[str]) -> dict[str, Any]
```

Apply the documented top-level nav order to entries that exist.

``Guide`` represents all authored documentation in its existing order;
``API Reference`` and ``Source Code`` both name the generated source tree.
Other labels match an authored page or folder by slug. Unknown labels are
ignored instead of creating dead sidebar routes.

**Returns:** `dict[str, Any]` - 

### `generate_meta_files` 

```python
def generate_meta_files(nav: list[str], modules: list[ModuleIR], docs: list[MarkdownResult] | None = None, *, default_collapsed: bool = False) -> dict[str, str]
```

Generate all _meta.ts files needed (root + docs + source code).

Returns a dict mapping file paths (relative) to their TS content.

**Returns:** `dict[str, str]` -
