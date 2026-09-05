# folio_docs.docs.theme_contract_codegen 

Generate TypeScript type definitions from Python theme contract.

This module provides code generation for TypeScript theme types that are
consumed by template/theme/preset-types.ts and written into build workspaces.

## Functions

### `generate_typescript_contract` 

```python
def generate_typescript_contract() -> str
```

Generate TypeScript type definitions from the Python theme contract.

**Returns:** `str` - TypeScript source code defining ThemeStyle, ThemeTuneKey, ThemeVars,
and themeRadiusScale.
