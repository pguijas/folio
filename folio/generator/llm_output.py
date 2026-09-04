from __future__ import annotations

import re
from pathlib import Path

from folio.config import Config
from folio.features import (
    disabled_api_feature_for_module,
    disabled_doc_feature_for_route,
)
from folio.generator.mdx_writer import _render_signature
from folio.generator.site_builder import SiteBuilder
from folio.ir import ClassIR, DocstringIR, FunctionIR, ModuleIR
from folio.parser.markdown_parser import MarkdownResult

# The MDX-to-Markdown rules already exist as a static method on SiteBuilder,
# which uses them for the per-page markdown copies. It reads no instance state,
# so llms-full.txt calls the same function instead of keeping a second copy of
# the rules that could drift.
_mdx_to_markdown = SiteBuilder._mdx_to_markdown

_LEADING_H1_RE = re.compile(r"^#\s+\S")


def _inline(text: object) -> str:
    """Collapse a value onto a single line of plain text."""
    return " ".join(str(text).split())


def _table_cell(text: object) -> str:
    return _inline(text).replace("|", "\\|")


def _absolute_link(path: str, site_url: str = "") -> str:
    if not site_url:
        return path
    return f"{site_url.rstrip('/')}{path}"


def _doc_link(route: str, site_url: str = "", docs_route_base: str = "/docs") -> str:
    normalized = route.strip("/")
    docs_route_base = docs_route_base.rstrip("/") or "/docs"
    if normalized in {"", "index"}:
        return _absolute_link(f"{docs_route_base}/", site_url)
    if normalized.endswith("/index"):
        normalized = normalized[: -len("/index")]
    return _absolute_link(f"{docs_route_base}/{normalized}/", site_url)


def _api_link(
    module_name: str,
    site_url: str = "",
    docs_route_base: str = "/docs",
) -> str:
    docs_route_base = docs_route_base.rstrip("/") or "/docs"
    path = f"{docs_route_base}/api-reference/{module_name.replace('.', '/')}/"
    return _absolute_link(path, site_url)


def _source_citation(source_file: str, line_number: int, project_dir: str = "") -> str:
    """Render a `path:line` citation, relative to the project directory."""
    if not source_file:
        return ""
    path = source_file
    root = project_dir.rstrip("/")
    if root and path.startswith(f"{root}/"):
        path = path[len(root) + 1 :]
    elif Path(path).is_absolute():
        # Without a project directory to strip, the absolute build-machine path
        # is noise; the file name still identifies the symbol.
        path = Path(path).name
    return f"{path}:{line_number}" if line_number > 0 else path


def _heading_block(heading: str, citation: str = "", url: str = "") -> str:
    lines = [heading]
    if url:
        lines.append(f"URL: {url}")
    if citation:
        lines.append(f"Source: {citation}")
    return "\n".join(lines)


def _prose_blocks(docstring: DocstringIR) -> list[str]:
    blocks: list[str] = []
    if docstring.short_description:
        blocks.append(docstring.short_description)
    if docstring.long_description:
        blocks.append(docstring.long_description)
    return blocks


def _tail_blocks(docstring: DocstringIR) -> list[str]:
    blocks: list[str] = []
    if docstring.examples:
        blocks.append("**Examples:**")
        blocks.extend(f"```python\n{example}\n```" for example in docstring.examples)
    if docstring.notes:
        note_lines = [f"- {_inline(note)}" for note in docstring.notes]
        blocks.append("\n".join(["**Notes:**", *note_lines]))
    return blocks


def _arg_table(func: FunctionIR) -> str:
    """Render the argument table for a function, or an empty string."""
    if not func.args:
        return ""
    rows = [
        "| Parameter | Type | Default | Description |",
        "| --- | --- | --- | --- |",
    ]
    for arg in func.args:
        if arg.kind == "var_positional":
            name = f"*{arg.name}"
        elif arg.kind == "var_keyword":
            name = f"**{arg.name}"
        else:
            name = arg.name
        default = f"`{arg.default}`" if arg.default is not None else ""
        rows.append(
            f"| `{name}` | `{arg.type or 'Any'}` | {default} "
            f"| {_table_cell(arg.description)} |"
        )
    return "\n".join(rows)


def _function_blocks(func: FunctionIR, heading: str, project_dir: str) -> list[str]:
    is_property = func.kind == "property"
    blocks = [
        _heading_block(
            f"{heading} {func.name}",
            _source_citation(func.source_file, func.line_number, project_dir),
        ),
        f"```python\n{_render_signature(func, show_parens=not is_property)}\n```",
    ]
    blocks.extend(_prose_blocks(func.docstring))

    if not is_property:
        table = _arg_table(func)
        if table:
            blocks.append(table)

    if func.returns:
        label = "Type" if is_property else "Returns"
        description = _inline(func.returns.description)
        suffix = f" - {description}" if description else ""
        blocks.append(f"**{label}:** `{func.returns.type}`{suffix}")

    if func.raises:
        raise_lines = [
            f"- `{r.exception}` - {_inline(r.description)}"
            if r.description
            else f"- `{r.exception}`"
            for r in func.raises
        ]
        blocks.append("\n".join(["**Raises:**", *raise_lines]))

    blocks.extend(_tail_blocks(func.docstring))
    return blocks


def _class_blocks(cls: ClassIR, project_dir: str) -> list[str]:
    blocks = [
        _heading_block(
            f"## {cls.name}",
            _source_citation(cls.source_file, cls.line_number, project_dir),
        )
    ]
    blocks.extend(_prose_blocks(cls.docstring))
    blocks.extend(_tail_blocks(cls.docstring))
    for method in cls.methods:
        blocks.extend(_function_blocks(method, "###", project_dir))
    return blocks


def _module_blocks(mod: ModuleIR, config: Config | None) -> list[str]:
    project_dir = config.project_dir if config else ""
    url = _api_link(mod.name, config.site_url, config.docs_route_base) if config else ""
    blocks = [
        _heading_block(
            f"# {mod.name}",
            _source_citation(mod.source_file, 0, project_dir),
            url,
        )
    ]
    blocks.extend(_prose_blocks(mod.docstring))
    blocks.extend(_tail_blocks(mod.docstring))
    for cls in mod.classes:
        blocks.extend(_class_blocks(cls, project_dir))
    for func in mod.functions:
        blocks.extend(_function_blocks(func, "##", project_dir))
    return blocks


def _doc_blocks(doc: MarkdownResult, config: Config | None) -> list[str]:
    """Split a document into its heading block and its Markdown body."""
    title = doc.frontmatter.get("title", doc.route)
    # Strip MDX before looking for the H1: import/export lines and JSX can sit
    # above the heading in a page's source.
    content = _mdx_to_markdown(doc.content).strip()
    first_line, _, rest = content.partition("\n")
    if _LEADING_H1_RE.match(first_line):
        heading, body = first_line, rest.strip("\n")
    else:
        heading, body = f"# {title}", content
    url = (
        _doc_link(doc.route, config.site_url, config.docs_route_base) if config else ""
    )
    blocks = [_heading_block(heading, url=url)]
    if body:
        blocks.append(body)
    return blocks


def generate_llms_txt(
    config: Config, modules: list[ModuleIR], docs: list[MarkdownResult]
) -> str:
    """Generate llmstxt.org format with project name, doc links, API reference links."""
    lines: list[str] = []

    # Project header
    lines.append(f"# {config.project_name}")
    lines.append("")
    if config.landing_hero_description:
        lines.append(f"> {_inline(config.landing_hero_description)}")
        lines.append("")

    # Doc links
    if docs:
        lines.append("## Docs")
        for doc in docs:
            if disabled_doc_feature_for_route(doc.route):
                continue
            title = doc.frontmatter.get("title", doc.route)
            link = _doc_link(doc.route, config.site_url, config.docs_route_base)
            description = _inline(doc.frontmatter.get("description", ""))
            suffix = f": {description}" if description else ""
            lines.append(f"- [{title}]({link}){suffix}")
        lines.append("")

    # API reference links
    if modules:
        lines.append("## API Reference")
        for mod in modules:
            if disabled_api_feature_for_module(mod.name):
                continue
            link = _api_link(mod.name, config.site_url, config.docs_route_base)
            description = _inline(mod.docstring.short_description)
            suffix = f": {description}" if description else ""
            lines.append(f"- [{mod.name}]({link}){suffix}")
        lines.append("")

    return "\n".join(lines)


def generate_llms_full_txt(
    modules: list[ModuleIR],
    docs: list[MarkdownResult],
    config: Config | None = None,
) -> str:
    """Generate full content concatenated, separated by ---.

    When ``config`` is supplied every section carries the page URL it was built
    from, so an agent reading the file can cite the published page.
    """
    sections: list[str] = []

    # Documentation sections
    for doc in docs:
        if disabled_doc_feature_for_route(doc.route):
            continue
        sections.append("\n\n".join(_doc_blocks(doc, config)))

    # API reference sections
    for mod in modules:
        if disabled_api_feature_for_module(mod.name):
            continue
        sections.append("\n\n".join(_module_blocks(mod, config)))

    # Blank lines around the separator keep it a thematic break; without them a
    # section ending in a paragraph turns that paragraph into a setext heading.
    return "\n\n---\n\n".join(sections)
