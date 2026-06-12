from __future__ import annotations

from folio.config import Config
from folio.features import (
    disabled_api_feature_for_module,
    disabled_doc_feature_for_route,
)
from folio.generator.mdx_writer import _render_signature
from folio.ir import ModuleIR
from folio.parser.markdown_parser import MarkdownResult


def _absolute_link(path: str, site_url: str = "") -> str:
    if not site_url:
        return path
    return f"{site_url.rstrip('/')}{path}"


def _doc_link(route: str, site_url: str = "") -> str:
    normalized = route.strip("/")
    if normalized in {"", "index"}:
        return _absolute_link("/docs/", site_url)
    if normalized.endswith("/index"):
        normalized = normalized[: -len("/index")]
    return _absolute_link(f"/docs/{normalized}/", site_url)


def _api_link(module_name: str, site_url: str = "") -> str:
    path = f"/docs/api-reference/{module_name.replace('.', '/')}/"
    return _absolute_link(path, site_url)


def generate_llms_txt(
    config: Config, modules: list[ModuleIR], docs: list[MarkdownResult]
) -> str:
    """Generate llmstxt.org format with project name, doc links, API reference links."""
    lines: list[str] = []

    # Project header
    lines.append(f"# {config.project_name}")
    lines.append("")

    # Doc links
    if docs:
        lines.append("## Docs")
        for doc in docs:
            if disabled_doc_feature_for_route(doc.route):
                continue
            title = doc.frontmatter.get("title", doc.route)
            lines.append(f"- [{title}]({_doc_link(doc.route, config.site_url)})")
        lines.append("")

    # API reference links
    if modules:
        lines.append("## API Reference")
        for mod in modules:
            if disabled_api_feature_for_module(mod.name):
                continue
            lines.append(f"- [{mod.name}]({_api_link(mod.name, config.site_url)})")
        lines.append("")

    return "\n".join(lines)


def generate_llms_full_txt(modules: list[ModuleIR], docs: list[MarkdownResult]) -> str:
    """Generate full content concatenated, separated by ---."""
    sections: list[str] = []

    # Documentation sections
    for doc in docs:
        if disabled_doc_feature_for_route(doc.route):
            continue
        title = doc.frontmatter.get("title", doc.route)
        content = doc.content
        section_lines = [f"# {title}", "", content]
        sections.append("\n".join(section_lines))

    # API reference sections
    for mod in modules:
        if disabled_api_feature_for_module(mod.name):
            continue
        section_lines = [f"# {mod.name}", ""]
        if mod.docstring.short_description:
            section_lines.append(mod.docstring.short_description)
            section_lines.append("")
        for cls in mod.classes:
            section_lines.append(f"## {cls.name}")
            if cls.docstring.short_description:
                section_lines.append(cls.docstring.short_description)
            for method in cls.methods:
                sig = _render_signature(method)
                section_lines.append(f"### {method.name}")
                section_lines.append(f"```python\n{sig}\n```")
            section_lines.append("")
        for func in mod.functions:
            sig = _render_signature(func)
            section_lines.append(f"## {func.name}")
            section_lines.append(f"```python\n{sig}\n```")
            if func.docstring.short_description:
                section_lines.append(func.docstring.short_description)
            section_lines.append("")
        sections.append("\n".join(section_lines))

    return "\n---\n".join(sections)
