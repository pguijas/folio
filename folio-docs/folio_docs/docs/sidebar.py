from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from folio_docs.features import disabled_doc_feature_for_route
from folio_docs.ir import ModuleIR
from folio_docs.slugs import slugify

if TYPE_CHECKING:
    from folio_docs.parser.markdown_parser import MarkdownResult

_SIDEBAR_EMOJI_RE = re.compile("[‍⌀-⏿☀-➿︎-️\U0001f000-\U0001faff]+")


def _meta_value_to_ts(value: Any, *, indent: int = 2) -> list[str]:
    if isinstance(value, dict):
        lines = ["{"]
        child_indent = " " * (indent + 2)
        for key, child_value in value.items():
            escaped_key = key.replace("\\", "\\\\").replace('"', '\\"')
            rendered = _meta_value_to_ts(child_value, indent=indent + 2)
            if len(rendered) == 1:
                lines.append(f'{child_indent}"{escaped_key}": {rendered[0]},')
            else:
                lines.append(f'{child_indent}"{escaped_key}": {rendered[0]}')
                lines.extend(rendered[1:-1])
                lines.append(f"{child_indent}{rendered[-1]},")
        lines.append("}")
        return lines
    if isinstance(value, bool):
        return ["true" if value else "false"]
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return [f'"{escaped}"']


def _meta_to_ts(meta: dict[str, Any]) -> str:
    """Convert a meta dict to a TypeScript `export default { ... }` string."""
    lines = ["export default {"]
    for key, value in meta.items():
        escaped_key = key.replace("\\", "\\\\").replace('"', '\\"')
        rendered = _meta_value_to_ts(value)
        if len(rendered) == 1:
            lines.append(f'  "{escaped_key}": {rendered[0]},')
        else:
            lines.append(f'  "{escaped_key}": {rendered[0]}')
            lines.extend(rendered[1:-1])
            lines.append(f"  {rendered[-1]},")
    lines.append("}")
    return "\n".join(lines)


def meta_to_ts(meta: dict[str, Any]) -> str:
    """Public wrapper for rendering a Nextra ``_meta.ts`` from a meta dict.

    Exposed for plugins that emit their own ``_meta.ts`` entries (e.g. the
    openapi plugin) so they share Folio's exact serialization.
    """
    return _meta_to_ts(meta)


def _build_module_tree(modules: list[ModuleIR]) -> dict:
    """Build a nested tree from dotted module names.

    Returns a dict where keys are path segments and values are either
    nested dicts (intermediate nodes) or None (leaf modules).
    """
    tree: dict = {}
    for mod in modules:
        parts = mod.name.split(".")
        node = tree
        for part in parts[:-1]:
            if part not in node:
                node[part] = {}
            elif node[part] is None:
                node[part] = {}
            node = node[part]
        leaf = parts[-1]
        if leaf not in node:
            node[leaf] = None
        # If already an intermediate node, keep it as a dict

    return tree


def _title_case(slug: str) -> str:
    """Convert a slug to a human-readable title."""
    return slug.replace("_", " ").replace("-", " ").title()


def _sidebar_title(title: Any, fallback: str) -> str:
    """Normalize a page title for Nextra sidebar metadata."""
    raw_title = title if isinstance(title, str) and title.strip() else fallback
    cleaned = _SIDEBAR_EMOJI_RE.sub("", raw_title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or fallback


def _folder_meta(title: str, *, default_collapsed: bool) -> str | dict[str, Any]:
    if not default_collapsed:
        return title
    return {"title": title, "theme": {"collapsed": True}}


def _generate_meta_from_tree(
    tree: dict,
    path_prefix: str,
    result: dict[str, str],
    *,
    include_index: bool = False,
    default_collapsed: bool = False,
) -> None:
    """Recursively generate _meta.ts files from a module tree."""
    meta: dict[str, Any] = {}
    if include_index:
        meta["index"] = {"display": "hidden"}
    for key, subtree in tree.items():
        if isinstance(subtree, dict) and subtree:
            meta[key] = _folder_meta(
                _title_case(key),
                default_collapsed=default_collapsed,
            )
            child_prefix = f"{path_prefix}/{key}" if path_prefix else key
            _generate_meta_from_tree(
                subtree,
                child_prefix,
                result,
                default_collapsed=default_collapsed,
            )
        else:
            meta[key] = _title_case(key)

    meta_path = f"{path_prefix}/_meta.ts" if path_prefix else "_meta.ts"
    result[meta_path] = _meta_to_ts(meta)


# Entries are either (slug, title) for flat pages
# or (slug, title, [child_entry, ...]) for directories. Children take the same
# two shapes, so a directory may declare the order of its own subdirectories.
_DOC_PAGE_ORDER: list[tuple] = [
    ("index", "Overview"),
    ("folio-docs", "Folio Docs"),
    (
        "agents",
        "Folio for Agents",
        [
            ("index", "Overview"),
            (
                "board",
                "Board",
                [
                    ("index", "Overview"),
                    ("start", "Start a board"),
                    ("formats", "Board formats"),
                    ("cli", "CLI reference"),
                    ("agents", "Operating a board"),
                ],
            ),
            ("board-component", "KanbanBoard"),
        ],
    ),
    ("introduction", "Introduction"),
    ("why-folio", "Why Folio"),
    ("installation", "Installation"),
    ("quickstart", "Quick Start"),
    ("architecture", "Architecture"),
    ("configuration", "Configuration"),
    ("cli", "CLI Reference"),
    ("docstrings", "Writing Docstrings"),
    (
        "components",
        "Components",
        [
            ("index", "Overview"),
            ("feature-cards", "FeatureCard & CardGrid"),
            ("callout", "Callout"),
            ("code-blocks", "Code Blocks"),
            ("code-group", "CodeGroup"),
            ("preview-code", "PreviewCode"),
            ("terminal-session", "TerminalSession"),
            ("config-panel", "ConfigPanel"),
            ("build-artifact", "BuildArtifact"),
            ("doc-preview", "DocPreview"),
            ("browser-frame", "BrowserFrame"),
            ("command-grid", "CommandGrid"),
            ("before-after", "BeforeAfter"),
            ("swot", "Swot"),
            ("compare-matrix", "CompareMatrix"),
            ("pull-quote", "PullQuote"),
            ("stat-strip", "StatStrip"),
            ("checklist", "Checklist"),
            ("hook-map", "HookMap"),
            ("steps", "Steps"),
            ("mermaid", "Mermaid"),
            ("file-tree", "FileTree"),
            ("math", "Math (LaTeX)"),
            ("param-table", "ParamTable"),
            ("class-overview", "ClassOverview"),
            ("method-accordion", "MethodAccordion"),
            ("type-badge", "TypeBadge"),
            ("example-tabs", "ExampleTabs"),
            ("deprecation-notice", "DeprecationNotice"),
            ("copy-page-button", "Page Actions"),
            ("page-feedback", "PageFeedback"),
            ("theme-configurator", "ThemeConfigurator"),
            ("tabs", "Tabs"),
            ("accordion", "Accordion"),
            ("timeline", "Timeline"),
        ],
    ),
    (
        "theming",
        "Theming",
        [
            ("index", "Overview"),
            ("personalization", "Personalization"),
            ("theme-packages", "Theme Packages"),
            ("custom-templates", "Custom Templates"),
        ],
    ),
    (
        "deployment",
        "Deployment",
        [
            ("index", "Overview"),
            ("static-hosts", "Static Hosts"),
            ("github-pages", "GitHub Pages"),
            ("ci-cd", "CI/CD"),
        ],
    ),
    (
        "plugins",
        "Plugins",
        [
            ("index", "Overview"),
            ("catalog", "Catalog"),
            ("authoring", "Writing Plugins"),
            ("trust", "Trust & Safety"),
            ("roadmap", "Roadmap"),
            ("landing", "Landing Page"),
        ],
    ),
    ("migration", "Migrating from Sphinx"),
]


def _order_for_dir(path: tuple[str, ...]) -> list[tuple[str, str]]:
    """Declared page order for a directory, as (slug, title) pairs.

    Walks `_DOC_PAGE_ORDER` one path segment at a time, so a directory at any
    depth orders its pages. Returns [] for a path nothing declares.
    """
    entries: list[tuple] = _DOC_PAGE_ORDER
    for segment in path:
        children = next(
            (entry[2] for entry in entries if entry[0] == segment and len(entry) > 2),
            None,
        )
        if children is None:
            return []
        entries = children
    return [(entry[0], entry[1]) for entry in entries]


_GENERATED_SOURCE_CODE_SLUG = "api-reference"
_GENERATED_SOURCE_CODE_TITLE = "Source Code"
_ROOT_TRAILING_DOC_PAGE_SLUGS = ("contributing",)
_ROOT_TRAILING_GENERATED_PAGE_SLUGS = (_GENERATED_SOURCE_CODE_SLUG,)


def _generate_doc_meta(
    docs: list[MarkdownResult],
    *,
    default_collapsed: bool = False,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Generate ordered doc page entries for the root and subdirectory _meta.ts.

    Returns (root_meta, extra_meta_files) where:
    - root_meta: dict of slug -> title for the root _meta.ts
    - extra_meta_files: dict of path -> ts_content for subdirectory _meta.ts files
    """
    pages_by_dir: dict[tuple[str, ...], dict[str, str]] = {}
    dirs_by_dir: dict[tuple[str, ...], dict[str, str]] = {}
    unlisted_pages: set[tuple[str, ...]] = set()

    for doc in docs:
        if disabled_doc_feature_for_route(doc.route):
            continue
        parts = tuple(part for part in doc.route.split("/") if part)
        if not parts:
            continue

        dir_path = parts[:-1]
        slug = parts[-1]
        title = _sidebar_title(doc.frontmatter.get("title"), _title_case(slug))
        pages_by_dir.setdefault(dir_path, {})[slug] = title
        if doc.unlisted:
            unlisted_pages.add(parts)

        for index, dir_slug in enumerate(dir_path):
            parent = dir_path[:index]
            dirs_by_dir.setdefault(parent, {}).setdefault(
                dir_slug, _title_case(dir_slug)
            )

    for parent_path, child_dirs in dirs_by_dir.items():
        for child_slug in child_dirs:
            child_path = parent_path + (child_slug,)
            index_title = pages_by_dir.get(child_path, {}).get("index")
            if index_title:
                child_dirs[child_slug] = index_title

    extra_meta_files: dict[str, str] = {}

    def subtree_unlisted(dir_path: tuple[str, ...]) -> bool:
        depth = len(dir_path)
        return all(
            page_dir[:depth] != dir_path or page_dir + (slug,) in unlisted_pages
            for page_dir, pages in pages_by_dir.items()
            for slug in pages
        )

    # Omission alone would not delist: Nextra lists content pages by default
    # and _meta.ts only orders and hides. An unlisted page — and a folder
    # whose every page is unlisted, which would otherwise sit in the sidebar
    # as an empty entry — gets the same value nested index pages already use.
    def entry_value(
        path: tuple[str, ...],
        slug: str,
        title: str,
    ) -> str | dict[str, Any]:
        if slug in dirs_by_dir.get(path, {}):
            if subtree_unlisted(path + (slug,)):
                return {"display": "hidden"}
            return _folder_meta(title, default_collapsed=default_collapsed)
        if path + (slug,) in unlisted_pages:
            return {"display": "hidden"}
        return title

    def build_meta_for_dir(path: tuple[str, ...]) -> dict[str, Any]:
        entries: dict[str, str] = {}
        entries.update(pages_by_dir.get(path, {}))
        entries.update(dirs_by_dir.get(path, {}))

        ordered: dict[str, Any] = {}
        remaining = dict(entries)
        if path and "index" in remaining:
            ordered["index"] = {"display": "hidden"}
            remaining.pop("index")
        for slug, title in _order_for_dir(path):
            if slug in remaining:
                ordered[slug] = entry_value(path, slug, remaining.pop(slug))
        for slug, title in remaining.items():
            ordered[slug] = entry_value(path, slug, title)
        return ordered

    all_dirs = set(pages_by_dir) | set(dirs_by_dir)
    for dir_path in sorted(path for path in all_dirs if path):
        extra_meta_files[f"{'/'.join(dir_path)}/_meta.ts"] = _meta_to_ts(
            build_meta_for_dir(dir_path)
        )

    return build_meta_for_dir(()), extra_meta_files


def _move_entries_to_end(meta: dict[str, Any], slugs: tuple[str, ...]) -> None:
    for slug in slugs:
        if slug in meta:
            meta[slug] = meta.pop(slug)


def _apply_nav_order(meta: dict[str, Any], nav: list[str]) -> dict[str, Any]:
    """Apply the documented top-level nav order to entries that exist.

    ``Guide`` represents all authored documentation in its existing order;
    ``API Reference`` and ``Source Code`` both name the generated source tree.
    Other labels match an authored page or folder by slug. Unknown labels are
    ignored instead of creating dead sidebar routes.
    """
    if not nav:
        return meta

    aliases: dict[str, str] = {}
    for key, value in meta.items():
        title = value.get("title") if isinstance(value, dict) else value
        aliases[slugify(key)] = key
        if isinstance(title, str):
            aliases[slugify(title)] = key

    ordered: dict[str, Any] = {}
    for item in nav:
        slug = slugify(item)
        if slug == "guide":
            for key, value in meta.items():
                if key != _GENERATED_SOURCE_CODE_SLUG:
                    ordered.setdefault(key, value)
            continue
        if slug == "source-code":
            slug = _GENERATED_SOURCE_CODE_SLUG
        key = aliases.get(slug)
        if key is not None:
            ordered.setdefault(key, meta[key])

    for key, value in meta.items():
        ordered.setdefault(key, value)
    return ordered


def generate_meta_files(
    nav: list[str],
    modules: list[ModuleIR],
    docs: list[MarkdownResult] | None = None,
    *,
    default_collapsed: bool = False,
) -> dict[str, str]:
    """Generate all _meta.ts files needed (root + docs + source code).

    Returns a dict mapping file paths (relative) to their TS content.
    """
    result: dict[str, str] = {}

    root_meta: dict = {}
    if docs:
        doc_root, doc_extra = _generate_doc_meta(
            docs,
            default_collapsed=default_collapsed,
        )
        root_meta.update(doc_root)
        result.update(doc_extra)
    if modules:
        root_meta[_GENERATED_SOURCE_CODE_SLUG] = _folder_meta(
            _GENERATED_SOURCE_CODE_TITLE,
            default_collapsed=default_collapsed,
        )
    _move_entries_to_end(root_meta, _ROOT_TRAILING_DOC_PAGE_SLUGS)
    _move_entries_to_end(root_meta, _ROOT_TRAILING_GENERATED_PAGE_SLUGS)
    root_meta = _apply_nav_order(root_meta, nav)
    result["_meta.ts"] = _meta_to_ts(root_meta)

    if modules:
        tree = _build_module_tree(modules)
        _generate_meta_from_tree(
            tree,
            _GENERATED_SOURCE_CODE_SLUG,
            result,
            include_index=True,
            default_collapsed=default_collapsed,
        )

    return result
