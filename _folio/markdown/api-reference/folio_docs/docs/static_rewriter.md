# folio_docs.docs.static_rewriter 

## Classes

### `__init__` 

```python
def __init__(output_dir: str | Path) -> None
```

**Returns:** `None` - 

### `fix_asset_paths` 

```python
def fix_asset_paths() -> None
```

Rewrite local URLs so static files work when opened via file://.

**Returns:** `None` - 

### `_copy_opengraph_images_with_png_extension` 

```python
def _copy_opengraph_images_with_png_extension() -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_rewrite_opengraph_image_urls` 

```python
def _rewrite_opengraph_image_urls(content: str) -> str
```

**Returns:** `str` - 

### `rewrite_file_urls` 

```python
def rewrite_file_urls(content: str, fpath: Path) -> str
```

**Returns:** `str` - 

### `rewrite_file_url` 

```python
def rewrite_file_url(url: str, fpath: Path, *, route_index: bool = False) -> str
```

**Returns:** `str` - 

### `_is_next_asset` 

```python
def _is_next_asset(fpath: Path) -> bool
```

**Returns:** `bool` - 

### `_patch_next_runtime_asset_prefix` 

```python
def _patch_next_runtime_asset_prefix(fpath: Path) -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_stash_script_bodies` 

```python
def _stash_script_bodies(content: str) -> tuple[str, list[str]]
```

**Returns:** `tuple[str, list[str]]` - 

`@staticmethod`

### `_restore_script_bodies` 

```python
def _restore_script_bodies(content: str, script_bodies: list[str]) -> str
```

**Returns:** `str` - 

### `_write_file_search_fallback` 

```python
def _write_file_search_fallback() -> bool
```

**Returns:** `bool` - 

`@staticmethod`

### `_read_pagefind_fragment` 

```python
def _read_pagefind_fragment(fragment_path: Path) -> dict | None
```

**Returns:** `dict | None` - 

### `_pagefind_file_url` 

```python
def _pagefind_file_url(url: str) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_inject_file_search_script` 

```python
def _inject_file_search_script(content: str) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_file_search_script` 

```python
def _file_search_script(index_json: str) -> str
```

**Returns:** `str` - 

### `_file_url_target_under_root` 

```python
def _file_url_target_under_root(target_path: Path, root: Path) -> Path | None
```

**Returns:** `Path | None` - 

`@staticmethod`

### `_file_url_target` 

```python
def _file_url_target(target_path: Path) -> Path | None
```

**Returns:** `Path | None` -
