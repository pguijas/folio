# folio_docs.build 

## Classes

### `__init__` 

```python
def __init__() -> None
```

**Returns:** `None` - 

### `__enter__` 

```python
def __enter__() -> '_BuildOutputStream'
```

**Returns:** `'_BuildOutputStream'` - 

### `__exit__` 

```python
def __exit__(exc_type, exc, traceback) -> None
```

**Returns:** `None` - 

### `record` 

```python
def record(line: str) -> None
```

**Returns:** `None` - 

## Functions

### `_find_template_dir` 

```python
def _find_template_dir() -> Path
```

**Returns:** `Path` - 

### `_validate_template_contract` 

```python
def _validate_template_contract(template_dir: Path, label: str) -> None
```

Validate a resolved template directory against the Folio contract.

Applies the required-files, MDX-component, and injection-marker checks to a
directory that Folio will copy into ``.build/``. ``label`` names the config
key (``template.path`` or the merged ``template.overlay_path`` result) so
errors point at the right surface.

**Returns:** `None` - 

### `_check_bundled_template_drift` 

```python
def _check_bundled_template_drift(template_dir: Path) -> None
```

Fail the build when the bundled template drifted from the manifest.

Bundled-template builds inject builtin components from

**Returns:** `None` - 

### `_resolve_overlay_dir` 

```python
def _resolve_overlay_dir(project_dir: Path, config: Config) -> Path
```

Resolve ``template.overlay_path`` against the project root.

Applies the same containment guards as ``template.path`` via

**Returns:** `Path` - 

### `_materialize_overlay_template` 

```python
def _materialize_overlay_template(bundled_dir: Path, overlay_dir: Path, staging_dir: Path) -> Path
```

Build a merged template = bundled template + overlay files on top.

Copies the bundled template into ``staging_dir``, then copies the user's
overlay files over it (user wins, missing files fall back to the bundled
template). The overlay is scanned for symlinks first — ``shutil.copytree``
dereferences them, so an untrusted overlay could otherwise pull files from
outside the tree into the published site. The build directories that are
never published are excluded from both the scan and the copy (so a symlink
under e.g. the overlay's ``content/`` is never copied either).

The staging dir is recreated on every build, so two guards protect user
data: the overlay may not live inside the staging dir, and an existing
staging dir is only removed when it carries the Folio staging marker file
(proving a previous Folio build created it).

**Returns:** `Path` - 

### `_resolve_template_dir` 

```python
def _resolve_template_dir(project_dir: Path, config: Config, *, build_dir: Path | None = None) -> Path
```

**Returns:** `Path` - 

### `_hash_file` 

```python
def _hash_file(path: Path) -> str
```

**Returns:** `str` - 

### `_hash_tree` 

```python
def _hash_tree(root: Path) -> str
```

**Returns:** `str` - 

### `_theme_package_signature` 

```python
def _theme_package_signature(resolved: Config) -> str
```

Signature of the resolved theme.package tree (empty when unset).

Folded into the manifest ``build`` context and compared against the previous
build so that changing/removing ``theme.package`` triggers a scoped prune of
the overlaid files in ``.build/`` (the theme is copied with
``copytree(dirs_exist_ok=True)`` and would otherwise leave orphans).

Collects the copyable files and rejects symlinks in a single traversal
(``collect_copyable_files``), then feeds the hash from that file list
instead of re-walking the tree.

**Returns:** `str` - 

### `_prune_stale_build_overlay` 

```python
def _prune_stale_build_overlay(prev_manifest: dict, build_dir: Path, build_context: dict[str, str]) -> None
```

Prune orphaned overlay files when template/theme/route inputs changed.

``prepare()`` overlays the template (and any ``theme.package``) with
``copytree(dirs_exist_ok=True)`` and never removes files that vanished from
the source. When a warm ``.build/`` was produced from a *different* template
or theme, delete everything under it except the preserved entries before
``prepare`` re-copies, so stale files cannot survive into the published site.

When only ``template.docs_route_base`` changed, remove the docs route dir
that the previous build relocated to — nothing else re-copies over it, so it
would otherwise stay published at the old URL.

**Returns:** `None` - 

### `_remove_relocated_docs_route` 

```python
def _remove_relocated_docs_route(build_dir: Path, route_base: str) -> None
```

Remove the docs route dir relocated for a previous ``docs_route_base``.

Template preparation moves ``app/docs`` to ``app/<route segments>``. When
the configured route base changes between warm builds, the previously
relocated dir is not overwritten by ``prepare`` (which only re-copies
``app/docs``), so it must be dropped explicitly — together with any parent
directories the old relocation created that are now empty.

**Returns:** `None` - 

### `_build_manifest_context` 

```python
def _build_manifest_context(config_path: Path, template_dir: Path, source_ref: str, theme_package_signature: str = '', docs_route_base: str = '/docs') -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_print_banner` 

```python
def _print_banner(config: Config, *, include_news: bool = True) -> None
```

**Returns:** `None` - 

### `_count_phrase` 

```python
def _count_phrase(count: int, singular: str, plural: str | None = None) -> str
```

**Returns:** `str` - 

### `_step_description` 

```python
def _step_description(label: str, detail: str) -> str
```

**Returns:** `str` - 

### `_print_step` 

```python
def _print_step(label: str, detail: str, *, marker: str = '✓', marker_style: str = 'green', label_style: str = 'bold') -> None
```

**Returns:** `None` - 

### `_print_step_detail` 

```python
def _print_step_detail(detail: str, *, style: str = 'dim') -> None
```

**Returns:** `None` - 

### `_build_output_panel` 

```python
def _build_output_panel(lines: list[str]) -> Panel
```

**Returns:** `Panel` - 

### `_print_build_output` 

```python
def _print_build_output(lines: list[str]) -> None
```

**Returns:** `None` - 

### `_warn_missing_assets` 

```python
def _warn_missing_assets(missing: list[str], route: str) -> None
```

**Returns:** `None` - 

### `_copy_doc_assets` 

```python
def _copy_doc_assets(builder: SiteBuilder, doc: MarkdownResult) -> list[str]
```

Carry a page's local images into the content tree beside it.

An author writes ``![The board](board.png)`` next to their Markdown. MDX
turns that into a module import resolved against the generated ``.mdx``,
so unless the file travels with the page the build fails outright. Only
project-local paths move: an absolute URL, a root-relative path and a
data URI are all left for the browser to resolve.

**Returns:** `list[str]` - 

### `_path_traverses_symlink` 

```python
def _path_traverses_symlink(root: Path, target: Path) -> bool
```

Whether ``target`` crosses a symlink at or below lexical ``root``.

**Returns:** `bool` - 

### `_parse_project_sources` 

```python
def _parse_project_sources(resolved: Config, verbose: bool, plugin_views: int = 0, plugin_manager: PluginManager | None = None) -> BuildSources
```

**Returns:** [`BuildSources`](/docs/api-reference/folio_docs/build#buildsources) - 

### `_collect_plugin_docs` 

```python
def _collect_plugin_docs(plugin_manager: PluginManager | None, config: Config) -> list[MarkdownResult]
```

Parse plugin-contributed Markdown through the core document parser.

**Returns:** [`list[MarkdownResult]`](/docs/api-reference/folio_docs/parser/markdown_parser#markdownresult) - 

### `_reject_duplicate_doc_routes` 

```python
def _reject_duplicate_doc_routes(docs: list[MarkdownResult]) -> None
```

**Returns:** `None` - 

### `_canonical_doc_route` 

```python
def _canonical_doc_route(route: str) -> str
```

Mirror the public docs router's aliases for collision detection.

**Returns:** `str` - 

### `_prepare_builder` 

```python
def _prepare_builder(builder: SiteBuilder, build_dir: Path, build_context: dict[str, str], prev_manifest: dict, *, clean: bool) -> None
```

**Returns:** `None` - 

### `_write_meta_pages` 

```python
def _write_meta_pages(builder: SiteBuilder, config: Config, modules: list[ModuleIR], docs: list[MarkdownResult]) -> None
```

**Returns:** `None` - 

### `_published_modules` 

```python
def _published_modules(modules: list[ModuleIR]) -> list[ModuleIR]
```

**Returns:** [`list[ModuleIR]`](/docs/api-reference/folio_docs/ir#moduleir) - 

### `_published_docs` 

```python
def _published_docs(docs: list[MarkdownResult]) -> list[MarkdownResult]
```

**Returns:** [`list[MarkdownResult]`](/docs/api-reference/folio_docs/parser/markdown_parser#markdownresult) - 

### `_generate_content_pages` 

```python
def _generate_content_pages(*, builder: SiteBuilder, config: Config, modules: list[ModuleIR], docs: list[MarkdownResult], project_dir: Path, build_context: dict[str, str], clean: bool, verbose: bool, prev_manifest: dict | None = None) -> GenerationResult
```

**Returns:** [`GenerationResult`](/docs/api-reference/folio_docs/build#generationresult) - 

### `build_registry` 

```python
def build_registry(pm: object, resolved: Config) -> ExtensionRegistry
```

Assemble the extension registry for a build.

Registration order: builtin layouts/components first, then config
``components:``, then plugin hooks. A config or plugin component may
shadow a builtin of the same name (the builtin is replaced and a
``UserWarning`` is emitted); a duplicate between two non-builtin
registrations raises ``ValueError``. Builtins are registered through the
same :class:`ExtensionRegistry` API that plugins use, but via a
deterministic direct call (not a pluggy hook) so emission order is stable.

**Returns:** [`ExtensionRegistry`](/docs/api-reference/folio_docs/extensions#extensionregistry) - 

### `_apply_extensions` 

```python
def _apply_extensions(builder: SiteBuilder, pm: object, resolved: Config, registry: ExtensionRegistry | None = None) -> None
```

**Returns:** `None` - 

### `_check_generated_links` 

```python
def _check_generated_links(builder: SiteBuilder, modules: list[ModuleIR], docs: list[MarkdownResult]) -> list
```

**Returns:** `list` - 

### `_build_timestamp` 

```python
def _build_timestamp() -> str
```

This build's UTC start-of-finalize time, for generated metadata.

**Returns:** `str` - 

### `_finalize_generated_files` 

```python
def _finalize_generated_files(*, builder: SiteBuilder, pm: object, resolved: Config, generation: GenerationResult, project_dir: Path, serve: bool, registry: ExtensionRegistry | None = None) -> bool
```

**Returns:** `bool` - 

### `_check_generated_links_with_progress` 

```python
def _check_generated_links_with_progress(builder: SiteBuilder, modules: list[ModuleIR], docs: list[MarkdownResult]) -> list
```

**Returns:** `list` - 

### `_install_dependencies` 

```python
def _install_dependencies(builder: SiteBuilder) -> bool
```

**Returns:** `bool` - 

### `_export_static_site` 

```python
def _export_static_site(*, builder: SiteBuilder, config: Config, resolved: Config, modules: list[ModuleIR], docs: list[MarkdownResult], pm: object) -> ExportResult
```

**Returns:** [`ExportResult`](/docs/api-reference/folio_docs/build#exportresult) - 

### `_write_llm_outputs` 

```python
def _write_llm_outputs(*, builder: SiteBuilder, config: Config, resolved: Config, modules: list[ModuleIR], docs: list[MarkdownResult], serve: bool = False) -> int
```

Render configured LLM outputs to the active site's public root.

**Returns:** `int` - 

### `_start_dev_server` 

```python
def _start_dev_server(*, builder: SiteBuilder, config: Config, resolved: Config, project_dir: Path, port: int, open_browser: bool, verbose: bool, kill_existing: bool, plugin_manager: object | None = None) -> None
```

**Returns:** `None` - 

### `run_build` 

```python
def run_build(project_dir: Path, serve: bool = False, verbose: bool = False, config_file: str = 'docs.yaml', port: int = 4321, open_browser: bool = False, clean: bool = False, output_override: str = '', current_version_path: str = '', include_versions: bool = False, build_dir_override: str | Path = '', source_ref_override: str = '', quiet: bool = False, kill_existing: bool = False) -> None
```

**Returns:** `None` -
