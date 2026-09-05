# folio_docs.docs.theme_package_validator 

Validator for theme packages to ensure they don't contain reserved paths.

## Functions

### `_validate_theme_package` 

```python
def _validate_theme_package(path: Path) -> list[str]
```

Validate a theme package for common issues.

Returns a list of error messages. Empty list means valid.

**Returns:** `list[str]` - 

### `validate_and_raise` 

```python
def validate_and_raise(path: Path) -> None
```

Validate a theme package and raise ValueError if validation fails.

**Returns:** `None` - 

**Raises:** `ValueError` - If validation fails with all error messages joined.
