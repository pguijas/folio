from __future__ import annotations

import hashlib
import io
import time
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.text import Text

from folio import __version__
from folio.branding import folio_banner
from folio.config import Config, load_config_with_plugins
from folio.extensions import (
    ExtensionRegistry,
    register_builtin_extensions,
    register_config_components,
)
from folio.features import (
    disabled_api_feature_for_module,
    disabled_doc_feature_for_route,
    experimental_feature_state,
)
from folio.generator.llm_output import generate_llms_full_txt, generate_llms_txt
from folio.generator.mdx_writer import (
    api_reference_index_to_mdx,
    markdown_to_mdx,
    module_to_mdx,
)
from folio.generator.sidebar import generate_meta_files
from folio.generator.site_builder import SiteBuilder
from folio.generator.xref import build_symbol_index
from folio.ir import ModuleIR
from folio.link_checker import check_links
from folio.parser.markdown_parser import MarkdownResult
from folio.sources import parse_doc_sources, parse_python_sources

console = Console()


@dataclass
class BuildSources:
    modules: list[ModuleIR]
    docs: list[MarkdownResult]
    warnings: list[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    build_context: dict[str, str]
    sources: dict[str, dict]
    skipped: int
    total_pages: int


@dataclass
class ExportResult:
    llm_files: int
    output_lines: list[str]


def _find_template_dir() -> Path:
    # Installed wheels bundle the template inside the package (folio/template);
    # git checkouts keep it at the repository root.
    packaged = Path(__file__).parent / "template"
    if packaged.is_dir():
        return packaged
    return Path(__file__).parent.parent / "template"


def _hash_file(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    ignored_dirs = {"node_modules", ".next", "out", "__pycache__", ".git"}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in ignored_dirs for part in rel.parts):
            continue
        if path.is_file():
            digest.update(rel.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _build_manifest_context(
    config_path: Path,
    template_dir: Path,
    source_ref: str,
) -> dict[str, str]:
    folio_dir = Path(__file__).parent
    generator_inputs = [
        Path(__file__),
        folio_dir / "config.py",
        folio_dir / "generator" / "site_builder.py",
        folio_dir / "generator" / "mdx_writer.py",
        folio_dir / "generator" / "sidebar.py",
        folio_dir / "generator" / "xref.py",
        folio_dir / "parser" / "markdown_parser.py",
        folio_dir / "parser" / "python_parser.py",
        folio_dir / "sources.py",
    ]
    generator_digest = hashlib.sha256()
    for path in generator_inputs:
        generator_digest.update(str(path.relative_to(folio_dir.parent)).encode("utf-8"))
        generator_digest.update(b"\0")
        generator_digest.update(_hash_file(path).encode("utf-8"))
        generator_digest.update(b"\0")
    return {
        "config": _hash_file(config_path),
        "template": _hash_tree(template_dir),
        "generator": generator_digest.hexdigest(),
        "source_ref": source_ref,
        "experimental_features": experimental_feature_state(),
    }


def _print_banner(config: Config, *, include_news: bool = True) -> None:
    v = f"v{__version__}"
    console.print(
        f"\n{folio_banner(v, width=console.width, include_news=include_news)}",
        highlight=False,
    )
    console.print()
    console.file.flush()


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    word = singular if count == 1 else plural or f"{singular}s"
    return f"{count} {word}"


def _step_description(label: str, detail: str) -> str:
    return f"[bold cyan]{label:<12}[/] [dim]›[/] {detail}"


def _print_step(
    label: str,
    detail: str,
    *,
    marker: str = "✓",
    marker_style: str = "green",
    label_style: str = "bold",
) -> None:
    console.print(
        f"[{marker_style}]{marker}[/] [{label_style}]{label:<12}[/] [dim]›[/] {detail}"
    )


def _print_step_detail(detail: str, *, style: str = "dim") -> None:
    console.print(f"  [{style}]{detail}[/]")


def _export_step_detail() -> str:
    return "building static site"


def _build_output_panel(lines: list[str]) -> Panel:
    output = "".join(lines).rstrip() or "Waiting for build output..."
    return Panel(
        Text.from_ansi(output),
        title="Build output",
        border_style="dim",
        padding=(0, 1),
    )


def _print_build_output(lines: list[str]) -> None:
    if not lines:
        return

    console.print()
    console.print(_build_output_panel(lines))


class _BuildOutputStream:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __enter__(self) -> "_BuildOutputStream":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def record(self, line: str) -> None:
        self.lines.append(line)


def _parse_project_sources(resolved: Config, verbose: bool) -> BuildSources:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Sources", "scanning Python and docs"), total=None
        )
        parsed_python = parse_python_sources(resolved)
        for src_path in parsed_python.scanned_paths:
            if verbose:
                console.print(f"  Scanning {src_path}")

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            parsed_docs = parse_doc_sources(resolved)

    for doc_path in parsed_docs.scanned_paths:
        if verbose:
            console.print(f"  Scanning {doc_path}")

    if not parsed_python.modules and not parsed_docs.docs:
        console.print(
            "[red]Error: No Python modules or documentation found. Check source paths in docs.yaml.[/red]"
        )
        raise RuntimeError(
            "No Python modules or documentation found. Check source paths in docs.yaml."
        )

    source_warnings = [
        f"Python source path not found: {src}" for src in parsed_python.missing_paths
    ]
    source_warnings.extend(
        f"Documentation source path not found: {doc_dir}"
        for doc_dir in parsed_docs.missing_paths
    )
    source_warnings.extend(str(warning.message) for warning in caught_warnings)

    return BuildSources(
        modules=parsed_python.modules,
        docs=parsed_docs.docs,
        warnings=source_warnings,
    )


def _prepare_builder(
    resolved: Config,
    template_dir: Path,
    build_dir: Path,
    *,
    clean: bool,
    verbose: bool,
) -> SiteBuilder:
    builder = SiteBuilder(resolved, str(template_dir), str(build_dir), verbose=verbose)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Template", "preparing workspace"), total=None
        )
        builder.prepare(clean=clean)
    return builder


def _write_meta_pages(
    builder: SiteBuilder,
    config: Config,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
) -> None:
    builder.remove_meta_tree("api-reference")
    meta_files = generate_meta_files(config.nav, modules, docs)
    for path, content in meta_files.items():
        directory = str(Path(path).parent) if "/" in path else ""
        builder.write_meta(directory, content)
    if modules:
        builder.write_page("api-reference/index", api_reference_index_to_mdx(modules))
    else:
        builder.remove_page("api-reference/index")


def _published_modules(modules: list[ModuleIR]) -> list[ModuleIR]:
    return [
        module for module in modules if not disabled_api_feature_for_module(module.name)
    ]


def _published_docs(docs: list[MarkdownResult]) -> list[MarkdownResult]:
    return [doc for doc in docs if not disabled_doc_feature_for_route(doc.route)]


def _generate_content_pages(
    *,
    builder: SiteBuilder,
    config: Config,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
    project_dir: Path,
    config_path: Path,
    template_dir: Path,
    clean: bool,
    verbose: bool,
) -> GenerationResult:
    new_sources: dict[str, dict] = {}
    skipped = 0
    published_modules = _published_modules(modules)
    published_docs = _published_docs(docs)
    total_candidates = len(docs) + len(modules)
    total_pages = len(published_docs) + len(published_modules)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=20),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            _step_description("Pages", "generating content"),
            total=total_candidates,
        )
        symbol_index = build_symbol_index(published_modules)
        _write_meta_pages(builder, config, published_modules, docs)

        build_context = _build_manifest_context(
            config_path,
            template_dir,
            config.project_repo_ref,
        )
        prev_manifest = (
            builder.load_manifest() if not clean else {"sources": {}, "build": {}}
        )
        prev_sources = prev_manifest.get("sources", {})
        context_changed = prev_manifest.get("build") != build_context

        for doc in docs:
            src_key = doc.source_file
            src_path = Path(src_key)
            file_hash = (
                hashlib.sha256(src_path.read_bytes()).hexdigest()
                if src_path.exists()
                else ""
            )
            new_sources[src_key] = {"hash": file_hash, "route": doc.route}

            if (
                prev_sources.get(src_key, {}).get("hash") == file_hash
                and file_hash
                and not context_changed
                and builder.page_exists(doc.route)
                and builder.page_markdown_exists(doc.route)
            ):
                skipped += 1
                progress.advance(task)
                continue

            if disabled_doc_feature_for_route(doc.route):
                if verbose:
                    console.print(f"  Skipping disabled doc: {doc.route}")
                builder.remove_page(doc.route)
                progress.advance(task)
                continue

            mdx = markdown_to_mdx(doc)
            if verbose:
                console.print(f"  Writing page: {doc.route}")
            builder.write_page(doc.route, mdx)
            progress.advance(task)

        for mod in modules:
            src_key = mod.source_file
            src_path = Path(src_key)
            file_hash = (
                hashlib.sha256(src_path.read_bytes()).hexdigest()
                if src_path.exists()
                else ""
            )
            route = f"api-reference/{mod.name.replace('.', '/')}"
            new_sources[src_key] = {"hash": file_hash, "route": route}

            if disabled_api_feature_for_module(mod.name):
                if verbose:
                    console.print(f"  Skipping disabled API module: {mod.name}")
                builder.remove_page(route)
                progress.advance(task)
                continue

            if (
                prev_sources.get(src_key, {}).get("hash") == file_hash
                and file_hash
                and not context_changed
                and builder.page_exists(route)
                and builder.page_markdown_exists(route)
            ):
                skipped += 1
                progress.advance(task)
                continue

            mdx = module_to_mdx(
                mod,
                repo_url=config.project_repo,
                source_root=str(project_dir) + "/",
                source_ref=config.project_repo_ref,
                symbol_index=symbol_index,
            )
            if verbose:
                console.print(f"  Writing page: {route}")
            builder.write_page(route, mdx)
            progress.advance(task)

    for old_key, old_info in prev_sources.items():
        if old_key not in new_sources:
            builder.remove_page(old_info["route"])
            if verbose:
                console.print(f"  Removed page: {old_info['route']}")

    return GenerationResult(
        build_context=build_context,
        sources=new_sources,
        skipped=skipped,
        total_pages=total_pages,
    )


def _apply_extensions(builder: SiteBuilder, pm: object, resolved: Config) -> None:
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    register_config_components(registry, resolved)
    pm.pm.hook.register_components(registry=registry)
    pm.pm.hook.register_extensions(registry=registry, config=resolved)
    builder.apply_extensions(registry)
    pm.pm.hook.emit_assets(builder=builder, config=resolved)


def _check_generated_links(
    builder: SiteBuilder,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
) -> list:
    published_modules = _published_modules(modules)
    all_routes = [doc.route for doc in _published_docs(docs)]
    if published_modules:
        all_routes.append("api-reference/index")
    for mod in published_modules:
        all_routes.append(f"api-reference/{mod.name.replace('.', '/')}")
    return check_links(builder.content_dir, all_routes)


def _finalize_generated_files(
    *,
    builder: SiteBuilder,
    pm: object,
    resolved: Config,
    generation: GenerationResult,
    project_dir: Path,
    serve: bool,
) -> bool:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Finalize", "preparing generated files"), total=None
        )
        _apply_extensions(builder, pm, resolved)
        builder.save_manifest(
            {"build": generation.build_context, "sources": generation.sources}
        )
        builder.write_search_index()

    preview_examples_dir = project_dir / "docs" / "examples"
    if not preview_examples_dir.exists():
        builder.write_preview_examples(preview_examples_dir)
        return False

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Previews", "building preview examples"), total=None
        )
        builder.write_preview_examples(preview_examples_dir)
    return True


def _check_generated_links_with_progress(
    builder: SiteBuilder,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
) -> list:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Links", "checking internal links"), total=None
        )
        return _check_generated_links(builder, modules, docs)


def _install_dependencies(builder: SiteBuilder) -> bool:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Dependencies", "checking pnpm"), total=None
        )
        did_install = builder.install_deps()
    return did_install


def _export_static_site(
    *,
    builder: SiteBuilder,
    config: Config,
    resolved: Config,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
    pm: object,
) -> ExportResult:
    output_stream = _BuildOutputStream()
    try:
        with output_stream:
            builder.build(
                log_path=builder.build_dir / ".folio-build.log",
                output_callback=output_stream.record,
            )
    except Exception:
        _print_build_output(output_stream.lines)
        raise

    llm_files = 0
    if resolved.generate_llms_txt or resolved.generate_llms_full_txt:
        published_modules = _published_modules(modules)
        llms_txt = (
            generate_llms_txt(config, published_modules, docs)
            if resolved.generate_llms_txt
            else None
        )
        llms_full = (
            generate_llms_full_txt(published_modules, docs)
            if resolved.generate_llms_full_txt
            else None
        )
        builder.write_llm_files(llms_txt, llms_full)
        llm_files = int(llms_txt is not None) + int(llms_full is not None)

    pm.pm.hook.post_build(site_dir=resolved.output_dir)
    return ExportResult(llm_files=llm_files, output_lines=output_stream.lines)


def _start_dev_server(
    *,
    builder: SiteBuilder,
    config: Config,
    resolved: Config,
    project_dir: Path,
    port: int,
    open_browser: bool,
    verbose: bool,
    kill_existing: bool,
) -> None:
    console.print()
    console.print("  [bold]Starting dev server...[/bold]\n")
    proc = builder.serve(port=port, kill_existing=kill_existing)

    if open_browser:
        import threading
        import webbrowser

        def _open() -> None:
            import time as _time

            _time.sleep(2)
            webbrowser.open(f"http://localhost:{port}")

        threading.Thread(target=_open, daemon=True).start()

    from folio.watcher import start_watcher

    watch_dirs = [
        Path(s)
        for s in resolved.python_sources + resolved.doc_sources
        if Path(s).exists()
    ]
    watcher_stop = start_watcher(
        watch_dirs=watch_dirs,
        config=config,
        resolved=resolved,
        builder=builder,
        project_dir=project_dir,
        console=console,
        verbose=verbose,
    )

    console.print("  [dim]Watching for file changes...[/dim]\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        watcher_stop.set()
        proc.terminate()


def run_build(
    project_dir: Path,
    serve: bool = False,
    verbose: bool = False,
    config_file: str = "docs.yaml",
    port: int = 4321,
    open_browser: bool = False,
    clean: bool = False,
    output_override: str = "",
    current_version_path: str = "",
    include_versions: bool = False,
    build_dir_override: str | Path = "",
    source_ref_override: str = "",
    quiet: bool = False,
    kill_existing: bool = False,
) -> None:
    global console

    if quiet:
        original_console = console
        console = Console(
            file=io.StringIO(),
            width=original_console.width,
            color_system=None,
            force_terminal=False,
        )
        try:
            run_build(
                project_dir,
                serve=serve,
                verbose=verbose,
                config_file=config_file,
                port=port,
                open_browser=open_browser,
                clean=clean,
                output_override=output_override,
                current_version_path=current_version_path,
                include_versions=include_versions,
                build_dir_override=build_dir_override,
                source_ref_override=source_ref_override,
                quiet=False,
                kill_existing=kill_existing,
            )
        finally:
            console = original_console
        return

    config_path = project_dir / config_file
    if not config_path.exists():
        raise FileNotFoundError(f"No {config_file} found in {project_dir}")

    config, pm = load_config_with_plugins(config_path, plugin_base_dir=project_dir)
    if source_ref_override.strip():
        config.project_repo_ref = source_ref_override.strip()
    version_note = ""
    if include_versions:
        config.current_version_path = current_version_path
    else:
        if config.versions and not serve:
            version_note = (
                "Current version only; use 'folio build-versions' for all versions."
            )
        config.versions = []
        config.current_version_path = ""
    resolved = config.resolve_paths(project_dir)
    if output_override:
        override_path = Path(output_override)
        if not override_path.is_absolute():
            override_path = project_dir / override_path
        resolved.output_dir = str(override_path.resolve())
        config.output_dir = output_override
    t0 = time.monotonic()

    _print_banner(config, include_news=False)
    sources = _parse_project_sources(resolved, verbose)
    _print_step(
        "Sources",
        ", ".join(
            [
                _count_phrase(len(sources.modules), "module"),
                _count_phrase(len(sources.docs), "doc page"),
            ]
        ),
    )
    for source_warning in sources.warnings:
        _print_step_detail(source_warning, style="yellow")
    if version_note:
        _print_step_detail(version_note)

    template_dir = _find_template_dir()
    build_dir = (
        Path(build_dir_override) if build_dir_override else project_dir / ".build"
    )
    builder = _prepare_builder(
        resolved,
        template_dir,
        build_dir,
        clean=clean,
        verbose=verbose,
    )
    _print_step("Template", ".build/ workspace ready")
    generation = _generate_content_pages(
        builder=builder,
        config=config,
        modules=sources.modules,
        docs=sources.docs,
        project_dir=project_dir,
        config_path=config_path,
        template_dir=template_dir,
        clean=clean,
        verbose=verbose,
    )
    page_detail = _count_phrase(generation.total_pages, "page")
    if generation.skipped:
        page_detail = (
            f"{page_detail}, {_count_phrase(generation.skipped, 'skipped page')}"
        )
    _print_step("Pages", page_detail)
    built_previews = _finalize_generated_files(
        builder=builder,
        pm=pm,
        resolved=resolved,
        generation=generation,
        project_dir=project_dir,
        serve=serve,
    )
    if built_previews:
        _print_step("Previews", "ready")

    if generation.skipped and verbose:
        console.print(f"  [dim]Skipped {generation.skipped} unchanged page(s)[/dim]")

    broken_links = _check_generated_links_with_progress(
        builder, sources.modules, sources.docs
    )
    if broken_links:
        _print_step(
            "Links",
            _count_phrase(len(broken_links), "broken internal link"),
            marker="!",
            marker_style="yellow",
            label_style="bold yellow",
        )
        for broken_link in broken_links:
            _print_step_detail(
                f"{broken_link.source_page}:{broken_link.line_number} -> {broken_link.target}",
                style="yellow",
            )
    else:
        _print_step("Links", "valid")

    did_install = _install_dependencies(builder)
    _print_step(
        "Dependencies",
        "installed" if did_install else "up to date",
    )

    llm_files = 0
    if not serve:
        export = _export_static_site(
            builder=builder,
            config=config,
            resolved=resolved,
            modules=sources.modules,
            docs=sources.docs,
            pm=pm,
        )
        llm_files = export.llm_files
        export_detail = "Site export completed"
        if llm_files:
            llm_names = []
            if resolved.generate_llms_txt:
                llm_names.append("llms.txt")
            if resolved.generate_llms_full_txt:
                llm_names.append("llms-full.txt")
            export_detail = f"{export_detail}, {', '.join(llm_names)}"
        _print_step("Export", export_detail)
        _print_build_output(export.output_lines)

    elapsed = time.monotonic() - t0
    done_detail = (
        f"{_count_phrase(generation.total_pages, 'page')}, ready in {elapsed:.1f}s"
        if serve
        else f"{_count_phrase(generation.total_pages, 'page')} in {elapsed:.1f}s"
    )
    _print_step("Done", done_detail, label_style="bold green")
    if not serve:
        _print_step(
            "Site ready",
            f"{config.output_dir}/",
            marker="✨",
            marker_style="magenta",
            label_style="bold magenta",
        )

    if serve:
        _start_dev_server(
            builder=builder,
            config=config,
            resolved=resolved,
            project_dir=project_dir,
            port=port,
            open_browser=open_browser,
            verbose=verbose,
            kill_existing=kill_existing,
        )
