from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from folio.features import disabled_doc_feature_for_route
from folio.ir import ModuleIR

if TYPE_CHECKING:
    from folio.parser.markdown_parser import MarkdownResult


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


def _slugify(text: str) -> str:
    """Convert a nav item to a URL-friendly slug."""
    slug = text.lower().strip()
    slug = slug.replace(".", "-")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def generate_meta_json(nav: list[str]) -> str:
    """Convert nav items to a Nextra _meta.ts string with slugified keys."""
    meta: dict[str, str] = {}
    for item in nav:
        meta[_slugify(item)] = item
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


def _generate_meta_from_tree(
    tree: dict,
    path_prefix: str,
    result: dict[str, str],
    *,
    include_index: bool = False,
) -> None:
    """Recursively generate _meta.ts files from a module tree."""
    meta: dict[str, Any] = {}
    if include_index:
        meta["index"] = {"display": "hidden"}
    for key, subtree in tree.items():
        meta[key] = _title_case(key)
        if isinstance(subtree, dict) and subtree:
            child_prefix = f"{path_prefix}/{key}" if path_prefix else key
            _generate_meta_from_tree(subtree, child_prefix, result)

    meta_path = f"{path_prefix}/_meta.ts" if path_prefix else "_meta.ts"
    result[meta_path] = _meta_to_ts(meta)


# Entries are either (slug, title) for flat pages
# or (slug, title, [(child_slug, child_title), ...]) for directories.
_DOC_PAGE_ORDER: list[tuple] = [
    ("index", "Overview"),
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
            ("command-grid", "CommandGrid"),
            ("before-after", "BeforeAfter"),
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
            ("organic-editorial-image-prompt", "OrganicEditorialImagePrompt"),
            ("tabs", "Tabs"),
            ("accordion", "Accordion"),
            ("timeline", "Timeline"),
        ],
    ),
    ("theming", "Theming"),
    ("deployment", "Deployment"),
    ("ci-cd", "CI/CD"),
    ("migration", "Migrating from Sphinx"),
]


def _generate_doc_meta(
    docs: list[MarkdownResult],
) -> tuple[dict[str, str], dict[str, str]]:
    """Generate ordered doc page entries for the root and subdirectory _meta.ts.

    Returns (root_meta, extra_meta_files) where:
    - root_meta: dict of slug -> title for the root _meta.ts
    - extra_meta_files: dict of path -> ts_content for subdirectory _meta.ts files
    """
    pages_by_dir: dict[tuple[str, ...], dict[str, str]] = {}
    dirs_by_dir: dict[tuple[str, ...], dict[str, str]] = {}

    for doc in docs:
        if disabled_doc_feature_for_route(doc.route):
            continue
        parts = tuple(part for part in doc.route.split("/") if part)
        if not parts:
            continue

        dir_path = parts[:-1]
        slug = parts[-1]
        title = doc.frontmatter.get("title", _title_case(slug))
        pages_by_dir.setdefault(dir_path, {})[slug] = title

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

    def order_for_dir(path: tuple[str, ...]) -> list[tuple[str, str]]:
        if not path:
            return [(entry[0], entry[1]) for entry in _DOC_PAGE_ORDER]
        if len(path) == 1:
            for entry in _DOC_PAGE_ORDER:
                if entry[0] == path[0] and len(entry) > 2:
                    return list(entry[2])
        return []

    def build_meta_for_dir(path: tuple[str, ...]) -> dict[str, Any]:
        entries: dict[str, str] = {}
        entries.update(pages_by_dir.get(path, {}))
        entries.update(dirs_by_dir.get(path, {}))

        ordered: dict[str, Any] = {}
        remaining = dict(entries)
        if path and "index" in remaining:
            ordered["index"] = {"display": "hidden"}
            remaining.pop("index")
        for slug, title in order_for_dir(path):
            if slug in remaining:
                ordered[slug] = title
                remaining.pop(slug)
        for slug, title in remaining.items():
            ordered[slug] = title
        return ordered

    all_dirs = set(pages_by_dir) | set(dirs_by_dir)
    for dir_path in sorted(path for path in all_dirs if path):
        extra_meta_files[f"{'/'.join(dir_path)}/_meta.ts"] = _meta_to_ts(
            build_meta_for_dir(dir_path)
        )

    return build_meta_for_dir(()), extra_meta_files


def generate_meta_files(
    nav: list[str],
    modules: list[ModuleIR],
    docs: list[MarkdownResult] | None = None,
) -> dict[str, str]:
    """Generate all _meta.ts files needed (root + docs + api-reference).

    Returns a dict mapping file paths (relative) to their TS content.
    """
    result: dict[str, str] = {}

    root_meta: dict = {}
    if docs:
        doc_root, doc_extra = _generate_doc_meta(docs)
        root_meta.update(doc_root)
        result.update(doc_extra)
    if modules:
        root_meta["api-reference"] = "API Reference"
    result["_meta.ts"] = _meta_to_ts(root_meta)

    if modules:
        tree = _build_module_tree(modules)
        _generate_meta_from_tree(tree, "api-reference", result, include_index=True)

    return result
