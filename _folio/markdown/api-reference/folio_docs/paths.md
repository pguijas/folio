# folio_docs.paths 

Shared path-resolution helpers with project containment guards.

## Functions

### `resolve_contained_dir` 

```python
def resolve_contained_dir(raw_path: str | Path, project_root: Path, output_dir: str | Path, label: str, must_exist: bool = True) -> Path
```

Resolve ``raw_path`` against the project root with containment guards.

This is the single implementation of the guard applied to every
user-configurable directory that Folio reads from or copies into the
build workspace (``theme.package``, ``template.path``,
``template.overlay_path``).

Contract:

- A relative ``raw_path`` is resolved against ``project_root``; an
  absolute path is resolved as-is.
- The resolved path must stay within ``project_root`` (the root itself is
  allowed); otherwise ``ValueError`` with
  ``"{label} must stay within the project directory"``.
- The resolved path must not be ``<project_root>/.build`` or anything
  inside it; otherwise ``ValueError`` with
  ``"{label} cannot point inside the .build directory"``.
- The resolved path must not be ``output_dir`` or anything inside it;
  otherwise ``ValueError`` with
  ``"{label} cannot point inside the output directory"``.
- With ``must_exist=True`` the resolved path must be an existing
  directory; otherwise ``FileNotFoundError`` with
  ``"{label} does not exist: {resolved}"``.

Returns the fully resolved absolute :class:`~pathlib.Path`.

**Returns:** `Path` -
