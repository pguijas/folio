# folio_docs.watcher 

## Classes

`@classmethod`

### `from_config` 

```python
def from_config(resolved: Config) -> _PythonModuleCache
```

**Returns:** `_PythonModuleCache` - 

### `all_modules` 

```python
def all_modules() -> list[ModuleIR]
```

**Returns:** [`list[ModuleIR]`](/docs/api-reference/folio_docs/ir#moduleir) - 

### `contains` 

```python
def contains(source_file: Path) -> bool
```

**Returns:** `bool` - 

### `upsert` 

```python
def upsert(module: ModuleIR) -> None
```

**Returns:** `None` - 

### `remove` 

```python
def remove(source_file: Path) -> None
```

**Returns:** `None` - 

## Functions

### `_preview_examples_dir` 

```python
def _preview_examples_dir(project_dir: Path) -> Path
```

**Returns:** `Path` - 

### `_watch_dirs_with_preview_examples` 

```python
def _watch_dirs_with_preview_examples(watch_dirs: list[Path], project_dir: Path) -> list[Path]
```

**Returns:** `list[Path]` - 

### `_plugin_watch_dirs` 

```python
def _plugin_watch_dirs(plugin_manager, resolved: Config) -> list[Path]
```

Directories plugins asked the watcher to care about (existing only).

**Returns:** `list[Path]` - 

### `_dispatch_plugin_change` 

```python
def _dispatch_plugin_change(plugin_manager, plugin_dirs: list[Path], builder, resolved: Config, change: Change, path: Path) -> bool
```

Offer a change under a plugin-watched directory to the plugins.

The handler, not the watcher, knows what the files mean — a board
directory holds .md cards and a .yaml column set, and future plugins
hold whatever they hold. Returns True when some plugin handled it.

**Returns:** `bool` - 

### `_is_under` 

```python
def _is_under(path: Path, dirs: list[Path]) -> bool
```

**Returns:** `bool` - 

### `_module_name_from_path` 

```python
def _module_name_from_path(path: Path, src_dir: Path) -> str
```

**Returns:** `str` - 

### `_route_from_doc_path` 

```python
def _route_from_doc_path(path: Path, doc_dir: Path) -> str
```

**Returns:** `str` - 

### `_parse_python_modules` 

```python
def _parse_python_modules(resolved: Config)
```

### `_parse_python_module` 

```python
def _parse_python_module(path: Path, module_name: str, resolved: Config) -> ModuleIR
```

**Returns:** [`ModuleIR`](/docs/api-reference/folio_docs/ir#moduleir) - 

### `_disabled_api_feature_for_module` 

```python
def _disabled_api_feature_for_module(module_name: str) -> str | None
```

**Returns:** `str | None` - 

### `_published_modules` 

```python
def _published_modules(modules: list[ModuleIR]) -> list[ModuleIR]
```

**Returns:** [`list[ModuleIR]`](/docs/api-reference/folio_docs/ir#moduleir) - 

### `_is_python_excluded` 

```python
def _is_python_excluded(path: Path, resolved: Config) -> bool
```

**Returns:** `bool` - 

### `_write_api_reference_index` 

```python
def _write_api_reference_index(modules: list[ModuleIR], builder: SiteBuilder) -> None
```

**Returns:** `None` - 

### `_write_meta_for_modules` 

```python
def _write_meta_for_modules(all_modules: list[ModuleIR], resolved: Config, config: Config, builder: SiteBuilder) -> None
```

**Returns:** `None` - 

### `_regenerate_meta` 

```python
def _regenerate_meta(python_source_dirs: list[Path], resolved: Config, config: Config, builder: SiteBuilder) -> None
```

**Returns:** `None` - 

### `_handle_python_change_incremental` 

```python
def _handle_python_change_incremental(change: Change, path: Path, module_name: str, route: str, module_cache: _PythonModuleCache, config: Config, resolved: Config, builder: SiteBuilder, project_dir: Path, console: Console, verbose: bool) -> bool
```

**Returns:** `bool` - 

### `_handle_python_change` 

```python
def _handle_python_change(change: Change, path: Path, python_source_dirs: list[Path], config: Config, resolved: Config, builder: SiteBuilder, project_dir: Path, console: Console, verbose: bool, module_cache: _PythonModuleCache | None = None) -> None
```

**Returns:** `None` - 

### `_handle_doc_change` 

```python
def _handle_doc_change(change: Change, path: Path, doc_source_dirs: list[Path], config: Config, resolved: Config, builder: SiteBuilder, python_source_dirs: list[Path], console: Console, verbose: bool) -> None
```

**Returns:** `None` - 

### `_handle_preview_example_change` 

```python
def _handle_preview_example_change(_change: Change, path: Path, examples_dir: Path, builder: SiteBuilder, console: Console, verbose: bool) -> None
```

**Returns:** `None` - 

### `_watcher_loop` 

```python
def _watcher_loop(stop_event: threading.Event, watch_dirs: list[Path], python_source_dirs: list[Path], doc_source_dirs: list[Path], preview_examples_dir: Path, config: Config, resolved: Config, builder: SiteBuilder, project_dir: Path, console: Console, verbose: bool, plugin_manager = None, plugin_watch_dirs: list[Path] | None = None) -> None
```

**Returns:** `None` - 

### `start_watcher` 

```python
def start_watcher(watch_dirs: list[Path], config: Config, resolved: Config, builder: SiteBuilder, project_dir: Path, console: Console, verbose: bool = False, plugin_manager = None) -> threading.Event
```

Start file watcher in a daemon thread. Returns stop event.

**Returns:** `threading.Event` -
