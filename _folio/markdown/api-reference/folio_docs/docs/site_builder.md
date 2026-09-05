# folio_docs.docs.site_builder 

## Classes

### `__init__` 

```python
def __init__(config: Config, template_dir: str, build_dir: str, verbose: bool = False) -> None
```

**Returns:** `None` - 

`@property`

### `manifest_path` 

```python
manifest_path
```

**Type:** `Path` - 

### `load_manifest` 

```python
def load_manifest() -> dict
```

**Returns:** `dict` - 

### `save_manifest` 

```python
def save_manifest(manifest: dict) -> None
```

**Returns:** `None` - 

### `prepare` 

```python
def prepare(clean: bool = False) -> None
```

**Returns:** `None` - 

### `view_routes` 

```python
def view_routes() -> set[str]
```

Site-absolute routes of registry views (e.g. \{"/roadmap"\}).

Recorded by apply_extensions; valid link targets for check_links.

**Returns:** `set[str]` - 

### `apply_extensions` 

```python
def apply_extensions(registry: object) -> None
```

**Returns:** `None` - 

### `_write_mdx_contract_module` 

```python
def _write_mdx_contract_module(components: Iterable[ComponentDefinition]) -> None
```

Rewrite lib/folio-mdx-contract.ts from the live registry.

Template preparation writes the module before any plugin has run, so
the version it writes can only describe the builtin manifest. Once the
registry exists, the config and plugin components flagged
``contract=True`` belong in it too — and the same set is what
``write_authoring_contract`` publishes.

**Returns:** `None` - 

### `write_authoring_contract` 

```python
def write_authoring_contract(config_keys: Iterable[str], generated_at: str) -> Path
```

Publish the authoring contract as a static file in the export.

Written under the workspace ``public/`` directory, which the Next
static export carries through unchanged — the same route the per-page
Markdown mirrors take. Call it after the extensions are applied, so
the component list and the emitted routes are complete.

**Returns:** `Path` - 

### `_runtime` 

```python
def _runtime() -> NextRuntime
```

**Returns:** [`NextRuntime`](/docs/api-reference/folio_docs/docs/next_runtime#nextruntime) - 

### `write_page` 

```python
def write_page(route: str, content: str) -> None
```

**Returns:** `None` - 

### `copy_page_asset` 

```python
def copy_page_asset(route: str, relative: str, source: Path) -> None
```

Copy a file a page references to sit beside the generated page.

MDX compiles ``![alt](shot.png)`` into ``import __img0 from
"shot.png"``, resolved relative to the generated ``.mdx``. Without the
file beside it the build does not merely lose the image, it fails:
"Module not found: Can't resolve 'shot.png'". So a documentation page
that shows a screenshot has to carry the screenshot into the content
tree, at the same relative path the author wrote.

**Returns:** `None` - 

### `copy_static_asset` 

```python
def copy_static_asset(relative: str, source: Path) -> None
```

Copy a file into ``public/``, where the site serves it verbatim.

``copy_page_asset`` puts a file beside a generated page so MDX can

how a plugin publishes something it does not own a page for, in the
same tree as ``/_folio/markdown/<route>.md`` and the preview examples.
The file is served exactly as it is on disk, so nothing here renders,
rewrites, or interprets it.

**Returns:** `None` - 

### `remove_static_tree` 

```python
def remove_static_tree(relative: str) -> None
```

Drop a subtree of ``public/`` before republishing it.

Warm builds keep the workspace, so a file that stopped existing in the
project would otherwise stay on the site forever — deleted from the
repository and still served. Emitters that publish a whole directory
clear it first and write what exists now.

**Returns:** `None` - 

### `register_route` 

```python
def register_route(route: str) -> None
```

Record a route as a live page so link-checking treats it as valid.

Plugins should call this for every page they own — even when they skip
``write_page`` because the page already exists from a prior build — so
internal links to plugin pages are not flagged as broken.

**Returns:** `None` - 

### `emitted_routes` 

```python
def emitted_routes() -> set[str]
```

Routes recorded via write_page/register_route since the last prepare().

**Returns:** `set[str]` - 

### `restore_emitted_routes` 

```python
def restore_emitted_routes(routes: set[str]) -> None
```

Reset the emitted-routes set to a snapshot taken via emitted_routes().

Used by the build core to roll back routes half-registered by a failed
``emit_assets`` hookimpl: a plugin that crashed between
``register_route`` and ``write_page`` must not leave a missing page
whitelisted for the link checker.

**Returns:** `None` - 

### `page_exists` 

```python
def page_exists(route: str) -> bool
```

**Returns:** `bool` - 

### `read_page` 

```python
def read_page(route: str) -> str
```

Return the current on-disk content of a page in the content dir.

Plugins use this on warm builds for write-if-changed refreshes of
pages they generated on a prior build (e.g. the openapi and kanban
plugins compare the existing page against the regenerated content
before rewriting it).

**Returns:** `str` - 

### `page_markdown_exists` 

```python
def page_markdown_exists(route: str) -> bool
```

**Returns:** `bool` - 

### `list_pages` 

```python
def list_pages(prefix: str) -> list[str]
```

Routes of the pages currently on disk under a content-dir prefix.

The counterpart of ``remove_page`` for plugins that generate a
variable set of pages: a warm build keeps the workspace, so a page
generated for something that no longer exists has to be found before
it can be dropped, and only its owner knows which marker to look for.

**Returns:** `list[str]` - 

### `remove_page` 

```python
def remove_page(route: str) -> None
```

**Returns:** `None` - 

### `write_meta` 

```python
def write_meta(directory: str, meta_json: str) -> None
```

**Returns:** `None` - 

### `read_meta` 

```python
def read_meta(directory: str) -> str
```

**Returns:** `str` - 

### `remove_meta_tree` 

```python
def remove_meta_tree(directory: str) -> None
```

**Returns:** `None` - 

### `write_llm_files` 

```python
def write_llm_files(llms_txt: str | None = None, llms_full_txt: str | None = None, *, serve: bool = False) -> None
```

**Returns:** `None` - 

### `write_preview_examples` 

```python
def write_preview_examples(examples_dir: str | Path) -> None
```

Build named documentation preview examples into public static assets.

**Returns:** `None` - 

### `_build_preview_example_project` 

```python
def _build_preview_example_project(example_dir: Path, target_dir: Path) -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_reset_preview_example_workspace` 

```python
def _reset_preview_example_workspace(example_build_dir: Path) -> None
```

**Returns:** `None` - 

### `_preview_example_base_path` 

```python
def _preview_example_base_path(example_name: str) -> str
```

**Returns:** `str` - 

### `_write_preview_example_manifest` 

```python
def _write_preview_example_manifest(example_dir: Path, target_dir: Path) -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_preview_example_source_paths` 

```python
def _preview_example_source_paths(example_dir: Path) -> list[Path]
```

**Returns:** `list[Path]` - 

### `_page_path` 

```python
def _page_path(route: str) -> Path
```

**Returns:** `Path` - 

### `_page_markdown_dir` 

```python
def _page_markdown_dir() -> Path
```

**Returns:** `Path` - 

### `_page_markdown_path` 

```python
def _page_markdown_path(route: str) -> Path
```

**Returns:** `Path` - 

### `_write_page_markdown` 

```python
def _write_page_markdown(route: str, content: str) -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_preview_example_language` 

```python
def _preview_example_language(path: Path) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_mdx_to_markdown` 

```python
def _mdx_to_markdown(content: str) -> str
```

**Returns:** `str` - 

### `write_search_index` 

```python
def write_search_index() -> None
```

Write a lightweight search index for `folio serve` development mode.

**Returns:** `None` - 

### `_content_route_to_docs_url` 

```python
def _content_route_to_docs_url(route: str) -> str
```

**Returns:** `str` - 

`@classmethod`

### `_mdx_search_title` 

```python
def _mdx_search_title(raw: str, route: str) -> str
```

**Returns:** `str` - 

`@classmethod`

### `_mdx_search_content` 

```python
def _mdx_search_content(raw: str) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_clean_search_text` 

```python
def _clean_search_text(value: str) -> str
```

**Returns:** `str` - 

### `install_deps` 

```python
def install_deps() -> bool
```

**Returns:** `bool` - 

### `build` 

```python
def build(**kwargs) -> None
```

**Returns:** `None` - 

`@staticmethod`

### `kill_port` 

```python
def kill_port(port: int) -> bool
```

**Returns:** `bool` - 

### `serve` 

```python
def serve(port: int = 4321, *, kill_existing: bool = False)
```
