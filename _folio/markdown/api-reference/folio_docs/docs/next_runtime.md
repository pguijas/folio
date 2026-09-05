# folio_docs.docs.next_runtime 

## Classes

### `__init__` 

```python
def __init__(template_dir: str | Path, build_dir: str | Path, output_dir: str | Path, *, verbose: bool = False) -> None
```

**Returns:** `None` - 

### `install_deps` 

```python
def install_deps() -> bool
```

Install dependencies if needed. Returns True if install ran.

**Returns:** `bool` - 

### `build` 

```python
def build(*, log_path: str | Path | None = None, output_callback: Callable[[str], None] | None = None) -> None
```

**Returns:** `None` - 

### `_remove_stale_build_artifacts` 

```python
def _remove_stale_build_artifacts() -> None
```

**Returns:** `None` - 

### `copy_static_output` 

```python
def copy_static_output() -> None
```

**Returns:** `None` - 

### `serve` 

```python
def serve(port: int = 4321, *, kill_existing: bool = False) -> subprocess.Popen
```

**Returns:** `subprocess.Popen` - 

### `_check_dependencies` 

```python
def _check_dependencies() -> None
```

**Returns:** `None` - 

### `_has_next_binary` 

```python
def _has_next_binary() -> bool
```

**Returns:** `bool` - 

### `_has_working_next` 

```python
def _has_working_next() -> bool
```

**Returns:** `bool` - 

### `_patch_nextra_schema` 

```python
def _patch_nextra_schema() -> None
```

Patch nextra-theme-docs Zod schema bug where children is validated

as nonoptional but has already been destructured out of props.

**Returns:** `None` - 

### `_patch_nextra_generated_content_timestamps` 

```python
def _patch_nextra_generated_content_timestamps() -> None
```

Skip Git timestamp lookups for Folio-generated MDX content.

**Returns:** `None` - 

`@staticmethod`

### `_file_hash` 

```python
def _file_hash(path: Path) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `is_port_in_use` 

```python
def is_port_in_use(port: int) -> bool
```

**Returns:** `bool` - 

`@staticmethod`

### `kill_port` 

```python
def kill_port(port: int) -> bool
```

Kill any process listening on the given port. Returns True if a process was killed.

**Returns:** `bool` - 

## Functions

### `_tool_version_output` 

```python
def _tool_version_output(command: list[str]) -> str
```

**Returns:** `str` - 

### `_parse_version` 

```python
def _parse_version(raw: str) -> tuple[int, ...]
```

**Returns:** `tuple[int, ...]` - 

### `preflight_check` 

```python
def preflight_check() -> None
```

Verify Node and pnpm exist at usable versions before expensive work.

Raises RuntimeError with every problem listed and an actionable fix, so
a missing toolchain fails in the first second of a build instead of
minutes in.

**Returns:** `None` -
