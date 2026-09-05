# folio_docs.agent_output.contract 

## Functions

### `strip_js_comments` 

```python
def strip_js_comments(code: str) -> str
```

Remove JS/TS line and block comments, leaving string literals intact.

A small scanner instead of a regex so that ``//`` inside a string or
template literal (e.g. ``"https://example.com"``) is not treated as the
start of a line comment.

**Returns:** `str` - 

### `import_statements` 

```python
def import_statements(code: str) -> list[str]
```

Return every import statement found in comment-stripped ``code``.

**Returns:** `list[str]` - 

### `strip_import_statements` 

```python
def strip_import_statements(code: str) -> str
```

Remove import statements from comment-stripped ``code``.

**Returns:** `str` - 

### `has_component_entry` 

```python
def has_component_entry(code: str, name: str) -> bool
```

Report whether ``name`` is wired as a components-mapping entry.

Accepts the object-property forms (``Name,`` / ``Name:`` / ``Name }``, at
any indentation) and ``as Name`` re-exports. ``code`` must already be
comment- and import-stripped so a merely imported symbol never counts as
a mapping entry.

**Returns:** `bool` - 

### `build_contract` 

```python
def build_contract(components: Iterable[ComponentDefinition] | None = None) -> list[dict[str, Any]]
```

Derive the MDX component contract from component definitions.

Membership is the explicit ``contract`` flag on the definition and the
contract ``source`` field comes from ``source_label`` (never from
``category``, which is pure taxonomy). Passing the components of a live
registry lets plugin components carrying ``contract=True`` join the
emitted contract; the default is the builtin manifest, keeping

**Returns:** `list[dict[str, Any]]` - 

### `required_component_names` 

```python
def required_component_names() -> list[str]
```

**Returns:** `list[str]` - 

### `render_mdx_contract_module` 

```python
def render_mdx_contract_module(components: Iterable[ComponentDefinition] | None = None) -> str
```

**Returns:** `str` - 

### `build_authoring_contract` 

```python
def build_authoring_contract(*, folio_version: str, generated_at: str, components: Iterable[ComponentDefinition] | None = None, config_keys: Iterable[str] = (), routes: Iterable[str] = ()) -> dict[str, Any]
```

Assemble what a page in this project may contain, as one JSON payload.

Three answers, one envelope: which components MDX pages can use, which
top-level ``docs.yaml`` keys this project accepts, and which pages the
build emitted. ``components`` takes the live registry so plugin and config
components flagged ``contract=True`` are described too; ``None`` falls back
to the builtin manifest.

**Returns:** `dict[str, Any]` - 

### `render_authoring_contract` 

```python
def render_authoring_contract(*, folio_version: str, generated_at: str, components: Iterable[ComponentDefinition] | None = None, config_keys: Iterable[str] = (), routes: Iterable[str] = ()) -> str
```

Serialize :func:`build_authoring_contract` as the published file text.

**Returns:** `str` - 

### `validate_template_mdx_contract` 

```python
def validate_template_mdx_contract(template_dir: str | Path) -> list[str]
```

**Returns:** `list[str]` -
