# folio_docs.docs.extension_emitter 

## Classes

### `__init__` 

```python
def __init__(build_dir: str | Path, *, inject_builtins: bool = True, project_dir: str = '') -> None
```

Emit registry extensions into ``build_dir``.

``inject_builtins=False`` keeps builtin-origin components out of
``mdx-components.tsx`` — used for custom ``template.path`` builds that
do not bundle the builtin component files. ``project_dir`` anchors
relative component ``source_path`` values (instead of the process CWD).

**Returns:** `None` - 

### `apply` 

```python
def apply(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `_copy_components` 

```python
def _copy_components(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `_component_target` 

```python
def _component_target(component: ComponentDefinition, source: Path) -> Path
```

**Returns:** `Path` - 

### `_write_data_modules` 

```python
def _write_data_modules(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `_write_data_module` 

```python
def _write_data_module(module: DataModuleDefinition) -> None
```

**Returns:** `None` - 

### `_inject_mdx_components` 

```python
def _inject_mdx_components(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `_write_views` 

```python
def _write_views(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `_write_view` 

```python
def _write_view(view: ViewDefinition, registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `_app_route_path` 

```python
def _app_route_path(route: str) -> Path
```

**Returns:** `Path` - 

`@staticmethod`

### `_component_import_line` 

```python
def _component_import_line(component: ComponentDefinition) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_layout_import_line` 

```python
def _layout_import_line(layout: LayoutDefinition) -> str
```

**Returns:** `str` -
