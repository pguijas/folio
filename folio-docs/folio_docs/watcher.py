from __future__ import annotations

from dataclasses import dataclass
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from rich.markup import escape
from watchfiles import Change, watch

from folio_docs.parser.python_parser import (
    _is_python_excluded as _matches_python_exclude,
    _is_python_import_root,
)

if TYPE_CHECKING:
    from rich.console import Console

    from folio_docs.config import Config
    from folio_docs.docs.site_builder import SiteBuilder
    from folio_docs.ir import ModuleIR


def _preview_examples_dir(project_dir: Path) -> Path:
    return project_dir / "docs" / "examples"


def _watch_dirs_with_preview_examples(
    watch_dirs: list[Path],
    project_dir: Path,
) -> list[Path]:
    examples_dir = _preview_examples_dir(project_dir)
    if not examples_dir.is_dir():
        return watch_dirs

    resolved_watch_dirs = {path.resolve() for path in watch_dirs if path.exists()}
    if examples_dir.resolve() in resolved_watch_dirs:
        return watch_dirs

    return [*watch_dirs, examples_dir]


def _plugin_watch_dirs(plugin_manager, resolved: Config) -> list[Path]:
    """Directories plugins asked the watcher to care about (existing only)."""
    if plugin_manager is None:
        return []
    dirs: list[Path] = []
    for result in plugin_manager.call_isolated(
        "watch_paths", policy="warn_skip", config=resolved
    ):
        for entry in result or []:
            path = Path(entry)
            if path.is_dir():
                dirs.append(path)
    return dirs


def _dispatch_plugin_change(
    plugin_manager,
    plugin_dirs: list[Path],
    builder,
    resolved: Config,
    change: Change,
    path: Path,
) -> bool:
    """Offer a change under a plugin-watched directory to the plugins.

    The handler, not the watcher, knows what the files mean — a board
    directory holds .md cards and a .yaml column set, and future plugins
    hold whatever they hold. Returns True when some plugin handled it."""
    if plugin_manager is None or not _is_under(path, plugin_dirs):
        return False
    results = plugin_manager.call_isolated(
        "on_watched_change",
        policy="warn_skip",
        builder=builder,
        config=resolved,
        path=str(path),
        change=change.name,
    )
    return any(bool(result) for result in results)


def _is_under(path: Path, dirs: list[Path]) -> bool:
    for d in dirs:
        try:
            path.relative_to(d)
            return True
        except ValueError:
            continue
    return False


def _module_name_from_path(path: Path, src_dir: Path) -> str:
    rel = path.relative_to(src_dir)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")
    if _is_python_import_root(src_dir):
        return ".".join(parts)
    return f"{src_dir.name}.{'.'.join(parts)}" if parts else src_dir.name


def _route_from_doc_path(path: Path, doc_dir: Path) -> str:
    rel = path.relative_to(doc_dir)
    parts = list(rel.parts)
    parts[-1] = parts[-1].removesuffix(".md")
    return "/".join(parts)


def _parse_python_modules(resolved: Config):
    from folio_docs.sources import parse_python_sources

    return parse_python_sources(resolved).modules


@dataclass
class _PythonModuleCache:
    modules: list[ModuleIR]

    @classmethod
    def from_config(cls, resolved: Config) -> _PythonModuleCache:
        return cls(_parse_python_modules(resolved))

    def all_modules(self) -> list[ModuleIR]:
        return list(self.modules)

    def contains(self, source_file: Path) -> bool:
        source_key = source_file.resolve()
        return any(
            Path(module.source_file).resolve() == source_key for module in self.modules
        )

    def upsert(self, module: ModuleIR) -> None:
        source_key = Path(module.source_file).resolve()
        for index, existing in enumerate(self.modules):
            if Path(existing.source_file).resolve() == source_key:
                self.modules[index] = module
                return
        self.modules.append(module)

    def remove(self, source_file: Path) -> None:
        source_key = source_file.resolve()
        self.modules = [
            module
            for module in self.modules
            if Path(module.source_file).resolve() != source_key
        ]


def _parse_python_module(path: Path, module_name: str, resolved: Config) -> ModuleIR:
    from folio_docs.parser.python_parser import _resolve_style, parse_python_file

    return parse_python_file(
        path,
        module_name,
        style=_resolve_style(resolved.docstring_style),
    )


def _disabled_api_feature_for_module(module_name: str) -> str | None:
    from folio_docs.features import disabled_api_feature_for_module

    return disabled_api_feature_for_module(module_name)


def _published_modules(modules: list[ModuleIR]) -> list[ModuleIR]:
    return [
        module
        for module in modules
        if not _disabled_api_feature_for_module(module.name)
    ]


def _is_python_excluded(path: Path, resolved: Config) -> bool:
    return _matches_python_exclude(path, resolved.python_excludes)


def _write_api_reference_index(
    modules: list[ModuleIR],
    builder: SiteBuilder,
) -> None:
    from folio_docs.docs.mdx_writer import api_reference_index_to_mdx

    if modules:
        builder.write_page("api-reference/index", api_reference_index_to_mdx(modules))
    else:
        builder.remove_page("api-reference/index")


def _write_meta_for_modules(
    all_modules: list[ModuleIR],
    resolved: Config,
    config: Config,
    builder: SiteBuilder,
) -> None:
    from folio_docs.docs.sidebar import generate_meta_files
    from folio_docs.sources import parse_doc_sources

    all_docs = parse_doc_sources(resolved).docs
    published_modules = _published_modules(all_modules)

    meta_files = generate_meta_files(
        config.nav,
        published_modules,
        all_docs,
        default_collapsed=config.sidebar_default_collapsed,
    )
    for path_str, content in meta_files.items():
        directory = str(Path(path_str).parent) if "/" in path_str else ""
        builder.write_meta(directory, content)
    _write_api_reference_index(published_modules, builder)
    builder.write_search_index()


def _regenerate_meta(
    python_source_dirs: list[Path],
    resolved: Config,
    config: Config,
    builder: SiteBuilder,
) -> None:
    all_modules = _parse_python_modules(resolved)
    _write_meta_for_modules(all_modules, resolved, config, builder)


def _handle_python_change_incremental(
    change: Change,
    path: Path,
    module_name: str,
    route: str,
    module_cache: _PythonModuleCache,
    config: Config,
    resolved: Config,
    builder: SiteBuilder,
    project_dir: Path,
    console: Console,
    verbose: bool,
) -> bool:
    if _is_python_excluded(path, resolved):
        return False

    from folio_docs.docs.mdx_writer import module_to_mdx
    from folio_docs.docs.xref import build_symbol_index

    if change == Change.deleted:
        module_cache.remove(path)
        builder.remove_page(route)
        if verbose:
            console.print(f"  [red]Removed: {route}[/red]")
        _write_meta_for_modules(module_cache.all_modules(), resolved, config, builder)
        return True

    was_known = module_cache.contains(path)
    try:
        mod = _parse_python_module(path, module_name, resolved)
    except Exception:
        return False

    module_cache.upsert(mod)
    all_modules = module_cache.all_modules()
    if _disabled_api_feature_for_module(mod.name):
        builder.remove_page(route)
        _write_meta_for_modules(all_modules, resolved, config, builder)
        if verbose:
            console.print(f"  [yellow]Skipped disabled API module: {mod.name}[/yellow]")
        return True

    published_modules = _published_modules(all_modules)
    symbol_index = build_symbol_index(published_modules)
    mdx = module_to_mdx(
        mod,
        repo_url=config.project_repo,
        source_root=str(project_dir) + "/",
        source_ref=config.project_repo_ref,
        symbol_index=symbol_index,
    )
    builder.write_page(route, mdx)
    _write_api_reference_index(published_modules, builder)
    builder.write_search_index()
    if verbose:
        console.print(f"  [green]Updated: {route}[/green]")

    if change == Change.added or not was_known:
        _write_meta_for_modules(all_modules, resolved, config, builder)
    return True


def _handle_python_change(
    change: Change,
    path: Path,
    python_source_dirs: list[Path],
    config: Config,
    resolved: Config,
    builder: SiteBuilder,
    project_dir: Path,
    console: Console,
    verbose: bool,
    module_cache: _PythonModuleCache | None = None,
) -> None:
    from folio_docs.docs.mdx_writer import module_to_mdx
    from folio_docs.docs.xref import build_symbol_index

    for src_dir in python_source_dirs:
        try:
            path.relative_to(src_dir)
        except ValueError:
            continue

        module_name = _module_name_from_path(path, src_dir)
        route = f"api-reference/{module_name.replace('.', '/')}"

        if module_cache is not None and _handle_python_change_incremental(
            change,
            path,
            module_name,
            route,
            module_cache,
            config,
            resolved,
            builder,
            project_dir,
            console,
            verbose,
        ):
            return

        if change == Change.deleted:
            builder.remove_page(route)
            if verbose:
                console.print(f"  [red]Removed: {route}[/red]")
            _regenerate_meta(python_source_dirs, resolved, config, builder)
            return

        all_modules = _parse_python_modules(resolved)
        changed_source = path.resolve()
        mod = next(
            (
                module
                for module in all_modules
                if Path(module.source_file).resolve() == changed_source
            ),
            None,
        )
        if mod is None:
            builder.remove_page(route)
            _regenerate_meta(python_source_dirs, resolved, config, builder)
            return

        if _disabled_api_feature_for_module(mod.name):
            builder.remove_page(route)
            _write_meta_for_modules(all_modules, resolved, config, builder)
            if verbose:
                console.print(
                    f"  [yellow]Skipped disabled API module: {mod.name}[/yellow]"
                )
            return

        published_modules = _published_modules(all_modules)
        symbol_index = build_symbol_index(published_modules)
        mdx = module_to_mdx(
            mod,
            repo_url=config.project_repo,
            source_root=str(project_dir) + "/",
            source_ref=config.project_repo_ref,
            symbol_index=symbol_index,
        )
        builder.write_page(route, mdx)
        _write_api_reference_index(published_modules, builder)
        builder.write_search_index()
        if verbose:
            console.print(f"  [green]Updated: {route}[/green]")

        if change == Change.added:
            _regenerate_meta(python_source_dirs, resolved, config, builder)
        return


def _handle_doc_change(
    change: Change,
    path: Path,
    doc_source_dirs: list[Path],
    config: Config,
    resolved: Config,
    builder: SiteBuilder,
    python_source_dirs: list[Path],
    console: Console,
    verbose: bool,
) -> None:
    from folio_docs.features import disabled_doc_feature_for_route
    from folio_docs.docs.mdx_writer import markdown_to_mdx
    from folio_docs.parser.markdown_parser import parse_markdown_file

    for doc_dir in doc_source_dirs:
        try:
            path.relative_to(doc_dir)
        except ValueError:
            continue

        route = _route_from_doc_path(path, doc_dir)

        if change == Change.deleted:
            builder.remove_page(route)
            if verbose:
                console.print(f"  [red]Removed: {route}[/red]")
            _regenerate_meta(python_source_dirs, resolved, config, builder)
            return

        result = parse_markdown_file(path)
        result.route = route
        if disabled_doc_feature_for_route(result.route):
            builder.remove_page(route)
            builder.write_search_index()
            if verbose:
                console.print(f"  [yellow]Skipped disabled doc: {route}[/yellow]")
            if change == Change.added:
                _regenerate_meta(python_source_dirs, resolved, config, builder)
            return

        mdx = markdown_to_mdx(result)
        builder.write_page(route, mdx)
        builder.write_search_index()
        if verbose:
            console.print(f"  [green]Updated: {route}[/green]")

        if change == Change.added:
            _regenerate_meta(python_source_dirs, resolved, config, builder)
        return


def _handle_preview_example_change(
    _change: Change,
    path: Path,
    examples_dir: Path,
    builder: SiteBuilder,
    console: Console,
    verbose: bool,
) -> None:
    builder.write_preview_examples(examples_dir)
    if verbose:
        rel_path = path.relative_to(examples_dir.parent)
        console.print(f"  [green]Updated preview examples: {rel_path}[/green]")


def _watcher_loop(
    stop_event: threading.Event,
    watch_dirs: list[Path],
    python_source_dirs: list[Path],
    doc_source_dirs: list[Path],
    preview_examples_dir: Path,
    config: Config,
    resolved: Config,
    builder: SiteBuilder,
    project_dir: Path,
    console: Console,
    verbose: bool,
    plugin_manager=None,
    plugin_watch_dirs: list[Path] | None = None,
) -> None:
    plugin_watch_dirs = plugin_watch_dirs or []
    try:
        module_cache = (
            _PythonModuleCache.from_config(resolved) if python_source_dirs else None
        )
    except Exception as e:
        module_cache = None
        if verbose:
            console.print(
                f"  [yellow]Watcher incremental cache disabled: {escape(str(e))}[/yellow]",
            )

    for changes in watch(
        *watch_dirs,
        stop_event=stop_event,
        watch_filter=lambda _, p: (
            p.endswith(".py")
            or p.endswith(".md")
            or _is_under(Path(p), [preview_examples_dir])
            or _is_under(Path(p), plugin_watch_dirs)
        ),
    ):
        for change_type, path_str in changes:
            path = Path(path_str)
            try:
                if _dispatch_plugin_change(
                    plugin_manager,
                    plugin_watch_dirs,
                    builder,
                    resolved,
                    change_type,
                    path,
                ):
                    if verbose:
                        console.print(f"  [green]Plugin refresh: {path.name}[/green]")
                elif _is_under(path, [preview_examples_dir]):
                    _handle_preview_example_change(
                        change_type,
                        path,
                        preview_examples_dir,
                        builder,
                        console,
                        verbose,
                    )
                elif path.suffix == ".py" and _is_under(path, python_source_dirs):
                    _handle_python_change(
                        change_type,
                        path,
                        python_source_dirs,
                        config,
                        resolved,
                        builder,
                        project_dir,
                        console,
                        verbose,
                        module_cache,
                    )
                elif path.suffix == ".md" and _is_under(path, doc_source_dirs):
                    _handle_doc_change(
                        change_type,
                        path,
                        doc_source_dirs,
                        config,
                        resolved,
                        builder,
                        python_source_dirs,
                        console,
                        verbose,
                    )
            except Exception as e:
                console.print(f"  [red]Watcher error: {escape(str(e))}[/red]")


def start_watcher(
    watch_dirs: list[Path],
    config: Config,
    resolved: Config,
    builder: SiteBuilder,
    project_dir: Path,
    console: Console,
    verbose: bool = False,
    plugin_manager=None,
) -> threading.Event:
    """Start file watcher in a daemon thread. Returns stop event."""
    stop_event = threading.Event()

    watch_dirs = _watch_dirs_with_preview_examples(watch_dirs, project_dir)
    python_source_dirs = [Path(s) for s in resolved.python_sources if Path(s).exists()]
    doc_source_dirs = [Path(s) for s in resolved.doc_sources if Path(s).exists()]
    preview_examples_dir = _preview_examples_dir(project_dir)
    plugin_watch_dirs = _plugin_watch_dirs(plugin_manager, resolved)
    already_watched = {path.resolve() for path in watch_dirs}
    watch_dirs = watch_dirs + [
        path for path in plugin_watch_dirs if path.resolve() not in already_watched
    ]

    thread = threading.Thread(
        target=_watcher_loop,
        args=(
            stop_event,
            watch_dirs,
            python_source_dirs,
            doc_source_dirs,
            preview_examples_dir,
            config,
            resolved,
            builder,
            project_dir,
            console,
            verbose,
            plugin_manager,
            plugin_watch_dirs,
        ),
        daemon=True,
        name="folio-watcher",
    )
    thread.start()
    return stop_event
