# folio_docs.link_checker 

Build-time link checker for internal documentation links.

## Classes

Represents a broken internal link found during validation.

## Functions

### `_route_from_mdx_path` 

```python
def _route_from_mdx_path(mdx_path: Path, content_dir: Path) -> str
```

Derive the route string from an MDX file path relative to content_dir.

For example:
    content_dir / "installation.mdx"  -&gt; "installation"
    content_dir / "api-reference/folio/config.mdx"  -&gt; "api-reference/folio/config"
    content_dir / "index.mdx"  -&gt; "index"

**Returns:** `str` - 

### `_normalize_target` 

```python
def _normalize_target(href: str, source_route: str, docs_route_base: str = '/docs') -> str | None
```

Normalize an internal link target to a route string.

Returns the normalized route, or None if the link should be skipped
(external, anchor-only, mailto, tel, etc.).

**Returns:** `str | None` - 

### `_strip_inline_code` 

```python
def _strip_inline_code(line: str) -> str
```

**Returns:** `str` - 

### `_links_in_line` 

```python
def _links_in_line(line: str) -> list[str]
```

**Returns:** `list[str]` - 

### `_static_target_exists` 

```python
def _static_target_exists(target: str, static_root: Path | None) -> bool
```

Return whether a site-absolute URL maps to a published static asset.

**Returns:** `bool` - 

### `check_links` 

```python
def check_links(content_dir: Path, pages: list[str], docs_route_base: str = '/docs', site_routes: set[str] | None = None, static_root: Path | None = None) -> list[BrokenLink]
```

Check all MDX files in content_dir for broken internal links.

**Returns:** [`list[BrokenLink]`](/docs/api-reference/folio_docs/link_checker#brokenlink) - A list of BrokenLink instances for every internal link that doesn't
match a known page route.
