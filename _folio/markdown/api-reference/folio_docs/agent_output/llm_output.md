# folio_docs.agent_output.llm_output 

## Functions

### `_inline` 

```python
def _inline(text: object) -> str
```

Collapse a value onto a single line of plain text.

**Returns:** `str` - 

### `_table_cell` 

```python
def _table_cell(text: object) -> str
```

**Returns:** `str` - 

### `_absolute_link` 

```python
def _absolute_link(path: str, site_url: str = '') -> str
```

**Returns:** `str` - 

### `_doc_link` 

```python
def _doc_link(route: str, site_url: str = '', docs_route_base: str = '/docs') -> str
```

**Returns:** `str` - 

### `_api_link` 

```python
def _api_link(module_name: str, site_url: str = '', docs_route_base: str = '/docs') -> str
```

**Returns:** `str` - 

### `_source_citation` 

```python
def _source_citation(source_file: str, line_number: int, project_dir: str = '') -> str
```

Render a `path:line` citation, relative to the project directory.

**Returns:** `str` - 

### `_heading_block` 

```python
def _heading_block(heading: str, citation: str = '', url: str = '') -> str
```

**Returns:** `str` - 

### `_prose_blocks` 

```python
def _prose_blocks(docstring: DocstringIR) -> list[str]
```

**Returns:** `list[str]` - 

### `_tail_blocks` 

```python
def _tail_blocks(docstring: DocstringIR) -> list[str]
```

**Returns:** `list[str]` - 

### `_arg_table` 

```python
def _arg_table(func: FunctionIR) -> str
```

Render the argument table for a function, or an empty string.

**Returns:** `str` - 

### `_function_blocks` 

```python
def _function_blocks(func: FunctionIR, heading: str, project_dir: str) -> list[str]
```

**Returns:** `list[str]` - 

### `_class_blocks` 

```python
def _class_blocks(project_dir: str) -> list[str]
```

**Returns:** `list[str]` - 

### `_module_blocks` 

```python
def _module_blocks(mod: ModuleIR, config: Config | None) -> list[str]
```

**Returns:** `list[str]` - 

### `_doc_blocks` 

```python
def _doc_blocks(doc: MarkdownResult, config: Config | None) -> list[str]
```

Split a document into its heading block and its Markdown body.

**Returns:** `list[str]` - 

### `generate_llms_txt` 

```python
def generate_llms_txt(config: Config, modules: list[ModuleIR], docs: list[MarkdownResult]) -> str
```

Generate llmstxt.org format with project name, doc links, API reference links.

**Returns:** `str` - 

### `generate_llms_full_txt` 

```python
def generate_llms_full_txt(modules: list[ModuleIR], docs: list[MarkdownResult], config: Config | None = None) -> str
```

Generate full content concatenated, separated by ---.

When ``config`` is supplied every section carries the page URL it was built
from, so an agent reading the file can cite the published page.

**Returns:** `str` -
