# folio_docs.cli 

## Classes

### `__init__` 

```python
def __init__(*, width: int, cursor_rows_below_news: int, initial_news_item: str, interval: float) -> None
```

**Returns:** `None` - 

### `start` 

```python
def start() -> None
```

**Returns:** `None` - 

### `stop` 

```python
def stop() -> None
```

**Returns:** `None` - 

### `add_static_lines` 

```python
def add_static_lines(count: int) -> None
```

**Returns:** `None` - 

### `set_active_prompt_lines` 

```python
def set_active_prompt_lines(count: int) -> None
```

**Returns:** `None` - 

### `clear_active_prompt_lines` 

```python
def clear_active_prompt_lines() -> None
```

**Returns:** `None` - 

### `_run` 

```python
def _run() -> None
```

**Returns:** `None` - 

### `refresh` 

```python
def refresh() -> None
```

**Returns:** `None` - 

### `__init__` 

```python
def __init__(info: dict, target: Path, repo: str, *, compact: bool, animate_news: bool) -> None
```

**Returns:** `None` - 

### `__enter__` 

```python
def __enter__() -> '_InitIntroPrinter'
```

**Returns:** `'_InitIntroPrinter'` - 

### `__exit__` 

```python
def __exit__(*exc_info: object) -> None
```

**Returns:** `None` - 

### `add_static_lines` 

```python
def add_static_lines(count: int) -> None
```

**Returns:** `None` - 

## Functions

### `_load_project_cli_plugins` 

```python
def _load_project_cli_plugins(cli_app: typer.Typer) -> PluginManager | None
```

Dispatch ``register_cli`` for plugins listed in ``./docs.yaml``.

Typer finalizes the command table when this module is imported — before
any command (and its project-directory argument) is parsed — so project
plugins can only contribute CLI commands when the project config is
resolvable from the current working directory. Running ``folio`` from
outside the project still loads project plugins for build hooks; only
their extra CLI commands require running inside the project. Every
failure degrades to a warning: a broken plugin must never take down the
whole CLI.

**Returns:** [`PluginManager | None`](/docs/api-reference/folio_docs/plugin#pluginmanager) - 

### `_resolve_project_target` 

```python
def _resolve_project_target(directory: Path | None, project_dir: Path | None) -> Path
```

**Returns:** `Path` - 

### `_format_cli_path` 

```python
def _format_cli_path(target: Path) -> str
```

**Returns:** `str` - 

### `_command_target_suffix` 

```python
def _command_target_suffix(target: Path) -> str
```

**Returns:** `str` - 

### `_exit_if_feature_disabled` 

```python
def _exit_if_feature_disabled(feature: str) -> None
```

**Returns:** `None` - 

### `_detected_label_spacer` 

```python
def _detected_label_spacer(label: str, label_width: int) -> str
```

**Returns:** `str` - 

### `_detected_summary_body` 

```python
def _detected_summary_body(info: dict, target: Path, repo: str) -> Text
```

**Returns:** `Text` - 

### `_print_init_intro` 

```python
def _print_init_intro(info: dict, target: Path, repo: str, *, compact: bool = False, news_item: str | None = None) -> tuple[int, str]
```

**Returns:** `tuple[int, str]` - 

### `_init_intro_renderable` 

```python
def _init_intro_renderable(info: dict, target: Path, repo: str, *, news_item: str | None = None) -> Group
```

**Returns:** `Group` - 

### `_renderable_plain_lines` 

```python
def _renderable_plain_lines(renderable: object) -> list[str]
```

**Returns:** `list[str]` - 

### `_cursor_rows_below_news` 

```python
def _cursor_rows_below_news(renderable: object) -> int
```

**Returns:** `int` - 

### `_active_init_intro_ticker` 

```python
def _active_init_intro_ticker() -> _InitIntroTicker | None
```

**Returns:** `_InitIntroTicker | None` - 

### `_set_active_init_prompt_lines` 

```python
def _set_active_init_prompt_lines(count: int) -> None
```

**Returns:** `None` - 

### `_clear_active_init_prompt_lines` 

```python
def _clear_active_init_prompt_lines() -> None
```

**Returns:** `None` - 

### `_add_static_init_prompt_lines` 

```python
def _add_static_init_prompt_lines(count: int) -> None
```

**Returns:** `None` - 

### `_write_completed_line` 

```python
def _write_completed_line(choice_set: dict[str, object], value: str) -> None
```

**Returns:** `None` - 

### `_ask_init_choice` 

```python
def _ask_init_choice(title: str, options: tuple[tuple[str, str, str], ...], *, default: str, style: str) -> str
```

**Returns:** `str` - 

### `prompt_line` 

```python
def prompt_line(choice_set: dict[str, object]) -> str
```

**Returns:** `str` - 

### `completed_line` 

```python
def completed_line(choice_set: dict[str, object], value: str) -> str
```

**Returns:** `str` - 

### `_formatted_init_prompt_title` 

```python
def _formatted_init_prompt_title(title: str) -> str
```

**Returns:** `str` - 

### `menu_line` 

```python
def menu_line(choice: dict[str, str], index: int, selected_index: int) -> str
```

**Returns:** `str` - 

### `draw_menu` 

```python
def draw_menu(choice_set: dict[str, object], choices: list[dict[str, str]], selected_index: int, first_draw: bool) -> None
```

**Returns:** `None` - 

### `clear_menu` 

```python
def clear_menu(choices: list[dict[str, str]]) -> None
```

**Returns:** `None` - 

### `_init_can_use_arrow_select` 

```python
def _init_can_use_arrow_select() -> bool
```

**Returns:** `bool` - 

### `_init_readchar` 

```python
def _init_readchar()
```

### `_ask_init_arrow_choice` 

```python
def _ask_init_arrow_choice(title: str, options: tuple[tuple[str, str, str], ...], *, default: str, style: str) -> str | None
```

**Returns:** `str | None` - 

### `_print_init_ready` 

```python
def _print_init_ready(target: Path, created: list[str], *, compact: bool = False) -> None
```

**Returns:** `None` - 

### `_created_cli_path` 

```python
def _created_cli_path(target: Path, relative_path: str | Path) -> str
```

**Returns:** `str` - 

### `_dependency_name` 

```python
def _dependency_name(spec: str) -> str
```

**Returns:** `str` - 

### `_project_dependency_names` 

```python
def _project_dependency_names(pyproject_data: dict) -> set[str]
```

**Returns:** `set[str]` - 

### `_detect_framework` 

```python
def _detect_framework(pyproject_data: dict) -> str
```

**Returns:** `str` - 

### `_documentation_status` 

```python
def _documentation_status(target: Path) -> str
```

**Returns:** `str` - 

### `_detect_project` 

```python
def _detect_project(target: Path) -> dict
```

Detect project name, version, and Python source paths from pyproject.toml.

**Returns:** `dict` - 

### `_detect_git_remote` 

```python
def _detect_git_remote(target: Path) -> str
```

Try to detect the GitHub repo URL from git remote.

**Returns:** `str` - 

### `_yaml_scalar` 

```python
def _yaml_scalar(value: object) -> str
```

Render ``value`` as a quoted YAML scalar.

Detected project metadata (pyproject name/version, the git remote, source
paths) is repository content, so interpolating it raw would let a clone
close the quote and append top-level keys - ``plugins:`` among them - to
the config Folio then trusts. JSON string syntax is valid YAML
double-quoted style, so ``json.dumps`` is the escape we want.

**Returns:** `str` - 

### `_generate_docs_yaml` 

```python
def _generate_docs_yaml(info: dict) -> str
```

**Returns:** `str` - 

### `_version_callback` 

```python
def _version_callback(value: bool) -> None
```

**Returns:** `None` - 

### `main` 

```python
def main(version: bool = typer.Option(False, '--version', '-V', callback=_version_callback, is_eager=True, help='Show version')) -> None
```

**Returns:** `None` - 

### `init` 

```python
def init(directory: Path = typer.Argument(default=None, help='Project directory (defaults to cwd)'), yes: bool = typer.Option(False, '--yes', '-y', help='Skip prompts, use detected defaults')) -> None
```

Initialize a new Folio documentation project.

**Returns:** `None` - 

### `_serve_static_site` 

```python
def _serve_static_site(site_dir: Path, port: int = 8787, open_browser: bool = False, kill_existing: bool = False) -> None
```

Start a local HTTP server for a built static site.

**Returns:** `None` - 

### `_serve_and_open` 

```python
def _serve_and_open(site_dir: Path, port: int = 8787) -> None
```

Start a local HTTP server for the built site and open it in the browser.

**Returns:** `None` - 

### `_read_output_dir_best_effort` 

```python
def _read_output_dir_best_effort(config_path: Path, target: Path) -> Path
```

**Returns:** `Path` - 

### `_resolve_version_output_dir` 

```python
def _resolve_version_output_dir(output_base: Path, version_path: object) -> Path
```

**Returns:** `Path` - 

### `_write_default_version_redirect` 

```python
def _write_default_version_redirect(output_base: Path, version_path: str) -> None
```

Write a static root redirect to the default docs version.

**Returns:** `None` - 

### `_sync_version_matrix` 

```python
def _sync_version_matrix(config_path: Path, versions: list[dict], synced_config: dict | None = None) -> None
```

Inject current version/plugin config into a checked-out historical ref.

**Returns:** `None` - 

### `_version_sync_config` 

```python
def _version_sync_config(config_path: Path, pm: object) -> dict
```

**Returns:** `dict` - 

### `_stable_hash` 

```python
def _stable_hash(value: object) -> str
```

**Returns:** `str` - 

### `_resolve_git_commit` 

```python
def _resolve_git_commit(project_dir: Path, ref: str) -> str
```

**Returns:** `str` - 

### `_version_build_manifest` 

```python
def _version_build_manifest(*, version: dict, commit: str, versions: list[dict], synced_config: dict) -> dict
```

**Returns:** `dict` - 

### `_read_version_build_manifest` 

```python
def _read_version_build_manifest(output_path: Path) -> dict | None
```

**Returns:** `dict | None` - 

### `_version_output_has_content` 

```python
def _version_output_has_content(output_path: Path) -> bool
```

**Returns:** `bool` - 

### `_version_build_manifest_matches` 

```python
def _version_build_manifest_matches(output_path: Path, expected: dict) -> bool
```

**Returns:** `bool` - 

### `_write_version_build_manifest` 

```python
def _write_version_build_manifest(output_path: Path, manifest: dict) -> None
```

**Returns:** `None` - 

### `_remove_version_worktree` 

```python
def _remove_version_worktree(project_dir: Path, worktree_dir: Path) -> None
```

Remove a generated version worktree and prune stale Git metadata.

**Returns:** `None` - 

### `_build_configured_versions` 

```python
def _build_configured_versions(*, project_dir: Path, verbose: bool, config: str, clean: bool) -> None
```

Build docs for every version configured in docs.yaml.

**Returns:** `None` - 

### `build` 

```python
def build(directory: Path = typer.Argument(default=None, help='Project directory (defaults to cwd)'), project_dir: Path = typer.Option(default=None, help='Compatibility option for scripts that prefer named arguments'), verbose: bool = typer.Option(False, '--verbose', '-v', help='Show detailed output'), config: str = typer.Option('docs.yaml', '--config', '-c', help='Config file path'), clean: bool = typer.Option(False, '--clean', help='Force full rebuild (clear cache)'), open_browser: bool = typer.Option(False, '--open', '-o', help='Starts a static preview in the browser and blocks until interrupted')) -> None
```

**Returns:** `None` - 

### `build_versions` 

```python
def build_versions(directory: Path = typer.Argument(default=None, help='Project directory (defaults to cwd)'), project_dir: Path = typer.Option(default=None, help='Compatibility option for scripts that prefer named arguments'), verbose: bool = typer.Option(False, '--verbose', '-v', help='Show detailed output'), config: str = typer.Option('docs.yaml', '--config', '-c', help='Config file path'), clean: bool = typer.Option(False, '--clean', help='Force full rebuild (clear cache)')) -> None
```

Build docs for all configured versions.

**Returns:** `None` - 

### `serve` 

```python
def serve(directory: Path = typer.Argument(default=None, help='Project directory (defaults to cwd)'), project_dir: Path = typer.Option(default=None, help='Compatibility option for scripts that prefer named arguments'), verbose: bool = typer.Option(False, '--verbose', '-v', help='Show detailed output'), config: str = typer.Option('docs.yaml', '--config', '-c', help='Config file path'), port: int = typer.Option(4321, '--port', '-p', help='Dev server port'), open_browser: bool = typer.Option(False, '--open', '-o', help='Open browser automatically'), clean: bool = typer.Option(False, '--clean', help='Force full rebuild (clear cache)'), versions: bool = typer.Option(False, '--versions', help='Build and serve every configured version as a static preview', hidden=True), kill_existing: bool = typer.Option(False, '--kill-existing', help='Stop an existing process on the selected port before serving')) -> None
```

**Returns:** `None` - 

### `coverage` 

```python
def coverage(directory: Path = typer.Argument(default=None, help='Project directory (defaults to cwd)'), project_dir: Path = typer.Option(default=None, help='Compatibility option for scripts that prefer named arguments'), config: str = typer.Option('docs.yaml', '--config', '-c', help='Config file path'), verbose: bool = typer.Option(False, '--verbose', '-v', help='List each undocumented symbol'), min_coverage: float = typer.Option(0, '--min', help='Minimum coverage percentage (exit 1 if below)')) -> None
```

Analyze documentation coverage of Python source files.

**Returns:** `None` - 

### `clean` 

```python
def clean(directory: Path = typer.Argument(default=None, help='Project directory (defaults to cwd)'), project_dir: Path = typer.Option(default=None, help='Compatibility option for scripts that prefer named arguments')) -> None
```

**Returns:** `None` -
