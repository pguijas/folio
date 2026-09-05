# folio_docs.docs.builtin_drift 

Guard the builtin manifest against the bundled MDX components.

Two guards, because the manifest can drift from the template in two ways.

## Functions

### `template_component_entry_names` 

```python
def template_component_entry_names(template_text: str) -> list[str]
```

Extract shorthand component entry names from ``mdx-components.tsx``.

Comments and import statements are ignored; only whole-line shorthand
mapping entries (``Name,`` at any indentation) count.

**Returns:** `list[str]` - 

### `check_template_drift` 

```python
def check_template_drift(template_text: str) -> list[str]
```

Compare the builtin manifest and a template's component entries.

Bidirectional: reports builtins declared in :data:`BUILTIN_COMPONENTS`
that have no entry in ``template_text``, and component entries present in
``template_text`` that the manifest does not declare. Returns
human-readable drift descriptions; empty when the two agree.

**Returns:** `list[str]` - 

### `_matching_brace` 

```python
def _matching_brace(text: str, start: int) -> int
```

Index just past the brace group opening at ``text[start]``.

**Returns:** `int` - 

### `_split_members` 

```python
def _split_members(body: str) -> list[str]
```

Split an object type body into members, ignoring nested punctuation.

**Returns:** `list[str]` - 

### `_object_fields` 

```python
def _object_fields(body: str) -> dict[str, bool]
```

Map member name -&gt; required, for one object type body.

**Returns:** `dict[str, bool]` - 

### `_resolve_alias` 

```python
def _resolve_alias(source: str, name: str) -> str | None
```

The object body of a same-file ``interface``/``type`` declaration.

**Returns:** `str | None` - 

### `_props_type_text` 

```python
def _props_type_text(source: str, component: str) -> str | None
```

The type expression annotating ``component``'s destructured props.

**Returns:** `str | None` - 

### `component_prop_names` 

```python
def component_prop_names(source: str, component: str) -> dict[str, bool] | None
```

Map ``component``'s prop names to whether they are required.

Handles both an inline destructured annotation and a named ``Props``
interface or type alias declared in the same file. Returns ``None`` when
the component is not declared in ``source``.

**Returns:** `dict[str, bool] | None` - 

### `component_object_field_names` 

```python
def component_object_field_names(source: str, component: str) -> dict[str, set[str]]
```

For each object-shaped prop, the field names it carries.

A prop typed ``Array<{ ... }>`` or ``SomeAlias[]`` declares a shape the
manifest also spells out, so the two shapes have to agree too - that is
how ``ApiReferenceIndex`` came to name four fields its component never
reads.

**Returns:** `dict[str, set[str]]` - 

### `_type_expression_fields` 

```python
def _type_expression_fields(source: str, type_text: str) -> set[str]
```

Field names of the first object shape a type expression resolves to.

**Returns:** `set[str]` - 

### `_manifest_field_names` 

```python
def _manifest_field_names(type_text: str) -> set[str]
```

**Returns:** `set[str]` - 

### `check_component_prop_drift` 

```python
def check_component_prop_drift(components_dir: Path) -> list[str]
```

Compare each builtin's declared props against its component source.

Reports manifest props the component does not accept, component props the
manifest omits, optionality mismatches, and object-shape field mismatches.
Components whose source cannot be found or parsed are skipped rather than
reported, so a refactor to a new declaration style degrades to no guard
instead of a false alarm.

**Returns:** `list[str]` -
