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


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


def _extract_first_paragraph(content: str) -> str:
    lines = content.strip().split("\n")
    paragraph: list[str] = []
    past_heading = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            past_heading = True
            continue
        if not stripped:
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
        desc = _extract_first_paragraph(content)
        desc = _IMAGE_RE.sub("", desc).strip()
        if desc:
            frontmatter["description"] = desc
    return MarkdownResult(
        content=content.strip(),
        frontmatter=frontmatter,
        route=path.stem,
        source_file=str(path),
    )


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
        rel = md_file.relative_to(root)
        parts = list(rel.parts)
        parts[-1] = parts[-1].removesuffix(".md")
        if parts[-1].lower() == "readme":
            parts[-1] = "index"
        route = "/".join(parts)
        if route_prefix:
            route = f"{route_prefix}/{route}"
        result.route = route
        results.append(result)
    return results
