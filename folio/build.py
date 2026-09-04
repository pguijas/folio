from __future__ import annotations

import hashlib
import re
import io
import shutil
import time
import warnings
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
from folio.builtins import register_builtin_components
from folio.config import Config, load_config_with_plugins, plugin_config_keys
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
from folio.generator.builtin_drift import check_template_drift
from folio.generator.next_runtime import preflight_check
from folio.generator.llm_output import generate_llms_full_txt, generate_llms_txt
from folio.generator.mdx_contract import (
    CORE_CONFIG_KEYS,
    validate_template_mdx_contract,
)
from folio.generator.template_workspace import (
    FOLIO_STAGING_MARKER,
    _reject_symlinks,
    collect_copyable_files,
    copytree_ignore,
    validate_template_marker_contract,
)
from folio.paths import resolve_contained_dir
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
from folio.parser.markdown_parser import MarkdownResult, parse_markdown_file
from folio.plugin import PluginDocument, PluginManager
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


def _validate_template_contract(template_dir: Path, label: str) -> None:
    """Validate a resolved template directory against the Folio contract.

    Applies the required-files, MDX-component, and injection-marker checks to a
    directory that Folio will copy into ``.build/``. ``label`` names the config
    key (``template.path`` or the merged ``template.overlay_path`` result) so
    errors point at the right surface.
    """
    required = [
        "package.json",
        "pnpm-lock.yaml",
        "next.config.mjs",
        "mdx-components.tsx",
        "app",
        "app/docs/layout.tsx",
        "app/docs/[[...mdxPath]]/page.jsx",
    ]
    missing = [name for name in required if not (template_dir / name).exists()]
    if missing:
        raise ValueError(
            f"{label} is missing required Next/Nextra files: " + ", ".join(missing)
        )
    missing_components = validate_template_mdx_contract(template_dir)
    if missing_components:
        raise ValueError(
            f"{label} mdx-components.tsx is missing Folio MDX contract "
            "components: " + ", ".join(missing_components)
        )
    missing_markers = validate_template_marker_contract(template_dir)
    if missing_markers:
        details = ", ".join(
            f"{marker} in {rel_path}" for rel_path, marker in missing_markers
        )
        raise ValueError(
            f"{label} is missing required Folio injection markers: " + details
        )


def _check_bundled_template_drift(template_dir: Path) -> None:
    """Fail the build when the bundled template drifted from the manifest.

    Bundled-template builds inject builtin components from
    :data:`folio.builtins.BUILTIN_COMPONENTS`, so the manifest and
    ``mdx-components.tsx`` must agree in both directions; otherwise the
    registry/contract would describe components the template does not wire
    (or vice versa) and the failure would only surface at the Next build.
    """
    mdx_path = template_dir / "mdx-components.tsx"
    drift = check_template_drift(mdx_path.read_text(encoding="utf-8"))
    if drift:
        raise ValueError(
            "Bundled template drifted from the builtin component manifest:\n"
            + "\n".join(f"  - {message}" for message in drift)
        )


def _resolve_overlay_dir(project_dir: Path, config: Config) -> Path:
    """Resolve ``template.overlay_path`` against the project root.

    Applies the same containment guards as ``template.path`` via
    :func:`folio.paths.resolve_contained_dir`: the overlay must live inside the
    project and may not point at ``.build/`` or the output directory.
    ``Config.resolve_paths`` already absolutized the path.
    """
    return resolve_contained_dir(
        config.template_overlay_path,
        project_dir,
        config.output_dir,
        "template.overlay_path",
    )


def _materialize_overlay_template(
    bundled_dir: Path,
    overlay_dir: Path,
    staging_dir: Path,
) -> Path:
    """Build a merged template = bundled template + overlay files on top.

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
    """
    resolved_overlay = overlay_dir.resolve()
    resolved_staging = staging_dir.resolve()
    if resolved_overlay == resolved_staging or resolved_overlay.is_relative_to(
        resolved_staging
    ):
        raise ValueError(
            "template.overlay_path cannot point inside the template staging "
            f"directory ({staging_dir.name}/): it is recreated on every build"
        )

    _reject_symlinks(overlay_dir, "template.overlay_path")

    if staging_dir.exists():
        if not (staging_dir / FOLIO_STAGING_MARKER).exists():
            raise ValueError(
                f"Refusing to delete existing directory {staging_dir}: it was "
                f"not created by Folio (missing {FOLIO_STAGING_MARKER} marker). "
                "Remove or rename it manually and rerun the build."
            )
        shutil.rmtree(staging_dir)
    ignore = copytree_ignore()
    # Write the marker BEFORE the (potentially long) bundled copy: if the copy
    # is interrupted (Ctrl-C, disk full), the partial staging dir still carries
    # the marker, so the next build can safely delete and rebuild it instead of
    # refusing forever.
    staging_dir.mkdir(parents=True)
    (staging_dir / FOLIO_STAGING_MARKER).write_text(
        "Folio overlay staging directory; safe to delete.\n",
        encoding="utf-8",
    )
    shutil.copytree(bundled_dir, staging_dir, ignore=ignore, dirs_exist_ok=True)
    shutil.copytree(overlay_dir, staging_dir, ignore=ignore, dirs_exist_ok=True)
    return staging_dir


def _resolve_template_dir(
    project_dir: Path,
    config: Config,
    *,
    build_dir: Path | None = None,
) -> Path:
    # ``Config.resolve_paths`` is the single owner of template-path resolution:
    # it absolutizes ``template.path``/``template.overlay_path`` against the
    # project root before this function ever runs, so the stored values are
    # always either empty or absolute here. We only revalidate containment and
    # required files.
    if config.template_overlay_path:
        # Opt-in partial override: layer the user's files on top of the bundled
        # template, then validate the merged result against the full contract.
        overlay_dir = _resolve_overlay_dir(project_dir, config)
        staging_root = build_dir if build_dir is not None else project_dir / ".build"
        staging_dir = staging_root.parent / f"{staging_root.name}-template"
        bundled_dir = _find_template_dir()
        _check_bundled_template_drift(bundled_dir)
        merged = _materialize_overlay_template(bundled_dir, overlay_dir, staging_dir)
        _validate_template_contract(merged, "template.overlay_path")
        return merged

    if not config.template_path:
        template_dir = _find_template_dir()
        _check_bundled_template_drift(template_dir)
        return template_dir

    resolved = resolve_contained_dir(
        config.template_path,
        project_dir,
        config.output_dir,
        "template.path",
    )
    _validate_template_contract(resolved, "template.path")
    return resolved


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


def _theme_package_signature(resolved: Config) -> str:
    """Signature of the resolved theme.package tree (empty when unset).

    Folded into the manifest ``build`` context and compared against the previous
    build so that changing/removing ``theme.package`` triggers a scoped prune of
    the overlaid files in ``.build/`` (the theme is copied with
    ``copytree(dirs_exist_ok=True)`` and would otherwise leave orphans).

    Collects the copyable files and rejects symlinks in a single traversal
    (``collect_copyable_files``), then feeds the hash from that file list
    instead of re-walking the tree.
    """
    package_path = getattr(resolved, "theme_package_path", "")
    if not package_path:
        return ""
    root = Path(package_path)
    if not root.is_dir():
        return ""
    digest = hashlib.sha256()
    for rel in sorted(collect_copyable_files(root, "theme.package")):
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update((root / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


# Files/dirs under .build/ that are expensive to recreate or hold generated
# content; a scoped prune (triggered when template/theme inputs change without
# --clean) must preserve them.
_SCOPED_CLEAN_PRESERVE = frozenset({"node_modules", ".next", "content"})


def _prune_stale_build_overlay(
    prev_manifest: dict,
    build_dir: Path,
    build_context: dict[str, str],
) -> None:
    """Prune orphaned overlay files when template/theme/route inputs changed.

    ``prepare()`` overlays the template (and any ``theme.package``) with
    ``copytree(dirs_exist_ok=True)`` and never removes files that vanished from
    the source. When a warm ``.build/`` was produced from a *different* template
    or theme, delete everything under it except the preserved entries before
    ``prepare`` re-copies, so stale files cannot survive into the published site.

    When only ``template.docs_route_base`` changed, remove the docs route dir
    that the previous build relocated to — nothing else re-copies over it, so it
    would otherwise stay published at the old URL.
    """
    if not build_dir.exists():
        return
    prev = prev_manifest.get("build")
    if not prev:
        # No prior build context (fresh dir or pre-signature manifest): nothing
        # to compare against, so avoid a surprising wipe.
        return
    current = (build_context.get("template"), build_context.get("theme_package"))
    previous = (prev.get("template"), prev.get("theme_package"))
    if current != previous:
        for entry in build_dir.iterdir():
            if entry.name in _SCOPED_CLEAN_PRESERVE:
                continue
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        return

    prev_route = prev.get("docs_route_base", "")
    if prev_route and prev_route != build_context.get("docs_route_base", ""):
        _remove_relocated_docs_route(build_dir, prev_route)


def _remove_relocated_docs_route(build_dir: Path, route_base: str) -> None:
    """Remove the docs route dir relocated for a previous ``docs_route_base``.

    Template preparation moves ``app/docs`` to ``app/<route segments>``. When
    the configured route base changes between warm builds, the previously
    relocated dir is not overwritten by ``prepare`` (which only re-copies
    ``app/docs``), so it must be dropped explicitly — together with any parent
    directories the old relocation created that are now empty.
    """
    segments = [part for part in route_base.strip("/").split("/") if part]
    if not segments or segments == ["docs"]:
        # /docs is the template's own location: nothing was relocated, and
        # prepare re-copies app/docs anyway.
        return
    app_dir = build_dir / "app"
    old_dir = app_dir.joinpath(*segments)
    if not old_dir.is_dir():
        return
    shutil.rmtree(old_dir)
    parent = old_dir.parent
    while parent != app_dir and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def _build_manifest_context(
    config_path: Path,
    template_dir: Path,
    source_ref: str,
    theme_package_signature: str = "",
    docs_route_base: str = "/docs",
) -> dict[str, str]:
    folio_dir = Path(__file__).parent
    generator_inputs = [
        Path(__file__),
        folio_dir / "config.py",
        folio_dir / "generator" / "site_builder.py",
        folio_dir / "generator" / "template_workspace.py",
        folio_dir / "generator" / "mdx_writer.py",
        folio_dir / "generator" / "mdx_contract.py",
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
        "theme_package": theme_package_signature,
        "docs_route_base": docs_route_base,
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


_FENCED_CODE_RE = re.compile(r"^(?P<fence>```+|~~~+).*?^(?P=fence)", re.S | re.M)
_CODE_SPAN_RE = re.compile(r"(?P<ticks>`+)(?:(?!(?P=ticks)).)*?(?P=ticks)", re.S)
_MARKDOWN_ASSET_RE = re.compile(
    r"!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"\'][^)]*)?\s*\)"
)


def _warn_missing_assets(missing: list[str], route: str) -> None:
    for asset in missing:
        console.print(f"[yellow]warning: {route}: image not found: {asset}[/yellow]")


def _copy_doc_assets(builder: SiteBuilder, doc: MarkdownResult) -> list[str]:
    """Carry a page's local images into the content tree beside it.

    An author writes ``![The board](board.png)`` next to their Markdown. MDX
    turns that into a module import resolved against the generated ``.mdx``,
    so unless the file travels with the page the build fails outright. Only
    project-local paths move: an absolute URL, a root-relative path and a
    data URI are all left for the browser to resolve.
    """
    if not doc.source_file:
        return []
    source_dir = Path(doc.source_file).parent
    missing: list[str] = []
    seen: set[str] = set()
    # Code is scanned out first. A page that documents Markdown syntax writes
    # `![path](path)` inside backticks to show the grammar, and treating that
    # as a real image warns about a file nobody meant to reference — which is
    # exactly what docs/guide/migration.md did.
    prose = _CODE_SPAN_RE.sub(" ", _FENCED_CODE_RE.sub(" ", doc.content))
    for raw in _MARKDOWN_ASSET_RE.findall(prose):
        target = raw.split("#", 1)[0].split("?", 1)[0].strip()
        if not target or target in seen:
            continue
        seen.add(target)
        if "://" in target or target.startswith(("/", "data:", "#")):
            continue
        if ".." in Path(target).parts:
            missing.append(f"{target} (escapes the docs directory)")
            continue
        lexical_source = source_dir / target
        if _path_traverses_symlink(source_dir, lexical_source):
            missing.append(f"{target} (symlinks are not published)")
            continue
        source = lexical_source.resolve()
        if not source.is_relative_to(source_dir.resolve()):
            missing.append(f"{target} (escapes the docs directory)")
            continue
        if not source.is_file():
            missing.append(target)
            continue
        builder.copy_page_asset(doc.route, target, source)
    return missing


def _path_traverses_symlink(root: Path, target: Path) -> bool:
    """Whether ``target`` crosses a symlink at or below lexical ``root``."""
    try:
        relative = target.relative_to(root)
    except ValueError:
        return True
    current = root
    if current.is_symlink():
        return True
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def _parse_project_sources(
    resolved: Config,
    verbose: bool,
    plugin_views: int = 0,
    plugin_manager: PluginManager | None = None,
) -> BuildSources:
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
            plugin_docs = _collect_plugin_docs(plugin_manager, resolved)

    docs = [*parsed_docs.docs, *plugin_docs]
    _reject_duplicate_doc_routes(docs)

    for doc_path in parsed_docs.scanned_paths:
        if verbose:
            console.print(f"  Scanning {doc_path}")

    # A project with nothing to publish is a misconfiguration worth stopping
    # for — but a plugin view is something to publish. A repository whose only
    # content is a kanban board has no Python and no docs by design, and used
    # to be told to check source paths it never set.
    if not parsed_python.modules and not docs and plugin_views == 0:
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
        docs=docs,
        warnings=source_warnings,
    )


def _collect_plugin_docs(
    plugin_manager: PluginManager | None,
    config: Config,
) -> list[MarkdownResult]:
    """Parse plugin-contributed Markdown through the core document parser."""
    if plugin_manager is None:
        return []

    docs: list[MarkdownResult] = []
    for contribution in plugin_manager.call_isolated(
        "collect_docs",
        policy="fail_fast",
        config=config,
    ):
        if isinstance(contribution, (str, bytes)) or not isinstance(
            contribution, Iterable
        ):
            raise TypeError("collect_docs() must return an iterable of PluginDocument")
        for document in contribution:
            if not isinstance(document, PluginDocument):
                raise TypeError("collect_docs() must return only PluginDocument values")
            route = document.route
            parts = route.split("/")
            if (
                not route
                or route.startswith("/")
                or "\\" in route
                or any(part in {"", ".", ".."} for part in parts)
            ):
                raise ValueError(
                    f"Plugin document route must be a clean relative URL: {route!r}"
                )
            source = document.source
            if not isinstance(source, Path) or source.suffix.lower() not in {
                ".md",
                ".mdx",
            }:
                raise TypeError(
                    "PluginDocument.source must be a pathlib.Path ending in .md or .mdx"
                )
            if not source.is_file():
                raise FileNotFoundError(f"Plugin document source not found: {source}")
            parsed = parse_markdown_file(source)
            parsed.route = route
            parsed.unlisted = document.unlisted
            docs.append(parsed)
    return docs


def _reject_duplicate_doc_routes(docs: list[MarkdownResult]) -> None:
    owners: dict[str, tuple[str, str]] = {}
    for doc in docs:
        owner = doc.source_file or "<generated document>"
        public_route = _canonical_doc_route(doc.route)
        previous = owners.get(public_route)
        if previous is not None:
            previous_route, previous_owner = previous
            raise ValueError(
                f"Documentation route collision at public route {public_route!r}: "
                f"{previous_route!r} ({previous_owner}) and "
                f"{doc.route!r} ({owner})"
            )
        owners[public_route] = (doc.route, owner)


def _canonical_doc_route(route: str) -> str:
    """Mirror the public docs router's aliases for collision detection."""
    parts = route.rstrip("/").split("/")
    if parts[-1:] == ["index"]:
        parts.pop()
    if parts and parts[0] != "api-reference":
        parts = [part.replace("_", "-") for part in parts]
    return "/".join(parts)


def _prepare_builder(
    builder: SiteBuilder,
    build_dir: Path,
    build_context: dict[str, str],
    prev_manifest: dict,
    *,
    clean: bool,
) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            _step_description("Template", "preparing workspace"), total=None
        )
        # Before re-overlaying the template/theme onto a warm .build/, drop any
        # files orphaned by a changed template.path, theme.package, or
        # docs_route_base. --clean already wipes everything, so only the warm
        # path needs pruning.
        if not clean:
            _prune_stale_build_overlay(prev_manifest, build_dir, build_context)
        builder.prepare(clean=clean)


def _write_meta_pages(
    builder: SiteBuilder,
    config: Config,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
) -> None:
    builder.remove_meta_tree("api-reference")
    meta_files = generate_meta_files(
        config.nav,
        modules,
        docs,
        default_collapsed=config.sidebar_default_collapsed,
    )
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
    build_context: dict[str, str],
    clean: bool,
    verbose: bool,
    prev_manifest: dict | None = None,
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
        symbol_index = build_symbol_index(
            published_modules,
            docs_route_base=config.docs_route_base,
        )
        _write_meta_pages(builder, config, published_modules, docs)

        if prev_manifest is None:
            # Callers inside run_build pass the manifest loaded once per build;
            # direct callers (tests, plugins) fall back to loading it here.
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
                # The page survives from the prior build, so it is live in this
                # one: record it, or the emitted-routes set (and the contract
                # built from it) would shrink on every warm build.
                builder.register_route(doc.route)
                # The page is unchanged, but a file beside it may not be:
                # the manifest hashes the Markdown, not the images it
                # references, so assets are refreshed on every build.
                _warn_missing_assets(_copy_doc_assets(builder, doc), doc.route)
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
            _warn_missing_assets(_copy_doc_assets(builder, doc), doc.route)
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
                builder.register_route(route)
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


def build_registry(pm: object, resolved: Config) -> ExtensionRegistry:
    """Assemble the extension registry for a build.

    Registration order: builtin layouts/components first, then config
    ``components:``, then plugin hooks. A config or plugin component may
    shadow a builtin of the same name (the builtin is replaced and a
    ``UserWarning`` is emitted); a duplicate between two non-builtin
    registrations raises ``ValueError``. Builtins are registered through the
    same :class:`ExtensionRegistry` API that plugins use, but via a
    deterministic direct call (not a pluggy hook) so emission order is stable.
    """
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    register_builtin_components(registry)
    register_config_components(registry, resolved)
    pm.call_isolated("register_components", policy="fail_fast", registry=registry)
    pm.call_isolated(
        "register_extensions", policy="fail_fast", registry=registry, config=resolved
    )
    return registry


def _apply_extensions(
    builder: SiteBuilder,
    pm: object,
    resolved: Config,
    registry: ExtensionRegistry | None = None,
) -> None:
    # A full build assembles the registry before it parses sources, so the
    # empty-project check can see the pages plugins will contribute; it hands
    # that registry back here rather than have every plugin's
    # register_extensions run a second time.
    if registry is None:
        registry = build_registry(pm, resolved)
    builder.apply_extensions(registry)

    def _routes_guard() -> Callable[[], None]:
        # Plugins call register_route before write_page; when an impl fails
        # under warn_skip, restore the pre-impl snapshot so a half-registered
        # route cannot whitelist a missing page for the link checker.
        snapshot = builder.emitted_routes()
        return lambda: builder.restore_emitted_routes(snapshot)

    pm.call_isolated(
        "emit_assets",
        policy="warn_skip",
        impl_guard=_routes_guard,
        builder=builder,
        config=resolved,
    )


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
    # Plugin-emitted pages are valid link targets even though they are not in
    # the published docs/modules set; the builder records them as they emit.
    # emitted_routes() is part of the AssetBuilder protocol, so call it
    # directly — a builder without it is a contract violation, not a fallback.
    all_routes.extend(sorted(builder.emitted_routes()))
    builder_config = getattr(builder, "config", None)
    docs_route_base = getattr(builder_config, "docs_route_base", "/docs")
    # Registry views (public pages like /roadmap) and the site root are
    # legitimate link targets outside the docs route space.
    view_routes = getattr(builder, "view_routes", lambda: set())()
    return check_links(
        builder.content_dir,
        all_routes,
        docs_route_base=docs_route_base,
        site_routes={"/"} | view_routes,
        static_root=builder.build_dir / "public",
    )


def _build_timestamp() -> str:
    """This build's UTC start-of-finalize time, for generated metadata."""
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    return stamp.isoformat().replace("+00:00", "Z")


def _finalize_generated_files(
    *,
    builder: SiteBuilder,
    pm: object,
    resolved: Config,
    generation: GenerationResult,
    project_dir: Path,
    serve: bool,
    registry: ExtensionRegistry | None = None,
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
        _apply_extensions(builder, pm, resolved, registry)
        # After the extensions: the component registry and the emitted routes
        # are only complete once every plugin has run.
        builder.write_authoring_contract(
            config_keys=CORE_CONFIG_KEYS | plugin_config_keys(pm),
            generated_at=_build_timestamp(),
        )
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

    llm_files = _write_llm_outputs(
        builder=builder,
        config=config,
        resolved=resolved,
        modules=modules,
        docs=docs,
    )

    pm.call_isolated("post_build", policy="warn_skip", site_dir=resolved.output_dir)
    return ExportResult(llm_files=llm_files, output_lines=output_stream.lines)


def _write_llm_outputs(
    *,
    builder: SiteBuilder,
    config: Config,
    resolved: Config,
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
    serve: bool = False,
) -> int:
    """Render configured LLM outputs to the active site's public root."""
    published_modules = _published_modules(modules)
    llms_txt = (
        generate_llms_txt(config, published_modules, docs)
        if resolved.generate_llms_txt
        else None
    )
    llms_full = (
        generate_llms_full_txt(published_modules, docs, config)
        if resolved.generate_llms_full_txt
        else None
    )
    builder.write_llm_files(llms_txt, llms_full, serve=serve)
    return int(llms_txt is not None) + int(llms_full is not None)


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
    plugin_manager: object | None = None,
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
        plugin_manager=plugin_manager,
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

    # Fail on a missing/old Node or pnpm in the first second, not minutes in.
    preflight_check()

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
    registry = build_registry(pm, resolved)
    sources = _parse_project_sources(
        resolved,
        verbose,
        len(registry.views),
        plugin_manager=pm,
    )
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

    build_dir = (
        Path(build_dir_override) if build_dir_override else project_dir / ".build"
    )
    template_dir = _resolve_template_dir(project_dir, resolved, build_dir=build_dir)
    build_context = _build_manifest_context(
        config_path,
        template_dir,
        config.project_repo_ref,
        theme_package_signature=_theme_package_signature(resolved),
        docs_route_base=resolved.docs_route_base.rstrip("/") or "/docs",
    )
    builder = SiteBuilder(resolved, str(template_dir), str(build_dir), verbose=verbose)
    # Load the previous manifest once per build; both the stale-overlay prune
    # and the incremental page generation compare against the same snapshot.
    prev_manifest = {"sources": {}, "build": {}} if clean else builder.load_manifest()
    _prepare_builder(
        builder,
        build_dir,
        build_context,
        prev_manifest,
        clean=clean,
    )
    _print_step("Template", ".build/ workspace ready")
    generation = _generate_content_pages(
        builder=builder,
        config=config,
        modules=sources.modules,
        docs=sources.docs,
        project_dir=project_dir,
        build_context=build_context,
        clean=clean,
        verbose=verbose,
        prev_manifest=prev_manifest,
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
        registry=registry,
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
                f"{broken_link.source_page}:{broken_link.line_number} → {broken_link.target}",
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
    if serve:
        llm_files = _write_llm_outputs(
            builder=builder,
            config=config,
            resolved=resolved,
            modules=sources.modules,
            docs=sources.docs,
            serve=True,
        )
    else:
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
            marker="✓",
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
            plugin_manager=pm,
        )
