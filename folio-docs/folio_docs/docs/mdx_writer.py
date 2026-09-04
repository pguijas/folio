from __future__ import annotations

import json
import re

import yaml

from folio_docs.docs.xref import resolve_type_link
from folio_docs.ir import ClassIR, FunctionIR, ModuleIR
from folio_docs.parser.markdown_parser import MarkdownResult
from folio_docs.signatures import render_signature


_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
# A backtick run opens a code span that the next run of the same length closes.
# `+` is greedy, so ``a `x` b`` is matched as one span rather than two.
_INLINE_CODE_RE = re.compile(r"(?P<ticks>`+)(?P<body>.+?)(?P=ticks)", re.S)


def _escape_mdx_text(text: str) -> str:
    return (
        text.replace("{", "\\{")
        .replace("}", "\\}")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_mdx_outside_inline_code(text: str) -> str:
    parts: list[str] = []
    pos = 0
    for match in _INLINE_CODE_RE.finditer(text):
        parts.append(_escape_mdx_text(text[pos : match.start()]))
        parts.append(match.group(0))
        pos = match.end()
    parts.append(_escape_mdx_text(text[pos:]))
    return "".join(parts)


def _code_fence_flags(lines: list[str]) -> list[bool]:
    """Mark which lines belong to a fenced code block, fence lines included.

    Only a run of the opener's own character, at least as long and carrying no
    info string, closes a block. Toggling on any ``` prefix instead would let a
    3-tick fence nested inside a 4-tick one flip the tracker back to "outside
    code" and escape real code content.
    """
    flags: list[bool] = []
    fence: tuple[str, int] | None = None
    for line in lines:
        match = _FENCE_RE.match(line)
        if fence is None:
            fence = (match.group(1)[0], len(match.group(1))) if match else None
            flags.append(match is not None)
            continue
        flags.append(True)
        if (
            match
            and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= fence[1]
            and not match.group(2).strip()
        ):
            fence = None
    return flags


def _escape_mdx(text: str) -> str:
    """Escape MDX syntax in docstring prose, leaving code alone.

    MDX parses `{` and `<` as expression and JSX delimiters, so prose has to
    escape them. Code is different: CommonMark treats the content of a fenced
    block or a backtick span as literal text and decodes neither backslash
    escapes nor HTML entities there, so escaping inside code renders the
    escape itself - `/\\{repo\\}` instead of `/{repo}`.
    """
    lines = text.split("\n")
    in_code = _code_fence_flags(lines)

    escaped: list[str] = []
    start = 0
    while start < len(lines):
        end = start
        while end < len(lines) and in_code[end] == in_code[start]:
            end += 1
        chunk = "\n".join(lines[start:end])
        escaped.append(chunk if in_code[start] else _escape_mdx_outside_inline_code(chunk))
        start = end
    return "\n".join(escaped)


def _escape_jsx_attr(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("{", "&#123;")
        .replace("}", "&#125;")
    )


def _frontmatter(data: dict[str, str]) -> str:
    """Generate a YAML frontmatter block."""
    lines = yaml.dump(data, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{lines}\n---\n"


def _render_param_table(
    func: FunctionIR,
    symbol_index: dict[str, str] | None = None,
    current_module: str = "",
) -> str:
    """Render a <ParamTable> JSX component for a function's arguments."""
    if not func.args:
        return ""
    args_list: list[dict[str, str | None]] = []
    for arg in func.args:
        if arg.kind == "var_positional":
            display_name = f"*{arg.name}"
        elif arg.kind == "var_keyword":
            display_name = f"**{arg.name}"
        else:
            display_name = arg.name
        entry: dict[str, str | None] = {
            "name": display_name,
            "type": arg.type or "Any",
            "default": arg.default if arg.default is not None else "",
            "description": arg.description,
        }
        if symbol_index and arg.type:
            href = resolve_type_link(arg.type, symbol_index, current_module)
            if href:
                entry["href"] = href
        args_list.append(entry)
    args_json = json.dumps(args_list, indent=2)
    return f"<ParamTable args={{{args_json}}} />"


def _effective_source_ref(repo_url: str, source_ref: str | None = None) -> str:
    if isinstance(source_ref, str) and source_ref.strip():
        return source_ref.strip()
    return "main"


def _source_link(
    repo_url: str,
    source_file: str,
    line_number: int,
    source_root: str = "",
    source_ref: str | None = None,
) -> str:
    if not repo_url:
        return ""
    if source_root and source_file.startswith(source_root):
        rel_path = source_file[len(source_root) :].lstrip("/")
    else:
        rel_path = source_file
    ref = _effective_source_ref(repo_url, source_ref)
    href = f"{repo_url.rstrip('/')}/blob/{ref}/{rel_path}#L{line_number}"
    return f' <SourceLink href="{href}" />'


def _render_function(
    func: FunctionIR,
    heading_level: int = 3,
    repo_url: str = "",
    source_root: str = "",
    source_ref: str | None = None,
    symbol_index: dict[str, str] | None = None,
    current_module: str = "",
) -> str:
    """Render a full function section in MDX."""
    parts: list[str] = []
    heading = "#" * heading_level
    is_property = func.kind == "property"

    if func.kind == "staticmethod":
        parts.append("`@staticmethod`\n")
    elif func.kind == "classmethod":
        parts.append("`@classmethod`\n")
    elif is_property:
        parts.append("`@property`\n")

    source = _source_link(
        repo_url, func.source_file, func.line_number, source_root, source_ref
    )
    parts.append(f"{heading} `{func.name}`{source}\n")

    sig = render_signature(func, show_parens=not is_property)
    parts.append(f"```python\n{sig}\n```\n")

    if func.docstring.short_description:
        parts.append(f"{_escape_mdx(func.docstring.short_description)}\n")
    if func.docstring.long_description:
        parts.append(f"{_escape_mdx(func.docstring.long_description)}\n")

    if not is_property:
        param_table = _render_param_table(
            func, symbol_index=symbol_index, current_module=current_module
        )
        if param_table:
            parts.append(f"{param_table}\n")

    if func.returns:
        ret_type = func.returns.type
        ret_href = None
        if symbol_index and ret_type:
            ret_href = resolve_type_link(ret_type, symbol_index, current_module)
        if ret_href:
            linked_type = f"[`{ret_type}`]({ret_href})"
        else:
            linked_type = f"`{ret_type}`"
        if is_property:
            parts.append(
                f"**Type:** {linked_type} - {_escape_mdx(func.returns.description)}\n"
            )
        else:
            parts.append(
                f"**Returns:** {linked_type} - {_escape_mdx(func.returns.description)}\n"
            )

    for r in func.raises:
        parts.append(f"**Raises:** `{r.exception}` - {_escape_mdx(r.description)}\n")

    for example in func.docstring.examples:
        parts.append(f"```python\n{example}\n```\n")

    return "\n".join(parts)


def _render_class(
    cls: ClassIR,
    heading_level: int = 3,
    repo_url: str = "",
    source_root: str = "",
    source_ref: str | None = None,
    symbol_index: dict[str, str] | None = None,
    current_module: str = "",
) -> str:
    """Render a full class section in MDX."""
    parts: list[str] = []

    # Build base class data with optional hrefs for cross-references
    if symbol_index and cls.bases:
        bases_data: list[dict[str, str]] = []
        for base in cls.bases:
            entry: dict[str, str] = {"name": base}
            href = resolve_type_link(base, symbol_index, current_module)
            if href:
                entry["href"] = href
            bases_data.append(entry)
        bases_prop = f"bases={{{json.dumps(bases_data)}}}"
    else:
        bases_prop = f"bases={{{json.dumps(cls.bases)}}}"

    decorators_json = json.dumps(cls.decorators)
    escaped_name = _escape_jsx_attr(cls.name)
    source = (
        _source_link(
            repo_url, cls.source_file, cls.line_number, source_root, source_ref
        )
        if cls.source_file
        else ""
    )
    parts.append(
        f'<ClassOverview name="{escaped_name}" {bases_prop} decorators={{{decorators_json}}} />{source}\n'
    )

    if cls.docstring.short_description:
        parts.append(f"{_escape_mdx(cls.docstring.short_description)}\n")
    if cls.docstring.long_description:
        parts.append(f"{_escape_mdx(cls.docstring.long_description)}\n")

    for method in cls.methods:
        parts.append(
            _render_function(
                method,
                heading_level=heading_level,
                repo_url=repo_url,
                source_root=source_root,
                source_ref=source_ref,
                symbol_index=symbol_index,
                current_module=current_module,
            )
        )

    for inner in cls.inner_classes:
        parts.append(
            _render_class(
                inner,
                heading_level=heading_level + 1,
                repo_url=repo_url,
                source_root=source_root,
                source_ref=source_ref,
                symbol_index=symbol_index,
                current_module=current_module,
            )
        )

    return "\n".join(parts)


def api_reference_index_to_mdx(modules: list[ModuleIR]) -> str:
    """Render the generated source code overview page."""
    parts: list[str] = [
        _frontmatter(
            {
                "title": "Source Code",
                "description": "Generated source code documentation for project modules.",
            }
        ),
    ]

    if not modules:
        parts.append("# Source Code\n")
        parts.append("No Python modules were found.\n")
        return "\n".join(parts)

    module_entries = []
    for module in sorted(modules, key=lambda item: item.name):
        module_entries.append(
            {
                "name": module.name,
                "description": module.docstring.short_description
                or "Module documentation.",
                "href": f"./{module.name.replace('.', '/')}/",
                "classCount": len(module.classes),
                "functionCount": len(module.functions),
            }
        )

    modules_json = json.dumps(module_entries, indent=2)
    parts.append(f"<ApiReferenceIndex modules={{{modules_json}}} />\n")

    return "\n".join(parts)


def module_to_mdx(
    module: ModuleIR,
    repo_url: str = "",
    source_root: str = "",
    source_ref: str | None = None,
    symbol_index: dict[str, str] | None = None,
) -> str:
    """Convert a ModuleIR into an MDX string."""
    parts: list[str] = []

    fm_data: dict[str, str] = {"title": module.name}
    if module.docstring.short_description:
        fm_data["description"] = module.docstring.short_description
    parts.append(_frontmatter(fm_data))

    source = (
        _source_link(repo_url, module.source_file, 1, source_root, source_ref)
        if repo_url
        else ""
    )
    parts.append(f"# {module.name}{source}\n")

    if module.docstring.short_description:
        parts.append(f"{_escape_mdx(module.docstring.short_description)}\n")
    if module.docstring.long_description:
        parts.append(f"{_escape_mdx(module.docstring.long_description)}\n")

    if module.classes:
        parts.append("## Classes\n")
        for cls in module.classes:
            parts.append(
                _render_class(
                    cls,
                    repo_url=repo_url,
                    source_root=source_root,
                    source_ref=source_ref,
                    symbol_index=symbol_index,
                    current_module=module.name,
                )
            )

    if module.functions:
        parts.append("## Functions\n")
        for func in module.functions:
            parts.append(
                _render_function(
                    func,
                    repo_url=repo_url,
                    source_root=source_root,
                    source_ref=source_ref,
                    symbol_index=symbol_index,
                    current_module=module.name,
                )
            )

    return "\n".join(parts)


_RELATIVE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((\.\./[^)]+)\)")
_HTML_TAG_RE = re.compile(
    r"<(iframe|script|style|video|audio|object|embed)[^>]*(?:/>|>[\s\S]*?</\1>)",
    re.IGNORECASE,
)
_RST_DIRECTIVE_RE = re.compile(r"```\{[^}]+\}\n[\s\S]*?```")
_MD_LINK_EXT_RE = re.compile(r"\]\(([^)]+)\.md\)")
_BARE_CURLY_RE = re.compile(r"(?<!\\)\{(?!/\*)")
# The opening rule spares `{/*`, so the closing rule has to spare `*/}` or an
# MDX comment comes out half-escaped — `{/* … */\}` — and the file stops
# parsing with "Expecting Unicode escape sequence \uXXXX", which names
# neither the brace nor the comment. Both rules are local to one line, so a
# comment spanning several lines is handled by the two lines that have the
# braces on them.
_BARE_CLOSE_CURLY_RE = re.compile(r"(?<!\*/)\}")
_INLINE_MATH_RE = re.compile(r"\$\$.+?\$\$|(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")
# Spans MDX passes through untouched: inline math and inline code. Code is
# tried first so a `$x$` inside backticks stays part of the code span.
_INLINE_VERBATIM_RE = re.compile(
    r"(?P<ticks>`+)(?:.+?)(?P=ticks)|" + _INLINE_MATH_RE.pattern
)
_MERMAID_BLOCK_RE = re.compile(r"```mermaid\n([\s\S]*?)```")


def _escape_curly_outside_math(line: str) -> str:
    """Escape bare curly braces, preserving inline math and inline code.

    MDX leaves both alone, and CommonMark decodes no backslash escape inside a
    backtick span, so escaping there renders the backslashes to the reader.
    """
    parts: list[str] = []
    last_end = 0
    for m in _INLINE_VERBATIM_RE.finditer(line):
        segment = line[last_end : m.start()]
        segment = _BARE_CURLY_RE.sub(r"\\{", segment)
        segment = _BARE_CLOSE_CURLY_RE.sub(r"\\}", segment)
        parts.append(segment)
        parts.append(m.group(0))
        last_end = m.end()
    segment = line[last_end:]
    segment = _BARE_CURLY_RE.sub(r"\\{", segment)
    segment = _BARE_CLOSE_CURLY_RE.sub(r"\\}", segment)
    parts.append(segment)
    return "".join(parts)


def _strip_relative_images(content: str) -> str:
    return _RELATIVE_IMAGE_RE.sub("", content)


def _convert_mermaid_blocks(content: str) -> str:
    """Convert fenced ```mermaid code blocks into <Mermaid chart="..." /> JSX.

    Only converts top-level mermaid blocks. Blocks nested inside an outer
    fenced code block (4+ backticks, e.g. ````md) are left untouched so that
    documentation examples are preserved as-is.
    """
    lines = content.split("\n")
    result: list[str] = []
    outer_fence: str | None = None  # tracks enclosing fence (4+ ticks)
    mermaid_fence = False  # inside a top-level ```mermaid block
    mermaid_lines: list[str] = []

    for line in lines:
        stripped = line.rstrip()

        # Detect fences: only backtick fences, count the run of backticks
        if stripped.startswith("```"):
            tick_run = len(stripped) - len(stripped.lstrip("`"))

            if outer_fence is not None:
                # We're inside an outer (4+) fence — check if this closes it
                if tick_run >= len(outer_fence) and stripped.rstrip("`") == "":
                    outer_fence = None
                result.append(line)
                continue

            if tick_run >= 4:
                # Opening a 4+ tick fence — everything inside is literal
                outer_fence = "`" * tick_run
                result.append(line)
                continue

            # 3-tick fence at top level
            if mermaid_fence:
                # Closing the mermaid block — convert it
                chart = "\n".join(mermaid_lines).rstrip("\n")
                escaped = (
                    chart.replace("\\", "\\\\")
                    .replace("`", "\\`")
                    .replace("${", "\\${")
                )
                result.append(f"<Mermaid chart={{`{escaped}`}} />")
                mermaid_fence = False
                mermaid_lines = []
                continue

            if stripped == "```mermaid":
                mermaid_fence = True
                mermaid_lines = []
                continue

        if mermaid_fence:
            mermaid_lines.append(line)
        else:
            result.append(line)

    return "\n".join(result)


_HTML_CLASS_RE = re.compile(r"(<[^>]*)\bclass=", re.IGNORECASE)


def _sanitize_for_mdx(content: str) -> str:
    content = _convert_mermaid_blocks(content)
    content = _strip_relative_images(content)
    content = _HTML_TAG_RE.sub("", content)
    content = _RST_DIRECTIVE_RE.sub("", content)
    content = _MD_LINK_EXT_RE.sub(r"](\1)", content)

    lines = content.split("\n")
    code_flags = _code_fence_flags(lines)
    result = []
    in_math_block = False
    in_html_tag = False
    for line, in_code_block in zip(lines, code_flags):
        if not in_code_block and line.strip() == "$$":
            in_math_block = not in_math_block
        if not in_code_block and not in_math_block:
            stripped = line.strip()
            is_html_line = stripped.startswith("<") or in_html_tag
            if stripped.startswith("<") and not stripped.endswith(">"):
                in_html_tag = True
            elif in_html_tag and stripped.endswith(">"):
                in_html_tag = False
            if not is_html_line:
                line = _escape_curly_outside_math(line)
            line = _HTML_CLASS_RE.sub(r"\1className=", line)
        result.append(line)
    return "\n".join(result)


def markdown_to_mdx(result: MarkdownResult) -> str:
    """Wrap markdown content with frontmatter to produce MDX."""
    fm = _frontmatter(result.frontmatter) if result.frontmatter else ""
    content = _sanitize_for_mdx(result.content)
    return f"{fm}\n{content}\n"
