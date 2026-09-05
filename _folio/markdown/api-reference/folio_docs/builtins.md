# folio_docs.builtins 

Single source of truth for Folio's builtin MDX components.

These components ship inside the bundled Next/Nextra template
(``template/components/``) and are registered into the

## Functions

### `_component` 

```python
def _component(name: str, module: str, *, props: dict[str, str] | None = None, required: bool = False, category: str = 'component-catalog', contract: bool = False, source_label: str = '') -> ComponentDefinition
```

**Returns:** [`ComponentDefinition`](/docs/api-reference/folio_docs/extensions#componentdefinition) - 

### `register_builtin_components` 

```python
def register_builtin_components(registry: ExtensionRegistry) -> None
```

Register every builtin component into ``registry`` in manifest order.

**Returns:** `None` -
