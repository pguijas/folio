# folio_docs.agent_output.markdown 

Markdown mirrors for Folio for Agents.

The human site may use MDX components. Agent mirrors deliberately keep the
authored prose and code while reducing that component shell to plain Markdown.

## Functions

### `mdx_to_markdown` 

```python
def mdx_to_markdown(content: str) -> str
```

Convert generated MDX into the lossy, agent-readable mirror format.

**Returns:** `str` - 

### `_strip_mdx_component_tags` 

```python
def _strip_mdx_component_tags(content: str) -> str
```

Remove PascalCase JSX tags while retaining useful child prose.

**Returns:** `str` - 

### `_mdx_tag_end` 

```python
def _mdx_tag_end(content: str, cursor: int) -> int | None
```

**Returns:** `int | None` - 

### `_mdx_string_prop` 

```python
def _mdx_string_prop(tag: str, name: str) -> str
```

**Returns:** `str` - 

### `_mdx_tag_markdown` 

```python
def _mdx_tag_markdown(tag: str, *, name: str, closing: bool) -> str
```

**Returns:** `str` -
