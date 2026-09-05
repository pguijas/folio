# folio_docs.coverage 

Coverage analysis for Python documentation.

Analyzes parsed ModuleIR objects and reports which symbols have docstrings
vs which are undocumented.

## Classes

Coverage statistics for a set of modules.

`@property`

### `percentage` 

```python
percentage
```

Return coverage as a percentage (0-100).

**Type:** `float` - 

## Functions

### `_is_private` 

```python
def _is_private(name: str) -> bool
```

Return True if the name is private (starts with _) but not __init__.

**Returns:** `bool` - 

### `_has_docstring` 

```python
def _has_docstring(docstring_short: str) -> bool
```

Return True if the short_description is non-empty.

**Returns:** `bool` - 

### `_analyze_function` 

```python
def _analyze_function(func: FunctionIR, prefix: str, documented: list[str], undocumented: list[str]) -> None
```

Check a single function/method and classify it.

**Returns:** `None` - 

### `_analyze_class` 

```python
def _analyze_class(prefix: str, documented: list[str], undocumented: list[str]) -> None
```

Check a class and all its public methods.

**Returns:** `None` - 

### `analyze_module` 

```python
def analyze_module(module: ModuleIR) -> CoverageResult
```

Analyze a single module and return coverage statistics.

**Returns:** [`CoverageResult`](/docs/api-reference/folio_docs/coverage#coverageresult) - 

### `analyze_modules` 

```python
def analyze_modules(modules: list[ModuleIR]) -> dict[str, CoverageResult]
```

Analyze multiple modules. Returns a dict mapping module name to CoverageResult.

**Returns:** [`dict[str, CoverageResult]`](/docs/api-reference/folio_docs/coverage#coverageresult) - 

### `aggregate` 

```python
def aggregate(results: dict[str, CoverageResult]) -> CoverageResult
```

Aggregate multiple CoverageResults into a single total.

**Returns:** [`CoverageResult`](/docs/api-reference/folio_docs/coverage#coverageresult) -
