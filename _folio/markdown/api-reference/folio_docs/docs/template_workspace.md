# folio_docs.docs.template_workspace 

## Classes

### `__init__` 

```python
def __init__(template_dir: str | Path, build_dir: str | Path, content_dir: str | Path | None = None) -> None
```

**Returns:** `None` - 

### `prepare` 

```python
def prepare(clean: bool = False) -> None
```

**Returns:** `None` - 

### `_remove_template_content` 

```python
def _remove_template_content() -> None
```

**Returns:** `None` - 

### `__init__` 

```python
def __init__(config: Config, build_dir: str | Path) -> None
```

**Returns:** `None` - 

### `_record_injected` 

```python
def _record_injected(path: Path) -> None
```

Track a build file the injector actually wrote to, for the summary.

**Returns:** `None` - 

### `_note_skip` 

```python
def _note_skip(target: str, reason: str) -> None
```

Log that an optional injection target was skipped.

Required markers/files are pre-validated in

**Returns:** `None` - 

### `_plugin_view_owns_root` 

```python
def _plugin_view_owns_root() -> bool
```

Check if a plugin view owns the root route (/).

Plugin sections conventionally expose public views through
``routes.public``. Inspect every normalized plugin section instead of
naming a product-specific key, so optional integrations remain outside
the Docs runtime boundary.

When a plugin view owns `/`, the injector skips the docs-index wrapper at
`app/page.tsx`, sets the docs canonical path to "/docs/", and includes
the docs index in the sitemap (no duplicate roots).

**Returns:** `bool` - 

### `inject` 

```python
def inject() -> None
```

**Returns:** `None` - 

### `_docs_route_base` 

```python
def _docs_route_base() -> str
```

**Returns:** `str` - 

### `_docs_route_with_trailing_slash` 

```python
def _docs_route_with_trailing_slash() -> str
```

**Returns:** `str` - 

### `_docs_route_path` 

```python
def _docs_route_path(suffix: str) -> str
```

**Returns:** `str` - 

### `_docs_route_segments` 

```python
def _docs_route_segments() -> list[str]
```

**Returns:** `list[str]` - 

### `_docs_app_import_path` 

```python
def _docs_app_import_path() -> str
```

**Returns:** `str` - 

### `_apply_theme_package` 

```python
def _apply_theme_package() -> None
```

**Returns:** `None` - 

### `_inject_root_layout` 

```python
def _inject_root_layout(name: str) -> None
```

**Returns:** `None` - 

### `_inject_favicon` 

```python
def _inject_favicon(name: str) -> None
```

**Returns:** `None` - 

### `_write_template_context` 

```python
def _write_template_context() -> None
```

**Returns:** `None` - 

### `_inject_docs_layout` 

```python
def _inject_docs_layout(name: str) -> None
```

**Returns:** `None` - 

### `_inject_project_header_logo` 

```python
def _inject_project_header_logo(content: str, name: str) -> str
```

**Returns:** `str` - 

### `_inject_project_header_actions` 

```python
def _inject_project_header_actions(content: str) -> str
```

**Returns:** `str` - 

### `_inject_docs_route_page` 

```python
def _inject_docs_route_page(name: str) -> None
```

**Returns:** `None` - 

### `_inject_previews_page` 

```python
def _inject_previews_page(name: str) -> None
```

**Returns:** `None` - 

### `_inject_docs_repo_link` 

```python
def _inject_docs_repo_link(content: str) -> str
```

**Returns:** `str` - 

### `_inject_search_config` 

```python
def _inject_search_config(content: str) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_inject_layout_search_null` 

```python
def _inject_layout_search_null(content: str) -> str
```

**Returns:** `str` - 

`@staticmethod`

### `_inject_search_command_import` 

```python
def _inject_search_command_import(content: str) -> str
```

**Returns:** `str` - 

### `_inject_layout_search_component` 

```python
def _inject_layout_search_component(content: str) -> str
```

**Returns:** `str` - 

### `_inject_og_image` 

```python
def _inject_og_image(name: str) -> None
```

**Returns:** `None` - 

### `_inject_landing_page` 

```python
def _inject_landing_page(name: str) -> None
```

**Returns:** `None` - 

### `_inject_landing_navbar` 

```python
def _inject_landing_navbar(name: str) -> None
```

Fill the navbar's placeholders, landing or no landing.

This used to live inside ``_inject_landing_page``, behind its
``landing_enabled`` gate. But ``PublicLayout`` renders
``LandingNavbar`` on every public plugin view, so a project with a
board and no ``landing:`` key shipped a navbar still containing
``__PROJECT_NAME_JSON__`` and died at prerender with a
ReferenceError. The navbar belongs to the site, not to the landing
page.

Every value below is a config read with its own fallback, so this is
correct whether or not the landing is enabled.

**Returns:** `None` - 

### `_default_landing_sections` 

```python
def _default_landing_sections(features: list[dict]) -> list[dict]
```

**Returns:** `list[dict]` - 

### `_inject_docs_index_page` 

```python
def _inject_docs_index_page() -> None
```

**Returns:** `None` - 

### `_inject_sitemap` 

```python
def _inject_sitemap() -> None
```

**Returns:** `None` - 

### `_inject_search_postbuild` 

```python
def _inject_search_postbuild() -> None
```

**Returns:** `None` - 

### `_is_package_owned` 

```python
def _is_package_owned(rel_path: str) -> bool
```

True when the theme.package overlay already ships this file.

**Returns:** `bool` - 

### `_inject_theme_config` 

```python
def _inject_theme_config() -> None
```

**Returns:** `None` - 

### `_write_project_theme_module` 

```python
def _write_project_theme_module() -> None
```

**Returns:** `None` - 

### `_inject_theme_configurator_mount` 

```python
def _inject_theme_configurator_mount() -> None
```

**Returns:** `None` - 

### `_inject_i18n` 

```python
def _inject_i18n() -> None
```

**Returns:** `None` - 

### `_configured_base_path` 

```python
def _configured_base_path() -> str
```

**Returns:** `str` - 

### `_inject_versions` 

```python
def _inject_versions() -> None
```

**Returns:** `None` - 

### `_relocate_docs_route` 

```python
def _relocate_docs_route() -> None
```

**Returns:** `None` - 

`@staticmethod`

### `_remove_nested_relocation_residue` 

```python
def _remove_nested_relocation_residue(source: Path, target: Path) -> None
```

Drop leftovers of a previous relocation nested inside ``source``.

With a route base nested under ``/docs`` (e.g. ``/docs/v2``), a warm
rebuild merges the template's ``app/docs`` over a ``.build`` tree whose
``app/docs`` still contains the previously relocated route dir. Without
this cleanup the whole tree — old relocated copy included — is moved
again, nesting one level deeper on every warm rebuild
(``app/docs/v2/v2/...``). A directory at the nested target that holds
the docs catch-all page can only be such residue: the relocation itself
put it there, so remove the residue chain before relocating again.

**Returns:** `None` - 

## Functions

### `_namespace_style_key` 

```python
def _namespace_style_key(key: str) -> str
```

**Returns:** `str` - 

### `validate_template_marker_contract` 

```python
def validate_template_marker_contract(template_dir: str | Path) -> list[tuple[str, str]]
```

Return ``(file, marker)`` pairs whose required marker is missing.

Each load-bearing marker in :data:`REQUIRED_INJECTION_MARKERS` must be
present verbatim in its expected file. A missing file surfaces every marker
it owns as missing, mirroring the "missing required files" / MDX-contract
checks so a custom template fails fast instead of building with silently
dropped project metadata.

**Returns:** `list[tuple[str, str]]` - 

### `copytree_ignore` 

```python
def copytree_ignore()
```

Ignore callable for every template/theme/overlay ``copytree`` call.

Single-sourced from :data:`_COPY_IGNORED_DIRS` (plus the staging marker
file) so the symlink scan and the copy can never drift apart.

### `_walk_copied_entries` 

```python
def _walk_copied_entries(root: Path)
```

Yield every path under ``root`` that a Folio copytree would copy.

Uses ``os.walk`` and prunes :data:`_COPY_IGNORED_DIRS` in place so large
excluded trees (``node_modules``, ``.git``, ...) are never descended into.
Directories are yielded before their contents.

### `_reject_symlinks` 

```python
def _reject_symlinks(root: Path, label: str) -> None
```

Raise if any copied entry under ``root`` is a symlink.

``shutil.copytree`` dereferences symlinks (``symlinks=False``), so an
untrusted tree containing a symlink could copy files from outside the tree
into the published site. Scan the tree and refuse to copy if any symlink is
present. Entries inside directories excluded from the copy are skipped, since
they are never published.

**Returns:** `None` - 

### `collect_copyable_files` 

```python
def collect_copyable_files(root: Path, label: str) -> set[Path]
```

Collect copied file paths (relative to ``root``) in a single traversal.

Combines the symlink rejection of :func:`_reject_symlinks` with file
collection so callers that need both (e.g. the theme.package overlay) walk
the tree once instead of twice. Raises ``ValueError`` on the first symlink.

**Returns:** `set[Path]` - 

### `_theme_radius_index` 

```python
def _theme_radius_index(radius: str) -> int
```

**Returns:** `int` - 

### `_has_project_theme_preset` 

```python
def _has_project_theme_preset(config: Config) -> bool
```

**Returns:** `bool` - 

### `_project_theme_default_config` 

```python
def _project_theme_default_config(config: Config) -> dict[str, object]
```

**Returns:** `dict[str, object]` - 

### `_project_theme_default_options` 

```python
def _project_theme_default_options(config: Config) -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_project_theme_controls` 

```python
def _project_theme_controls(config: Config) -> list[dict[str, object]]
```

**Returns:** `list[dict[str, object]]` - 

### `_project_theme_variant_themes` 

```python
def _project_theme_variant_themes(config: Config) -> dict[str, dict[str, object]]
```

**Returns:** `dict[str, dict[str, object]]` - 

### `_project_theme_option_preview` 

```python
def _project_theme_option_preview(option: dict[str, Any]) -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_project_theme_style` 

```python
def _project_theme_style(config: Config) -> dict[str, str]
```

**Returns:** `dict[str, str]` - 

### `_render_project_header_logo` 

```python
def _render_project_header_logo(config: Config, fallback_name: str) -> str
```

**Returns:** `str` - 

### `_has_project_header_actions` 

```python
def _has_project_header_actions(config: Config) -> bool
```

**Returns:** `bool` - 

### `_render_project_header_actions` 

```python
def _render_project_header_actions(config: Config) -> str
```

**Returns:** `str` - 

### `_render_project_theme_module` 

```python
def _render_project_theme_module(config: Config) -> str
```

**Returns:** `str` - 

### `resolve_base_path` 

```python
def resolve_base_path(config: Config, env: Mapping[str, str] | None = None) -> str
```

**Returns:** `str` - 

### `_is_github_pages_deploy` 

```python
def _is_github_pages_deploy(config: Config, env: Mapping[str, str]) -> bool
```

**Returns:** `bool` - 

### `_github_pages_base_path` 

```python
def _github_pages_base_path(repository: str) -> str
```

**Returns:** `str` -
