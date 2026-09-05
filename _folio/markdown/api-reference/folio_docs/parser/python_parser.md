# folio_docs.parser.python_parser 

## Functions

### `_resolve_style` 

```python
def _resolve_style(style: str) -> docstring_parser.Style
```

**Returns:** `docstring_parser.Style` - 

### `_parse_docstring` 

```python
def _parse_docstring(raw: str | None, style: docstring_parser.Style = docstring_parser.Style.GOOGLE) -> DocstringIR
```

**Returns:** [`DocstringIR`](/docs/api-reference/folio_docs/ir#docstringir) - 

### `_get_annotation` 

```python
def _get_annotation(node: ast.expr | None) -> str
```

**Returns:** `str` - 

### `_parse_function` 

```python
def _parse_function(node: ast.FunctionDef | ast.AsyncFunctionDef, source_file: str, is_in_class: bool = False, style: docstring_parser.Style = docstring_parser.Style.GOOGLE) -> FunctionIR
```

**Returns:** [`FunctionIR`](/docs/api-reference/folio_docs/ir#functionir) - 

### `_parse_class` 

```python
def _parse_class(node: ast.ClassDef, source_file: str, style: docstring_parser.Style = docstring_parser.Style.GOOGLE) -> ClassIR
```

**Returns:** [`ClassIR`](/docs/api-reference/folio_docs/ir#classir) - 

### `parse_python_file` 

```python
def parse_python_file(path: Path, module_name: str, style: docstring_parser.Style = docstring_parser.Style.GOOGLE) -> ModuleIR
```

**Returns:** [`ModuleIR`](/docs/api-reference/folio_docs/ir#moduleir) - 

### `_is_python_excluded` 

```python
def _is_python_excluded(path: Path, excludes: list[str]) -> bool
```

Match project-relative glob patterns and exact file/directory paths.

**Returns:** `bool` - 

### `_is_python_import_root` 

```python
def _is_python_import_root(path: Path) -> bool
```

Whether a configured path is the conventional ``src/`` import root.

**Returns:** `bool` - 

### `parse_python_directory` 

```python
def parse_python_directory(directory: str, package_name: str, excludes: list[str], docstring_style: str = 'google') -> list[ModuleIR]
```

**Returns:** [`list[ModuleIR]`](/docs/api-reference/folio_docs/ir#moduleir) - 

### `parse_python_source_root` 

```python
def parse_python_source_root(directory: str, excludes: list[str], docstring_style: str = 'google') -> list[ModuleIR]
```

Parse modules and packages beneath a conventional import root.

**Returns:** [`list[ModuleIR]`](/docs/api-reference/folio_docs/ir#moduleir) -
