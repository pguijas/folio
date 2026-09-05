# folio_docs.agent_output.artifacts 

Publication boundary for Folio for Agents artifacts.

## Classes

Write machine-readable artifacts beside the Folio Docs site.

The class owns only agent-facing output. It receives resolved site paths
from the shared build pipeline and never builds the human frontend.

### `__init__` 

```python
def __init__(config: Config, *, build_dir: str | Path, output_dir: str | Path, base_path: str = '') -> None
```

**Returns:** `None` - 

`@property`

### `markdown_root` 

```python
markdown_root
```

**Type:** `Path` - 

### `markdown_path` 

```python
def markdown_path(route: str) -> Path
```

**Returns:** `Path` - 

### `write_markdown_mirror` 

```python
def write_markdown_mirror(route: str, content: str) -> Path
```

**Returns:** `Path` - 

### `markdown_mirror_exists` 

```python
def markdown_mirror_exists(route: str) -> bool
```

**Returns:** `bool` - 

### `remove_markdown_mirror` 

```python
def remove_markdown_mirror(route: str) -> None
```

**Returns:** `None` - 

### `write_authoring_contract` 

```python
def write_authoring_contract(*, generated_at: str, components: Iterable[ComponentDefinition] | None, config_keys: Iterable[str], routes: Iterable[str]) -> Path
```

**Returns:** `Path` - 

### `write_llm_files` 

```python
def write_llm_files(llms_txt: str | None = None, llms_full_txt: str | None = None, *, serve: bool = False) -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_write_or_remove` 

```python
def _write_or_remove(destination: Path, name: str, content: str | None) -> None
```

**Returns:** `None` - 

### `_point_robots_at_files` 

```python
def _point_robots_at_files(destination: Path, names: list[str]) -> None
```

**Returns:** `None` - 

### `_artifact_url` 

```python
def _artifact_url(name: str) -> str
```

**Returns:** `str` -
