# folio_docs.docs.xref 

## Functions

### `build_symbol_index` 

```python
def build_symbol_index(modules: list[ModuleIR], docs_route_base: str = '/docs') -> dict[str, str]
```

Build a mapping of fully-qualified symbol names to documentation URLs.

Returns a dict like:
    \{
        "folio_docs.config": "/docs/api-reference/folio_docs/config",
        "folio_docs.config.Config": "/docs/api-reference/folio_docs/config#config",
        "folio_docs.config.load_config": "/docs/api-reference/folio_docs/config#load_config",
    \}

**Returns:** `dict[str, str]` - 

### `_index_class` 

```python
def _index_class(index: dict[str, str], parent_fqn: str, mod_route: str) -> None
```

Index a class and its inner classes recursively.

**Returns:** `None` - 

### `_extract_bare_names` 

```python
def _extract_bare_names(type_str: str) -> list[str]
```

Extract all potential symbol names from a type string.

Handles generics like ``list[Config]``, unions like ``Config | None``,
and comma-separated types like ``dict[str, Config]``.

**Returns:** `list[str]` - 

### `_split_respecting_brackets` 

```python
def _split_respecting_brackets(s: str) -> list[str]
```

Split a string on commas, but not inside brackets.

**Returns:** `list[str]` - 

### `resolve_type_link` 

```python
def resolve_type_link(type_str: str, index: dict[str, str], current_module: str) -> str | None
```

Try to resolve a type string to a documentation URL.

Handles:
- Simple names: ``Config`` -&gt; look up ``{current_module}.Config``, then all modules
- Qualified names: ``folio_docs.config.Config`` -&gt; direct lookup
- Generic types: ``list[Config]`` -&gt; resolve the inner type ``Config``
- Union types: ``Config | None`` -&gt; resolve ``Config``

Returns the URL if a single resolvable symbol is found, None otherwise.

**Returns:** `str | None` -
