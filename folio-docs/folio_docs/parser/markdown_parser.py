from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class MarkdownResult:
    content: str
    frontmatter: dict[str, str] = field(default_factory=dict)
    route: str = ""
    source_file: str = ""
    # Hidden from the docs sidebar, published everywhere else. Set from
    # PluginDocument.unlisted; authored docs are always listed.
    unlisted: bool = False


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
# The description falls back to the page's first paragraph, and it ends up in
# <meta name="description">. A comment is written for whoever opens the file
# and a lone component is markup, so neither is a sentence about the page —
# a page opening with either used to describe itself to search engines with
# its own source. With nothing prose-like to use, no description is written
# and the site's own takes over, which is the right answer.
_MDX_COMMENT_RE = re.compile(r"\{/\*.*?\*/\}", re.DOTALL)
_LONE_ELEMENT_RE = re.compile(r"^</?[A-Za-z][^>]*/?>$")


def _extract_first_paragraph(content: str) -> str:
    lines = content.strip().split("\n")
    paragraph: list[str] = []
    past_heading = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            past_heading = True
            continue
        if not stripped or _LONE_ELEMENT_RE.match(stripped):
            if paragraph:
                break
            continue
        if past_heading or not content.strip().startswith("#"):
            paragraph.append(stripped)
    return " ".join(paragraph) if paragraph else ""


def parse_markdown_file(path: Path) -> MarkdownResult:
    raw = path.read_text(encoding="utf-8")
    frontmatter: dict[str, str] = {}
    content = raw
    fm_match = _FRONTMATTER_RE.match(raw)
    if fm_match:
        frontmatter = yaml.safe_load(fm_match.group(1)) or {}
        content = raw[fm_match.end() :]
    if "title" not in frontmatter:
        h1_match = _H1_RE.search(content)
        if h1_match:
            frontmatter["title"] = h1_match.group(1).strip()
    if "description" not in frontmatter:
        desc = _extract_first_paragraph(_MDX_COMMENT_RE.sub("", content))
        desc = _IMAGE_RE.sub("", desc).strip()
        if desc:
            frontmatter["description"] = desc
    return MarkdownResult(
        content=content.strip(),
        frontmatter=frontmatter,
        route=path.stem,
        source_file=str(path),
    )


def source_route(relative: Path) -> str:
    """The route a docs source publishes for a Markdown file at ``relative``.

    One rule, shared with everything that names a published page (the kanban
    plugin resolves ``doc:`` artifacts through it): the ``.md`` suffix comes
    off, and a README is its folder's page.
    """
    parts = list(relative.parts)
    parts[-1] = parts[-1].removesuffix(".md")
    if parts[-1].lower() == "readme":
        parts[-1] = "index"
    return "/".join(parts)


def parse_markdown_directory(
    directory: str, route_prefix: str = ""
) -> list[MarkdownResult]:
    root = Path(directory)
    results: list[MarkdownResult] = []
    rst_files = sorted(root.rglob("*.rst"))
    if rst_files:
        warnings.warn(
            "source.docs supports Markdown build inputs only; "
            "convert .rst files to Markdown before adding them.",
            UserWarning,
            stacklevel=2,
        )
    for md_file in sorted(root.rglob("*.md")):
        result = parse_markdown_file(md_file)
        route = source_route(md_file.relative_to(root))
        if route_prefix:
            route = f"{route_prefix}/{route}"
        result.route = route
        results.append(result)
    return results
