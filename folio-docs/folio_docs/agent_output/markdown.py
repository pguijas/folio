"""Markdown mirrors for Folio for Agents.

The human site may use MDX components. Agent mirrors deliberately keep the
authored prose and code while reducing that component shell to plain Markdown.
"""

from __future__ import annotations

import re


def mdx_to_markdown(content: str) -> str:
    """Convert generated MDX into the lossy, agent-readable mirror format."""
    markdown = re.sub(r"\A---\n.*?\n---\n?", "", content, flags=re.DOTALL)

    def restore_mermaid(match: re.Match[str]) -> str:
        chart = match.group("chart").replace(r"\`", "`").replace(r"\${", "${")
        return f"```mermaid\n{chart}\n```"

    markdown = re.sub(
        r"<Mermaid\s+chart=\{`(?P<chart>(?:\\.|[^`])*)`\}\s*/>",
        restore_mermaid,
        markdown,
        flags=re.DOTALL,
    )

    protected: list[str] = []

    def protect(match: re.Match[str]) -> str:
        token = f"\x00FOLIO_MARKDOWN_CODE_{len(protected)}\x00"
        protected.append(match.group(0))
        return token

    # A fence indented under a list item, or carried inside a blockquote, is
    # still a fence. Anchoring at column 0 left its contents unshielded, so the
    # component stripper below deleted any `<Tag>` inside it.
    markdown = re.sub(
        r"(?ms)^[ \t>]*(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^[ \t>]*(?P=fence)[ \t]*$",
        protect,
        markdown,
    )
    markdown = re.sub(
        r"(?<!`)(?P<fence>`+)(?P<body>[^\n]*?)(?P=fence)(?!`)",
        protect,
        markdown,
    )
    markdown = re.sub(r"^import\s+.+$", "", markdown, flags=re.MULTILINE)
    markdown = re.sub(r"^export\s+.+$", "", markdown, flags=re.MULTILINE)
    markdown = _strip_mdx_component_tags(markdown)

    for index, value in enumerate(protected):
        markdown = markdown.replace(f"\x00FOLIO_MARKDOWN_CODE_{index}\x00", value)

    markdown = re.sub(r"(?m)^[ \t]+$", "", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip() + "\n"


def _strip_mdx_component_tags(content: str) -> str:
    """Remove PascalCase JSX tags while retaining useful child prose."""
    parts: list[str] = []
    cursor = 0
    length = len(content)

    while cursor < length:
        start = content.find("<", cursor)
        if start == -1:
            parts.append(content[cursor:])
            break

        match = re.match(
            r"<\s*(?P<closing>/?)\s*(?P<name>[A-Z][A-Za-z0-9]*)", content[start:]
        )
        if match is None:
            parts.append(content[cursor : start + 1])
            cursor = start + 1
            continue

        end = _mdx_tag_end(content, start + match.end())
        if end is None:
            parts.append(content[cursor:])
            break

        tag = content[start : end + 1]
        parts.append(content[cursor:start])
        parts.append(
            _mdx_tag_markdown(
                tag,
                name=match.group("name"),
                closing=bool(match.group("closing")),
            )
        )
        cursor = end + 1

    return "".join(parts)


def _mdx_tag_end(content: str, cursor: int) -> int | None:
    quote = ""
    escaped = False
    brace_depth = 0

    while cursor < len(content):
        char = content[cursor]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
        elif char in {'"', "'", "`"}:
            quote = char
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
        elif char == ">" and brace_depth == 0:
            return cursor
        cursor += 1

    return None


def _mdx_string_prop(tag: str, name: str) -> str:
    match = re.search(
        rf"\b{re.escape(name)}\s*=\s*(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
        tag,
        flags=re.DOTALL,
    )
    if match is None:
        return ""
    quote = match.group("quote")
    return match.group("value").replace(f"\\{quote}", quote)


def _mdx_tag_markdown(tag: str, *, name: str, closing: bool) -> str:
    if closing:
        return ""

    self_closing = bool(re.search(r"/\s*>$", tag))
    if self_closing and name in {"FeatureCard", "CommandCard"}:
        title = _mdx_string_prop(tag, "title") or _mdx_string_prop(tag, "command")
        description = _mdx_string_prop(tag, "description")
        href = _mdx_string_prop(tag, "href")
        if not title and not description:
            return ""
        label = f"[{title}]({href})" if title and href else title
        if label and description:
            return f"\n- **{label}**: {description}\n"
        return f"\n- {f'**{label}**' if label else description}\n"

    if not self_closing:
        label_props = {
            "AccordionItem": "title",
            "Step": "title",
            "TabItem": "label",
        }
        label_prop = label_props.get(name)
        if label_prop:
            label = _mdx_string_prop(tag, label_prop)
            if label:
                return f"\n### {label}\n\n"

        if name in {"Callout", "PullQuote", "PreviewCode"}:
            label = _mdx_string_prop(tag, "title") or _mdx_string_prop(tag, "kicker")
            if label:
                return f"\n**{label}**\n\n"

    return ""
