# folio_docs.docs.mdx_writer 

## Functions

### `_escape_mdx_text` 

```python
def _escape_mdx_text(text: str) -> str
```

**Returns:** `str` - 

### `_escape_mdx_outside_inline_code` 

```python
def _escape_mdx_outside_inline_code(text: str) -> str
```

**Returns:** `str` - 

### `_code_fence_flags` 

```python
def _code_fence_flags(lines: list[str]) -> list[bool]
```

Mark which lines belong to a fenced code block, fence lines included.

Only a run of the opener's own character, at least as long and carrying no
info string, closes a block. Toggling on any ``` prefix instead would let a
3-tick fence nested inside a 4-tick one flip the tracker back to "outside
code" and escape real code content.

**Returns:** `list[bool]` - 

### `_escape_mdx` 

```python
def _escape_mdx(text: str) -> str
```

Escape MDX syntax in docstring prose, leaving code alone.

MDX parses `{` and `<` as expression and JSX delimiters, so prose has to
escape them. Code is different: CommonMark treats the content of a fenced
block or a backtick span as literal text and decodes neither backslash
escapes nor HTML entities there, so escaping inside code renders the
escape itself - `/\{repo\}` instead of `/{repo}`.

**Returns:** `str` - 

### `_escape_jsx_attr` 

```python
def _escape_jsx_attr(text: str) -> str
```

**Returns:** `str` - 

### `_frontmatter` 

```python
def _frontmatter(data: dict[str, str]) -> str
```

Generate a YAML frontmatter block.

**Returns:** `str` - 

### `_render_param_table` 

```python
def _render_param_table(func: FunctionIR, symbol_index: dict[str, str] | None = None, current_module: str = '') -> str
```

Render a &lt;ParamTable&gt; JSX component for a function's arguments.

**Returns:** `str` - 

### `_effective_source_ref` 

```python
def _effective_source_ref(repo_url: str, source_ref: str | None = None) -> str
```

**Returns:** `str` - 

### `_source_link` 

```python
def _source_link(repo_url: str, source_file: str, line_number: int, source_root: str = '', source_ref: str | None = None) -> str
```

**Returns:** `str` - 

### `_render_function` 

```python
def _render_function(func: FunctionIR, heading_level: int = 3, repo_url: str = '', source_root: str = '', source_ref: str | None = None, symbol_index: dict[str, str] | None = None, current_module: str = '') -> str
```

Render a full function section in MDX.

**Returns:** `str` - 

### `_render_class` 

```python
def _render_class(heading_level: int = 3, repo_url: str = '', source_root: str = '', source_ref: str | None = None, symbol_index: dict[str, str] | None = None, current_module: str = '') -> str
```

Render a full class section in MDX.

**Returns:** `str` - 

### `api_reference_index_to_mdx` 

```python
def api_reference_index_to_mdx(modules: list[ModuleIR]) -> str
```

Render the generated source code overview page.

**Returns:** `str` - 

### `module_to_mdx` 

```python
def module_to_mdx(module: ModuleIR, repo_url: str = '', source_root: str = '', source_ref: str | None = None, symbol_index: dict[str, str] | None = None) -> str
```

Convert a ModuleIR into an MDX string.

**Returns:** `str` - 

### `_escape_curly_outside_math` 

```python
def _escape_curly_outside_math(line: str) -> str
```

Escape bare curly braces, preserving inline math and inline code.

MDX leaves both alone, and CommonMark decodes no backslash escape inside a
backtick span, so escaping there renders the backslashes to the reader.

**Returns:** `str` - 

### `_strip_relative_images` 

```python
def _strip_relative_images(content: str) -> str
```

**Returns:** `str` - 

### `_convert_mermaid_blocks` 

```python
def _convert_mermaid_blocks(content: str) -> str
```

Convert fenced ```mermaid code blocks into &lt;Mermaid chart="..." /&gt; JSX.

Only converts top-level mermaid blocks. Blocks nested inside an outer
fenced code block (4+ backticks, e.g. ````md) are left untouched so that
documentation examples are preserved as-is.

**Returns:** `str` - 

### `_sanitize_for_mdx` 

```python
def _sanitize_for_mdx(content: str) -> str
```

**Returns:** `str` - 

### `markdown_to_mdx` 

```python
def markdown_to_mdx(result: MarkdownResult) -> str
```

Wrap markdown content with frontmatter to produce MDX.

**Returns:** `str` -
