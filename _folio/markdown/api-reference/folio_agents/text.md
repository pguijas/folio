# folio_agents.text 

Small text and link primitives owned by Folio for Agents.

## Functions

### `slugify` 

```python
def slugify(text: str) -> str
```

Convert human-readable text to a stable file-safe identifier.

**Returns:** `str` - 

### `safe_href` 

```python
def safe_href(raw_value: Any, path: str) -> str
```

Accept web URLs and relative paths while rejecting executable schemes.

**Returns:** `str` -
