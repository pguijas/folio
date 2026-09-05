# folio_docs.extensions 

## Classes

`@property`

### `imported_name` 

```python
imported_name
```

**Type:** `str` - 

### `__init__` 

```python
def __init__() -> None
```

**Returns:** `None` - 

### `register_component` 

```python
def register_component(name: str, *, import_path: str, export_name: str | None = None, expose_mdx: bool = True, source_path: str | Path | None = None, props: Mapping[str, str] | None = None, required: bool = False, category: str = 'general', contract: bool = False, source_label: str = '', origin: str = 'plugin') -> ComponentDefinition
```

**Returns:** [`ComponentDefinition`](/docs/api-reference/folio_docs/extensions#componentdefinition) - 

### `register_layout` 

```python
def register_layout(name: str, *, import_path: str, export_name: str, slots: list[str] | tuple[str, ...] = ('main',)) -> LayoutDefinition
```

**Returns:** [`LayoutDefinition`](/docs/api-reference/folio_docs/extensions#layoutdefinition) - 

### `write_data_module` 

```python
def write_data_module(name: str, *, export_name: str, data: Any, type_source: str = '', type_annotation: str = '', module_path: str = '') -> DataModuleDefinition
```

**Returns:** [`DataModuleDefinition`](/docs/api-reference/folio_docs/extensions#datamoduledefinition) - 

### `add_view` 

```python
def add_view(*, path: str, layout: str, slots: dict[str, list[dict[str, Any]] | tuple[ViewBlock, ...]], title: str = '', props: dict[str, Any] | None = None) -> ViewDefinition
```

**Returns:** [`ViewDefinition`](/docs/api-reference/folio_docs/extensions#viewdefinition) - 

`@staticmethod`

### `_normalize_view_path` 

```python
def _normalize_view_path(path: str) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_validate_identifier` 

```python
def _validate_identifier(value: str, label: str) -> None
```

**Returns:** `None` - 

## Functions

### `register_builtin_extensions` 

```python
def register_builtin_extensions(registry: ExtensionRegistry) -> None
```

**Returns:** `None` - 

### `register_config_components` 

```python
def register_config_components(registry: ExtensionRegistry, config: Any) -> None
```

Register docs.yaml ``components:`` entries into the registry.

Directory entries are expanded first (each top-level ``.tsx``/``.jsx``
file becomes a component named after its PascalCased stem), then named
specs are registered. Both share the same import-stem deduplication, so a
directory file and a ``from:`` spec with the same filename stem get
distinct generated import paths.

**Returns:** `None` - 

### `_component_dir_specs` 

```python
def _component_dir_specs(config: Any) -> list[dict[str, Any]]
```

Expand ``components:`` directory entries into named component specs.

Relative directories are anchored to the project directory (mirroring how
the emitter anchors relative ``source_path`` values). A missing directory
fails the build loudly; a directory without component files warns so a
typo'd but existing path does not silently register nothing.

**Returns:** `list[dict[str, Any]]` - 

### `_component_name_from_stem` 

```python
def _component_name_from_stem(stem: str) -> str
```

Derive a PascalCase component name from a file stem.

``hero.tsx`` -&gt; ``Hero``; ``my-chart.tsx`` -&gt; ``MyChart``. The file must

``export:`` field of a named spec).

**Returns:** `str` - 

### `_component_import_stem` 

```python
def _component_import_stem(source_stem: str, component_name: str, *, duplicate_source_stem: bool, used_import_stems: set[str]) -> str
```

**Returns:** `str` - 

### `_component_file_segment` 

```python
def _component_file_segment(value: str) -> str
```

**Returns:** `str` -
