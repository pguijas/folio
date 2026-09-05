# folio_docs.parser.markdown_parser 

## Classes

## Functions

### `_extract_first_paragraph` 

```python
def _extract_first_paragraph(content: str) -> str
```

**Returns:** `str` - 

### `parse_markdown_file` 

```python
def parse_markdown_file(path: Path) -> MarkdownResult
```

**Returns:** [`MarkdownResult`](/docs/api-reference/folio_docs/parser/markdown_parser#markdownresult) - 

### `source_route` 

```python
def source_route(relative: Path) -> str
```

The route a docs source publishes for a Markdown file at ``relative``.

One rule, shared with everything that names a published page (the kanban
plugin resolves ``doc:`` artifacts through it): the ``.md`` suffix comes
off, and a README is its folder's page.

**Returns:** `str` - 

### `parse_markdown_directory` 

```python
def parse_markdown_directory(directory: str, route_prefix: str = '') -> list[MarkdownResult]
```

**Returns:** [`list[MarkdownResult]`](/docs/api-reference/folio_docs/parser/markdown_parser#markdownresult) -
