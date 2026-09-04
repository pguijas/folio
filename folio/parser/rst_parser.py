from __future__ import annotations

import re


def _dedent_directive_body(body: str) -> str:
    lines = body.split("\n")
    dedented: list[str] = []
    for line in lines:
        if line.strip():
            dedented.append(re.sub(r"^   ", "", line))
        else:
            dedented.append("")
    return "\n".join(dedented).strip()


def rst_to_mdx(rst: str) -> str:
    """Convert RST syntax to MDX using regex transformations."""
    result = rst

    # Convert RST headings with underlines to markdown headings
    # Process from most specific (^) to most general (=)
    # = heading (h1), - heading (h2), ~ heading (h3), ^ heading (h4)
    heading_chars = [
        ("=", "#"),
        ("-", "##"),
        ("~", "###"),
        ("^", "####"),
    ]
    for char, prefix in heading_chars:
        escaped = re.escape(char)
        pattern = rf"^(.+)\n{escaped}{{3,}}\s*$"
        result = re.sub(pattern, rf"{prefix} \1", result, flags=re.MULTILINE)

    # Convert code blocks: .. code-block:: <lang> to fenced code blocks
    def _convert_code_block(match: re.Match) -> str:
        lang = match.group(1).strip()
        body = match.group(2)
        content = _dedent_directive_body(body)
        return f"```{lang}\n{content}\n```"

    result = re.sub(
        r"\.\. code-block::\s*(\w+)\s*\n((?:\n|[ \t]+[^\n]*\n?)+)",
        _convert_code_block,
        result,
    )

    # Convert .. note:: to <Callout type="info">
    def _convert_note(match: re.Match) -> str:
        body = match.group(1)
        content = _dedent_directive_body(body)
        return f'<Callout type="info">\n{content}\n</Callout>'

    result = re.sub(
        r"\.\. note::\s*\n((?:\n|[ \t]+[^\n]*\n?)+)",
        _convert_note,
        result,
    )

    # Convert .. warning:: to <Callout type="warning">
    def _convert_warning(match: re.Match) -> str:
        body = match.group(1)
        content = _dedent_directive_body(body)
        return f'<Callout type="warning">\n{content}\n</Callout>'

    result = re.sub(
        r"\.\. warning::\s*\n((?:\n|[ \t]+[^\n]*\n?)+)",
        _convert_warning,
        result,
    )

    # Convert additional RST admonition directives to Callout components
    directive_map = {
        "tip": "tip",
        "hint": "tip",
        "danger": "danger",
        "error": "danger",
        "important": "warning",
        "caution": "warning",
        "attention": "warning",
        "seealso": "info",
        "deprecated": "danger",
        "versionadded": "note",
        "versionchanged": "note",
    }

    def _make_directive_converter(callout_type: str):
        def _converter(match: re.Match) -> str:
            directive_name = match.group(1)
            version_arg = (match.group(2) or "").strip()
            body = match.group(3)
            content = _dedent_directive_body(body)
            if version_arg and directive_name in (
                "deprecated",
                "versionadded",
                "versionchanged",
            ):
                label = directive_name.replace("version", "Version ")
                if directive_name == "deprecated":
                    label = "Deprecated since"
                prefix = f"**{label} {version_arg}:** "
                content = (
                    prefix + content
                    if content
                    else prefix.rstrip(": ") + " " + version_arg
                )
            return f'<Callout type="{callout_type}">\n{content}\n</Callout>'

        return _converter

    for directive, callout_type in directive_map.items():
        pattern = rf"\.\. ({re.escape(directive)})::[ \t]*([\w.]*)\s*\n((?:\n|[ \t]+[^\n]*\n?)+)"
        result = re.sub(pattern, _make_directive_converter(callout_type), result)

    # Convert .. image:: path to ![alt](path)
    result = re.sub(
        r"\.\. image::\s*(.+)",
        r"![\1](\1)",
        result,
    )

    # Convert RST inline code ``code`` to markdown `code`
    result = re.sub(r"``(.+?)``", r"`\1`", result)

    # Convert RST roles :class:`Name` to `Name`
    result = re.sub(r":[\w]+:`([^`]+)`", r"`\1`", result)

    return result
