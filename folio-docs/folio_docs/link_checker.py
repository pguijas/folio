"""Build-time link checker for internal documentation links."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

# Matches markdown links: [text](href)
# Captures the href in group 1.
# `(?<!!)` keeps Markdown images out of it. An image is not a navigation
# target: `![board](./board.png)` points at a file that travels with the page,
# and reporting it as a broken route made every documented screenshot look
# like a mistake.
_LINK_RE = re.compile(r"(?<!!)\[(?:[^\]]*)\]\(([^)]+)\)")
_HREF_RE = re.compile(r"""\bhref\s*=\s*(?:"([^"]+)"|'([^']+)')""")
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


@dataclass
class BrokenLink:
    """Represents a broken internal link found during validation."""

    source_page: str  # route of the page containing the link
    target: str  # the href that's broken
    line_number: int  # approximate line in the MDX


def _route_from_mdx_path(mdx_path: Path, content_dir: Path) -> str:
    """Derive the route string from an MDX file path relative to content_dir.

    For example:
        content_dir / "installation.mdx"  -> "installation"
        content_dir / "api-reference/folio/config.mdx"  -> "api-reference/folio/config"
        content_dir / "index.mdx"  -> "index"
    """
    rel = mdx_path.relative_to(content_dir)
    # Drop the .mdx suffix
    return str(rel.with_suffix(""))


def _normalize_target(
    href: str,
    source_route: str,
    docs_route_base: str = "/docs",
) -> str | None:
    """Normalize an internal link target to a route string.

    Returns the normalized route, or None if the link should be skipped
    (external, anchor-only, mailto, tel, etc.).
    """
    # Skip external links
    if href.startswith(("http://", "https://", "mailto:", "tel:")):
        return None

    # Skip anchor-only links
    if href.startswith("#"):
        return None

    # Strip anchor fragments for resolution
    href = href.split("#")[0]

    # Strip query params
    href = href.split("?")[0]

    if not href:
        # Was something like "page#section" -> after stripping anchor, empty
        # means it was anchor-only relative to current page
        return None

    # Remove .mdx or .md extensions if present
    for ext in (".mdx", ".md"):
        if href.endswith(ext):
            href = href[: -len(ext)]

    # Handle absolute paths like /docs/installation
    docs_route_base = docs_route_base.rstrip("/") or "/docs"
    if href == docs_route_base or href.startswith(f"{docs_route_base}/"):
        remainder = href[len(docs_route_base) :]
        remainder = remainder.strip("/")
        return remainder if remainder else "index"

    # Absolute paths outside the docs space (the landing root, registry
    # views like /roadmap) are site routes: keep the leading slash so
    # check_links validates them against site_routes, not page routes.
    if href.startswith("/"):
        return "/" + href.strip("/") if href.strip("/") else "/"

    # Handle relative paths
    # Remove leading ./ if present
    if href.startswith("./"):
        href = href[2:]

    # The source_route includes the page name (e.g., "guide/setup").
    # Relative links resolve from the *directory* of that page.
    source_dir_parts = source_route.split("/")[:-1]

    # If it starts with ../, walk up from the source directory
    if href.startswith("../"):
        href_remaining = href
        dir_parts = list(source_dir_parts)
        while href_remaining.startswith("../"):
            href_remaining = href_remaining[3:]
            if dir_parts:
                dir_parts.pop()
        if dir_parts:
            return (
                "/".join(dir_parts) + "/" + href_remaining
                if href_remaining
                else "/".join(dir_parts)
            )
        return href_remaining if href_remaining else "index"

    # Plain relative path: resolve relative to the directory of the source route
    if source_dir_parts:
        return "/".join(source_dir_parts) + "/" + href
    return href


def _strip_inline_code(line: str) -> str:
    return _INLINE_CODE_RE.sub("", line)


def _links_in_line(line: str) -> list[str]:
    markdown_links = [match.group(1) for match in _LINK_RE.finditer(line)]
    href_links = []
    for match in _HREF_RE.finditer(line):
        href = match.group(1) if match.group(1) is not None else match.group(2)
        if href is not None:
            href_links.append(href)
    return markdown_links + href_links


def _static_target_exists(target: str, static_root: Path | None) -> bool:
    """Return whether a site-absolute URL maps to a published static asset."""
    if static_root is None:
        return False

    root = static_root.resolve()
    candidate = (root / unquote(target).lstrip("/")).resolve()
    if not candidate.is_relative_to(root):
        return False
    return candidate.is_file() or (candidate / "index.html").is_file()


def check_links(
    content_dir: Path,
    pages: list[str],
    docs_route_base: str = "/docs",
    site_routes: set[str] | None = None,
    static_root: Path | None = None,
) -> list[BrokenLink]:
    """Check all MDX files in content_dir for broken internal links.

    Args:
        content_dir: Path to .build/content/
        pages: list of valid routes (e.g., ["index", "installation", "api-reference/folio/config"])
        site_routes: valid site-absolute routes outside the docs space
            (e.g., {"/", "/roadmap"}); the site root is always valid.
        static_root: public directory containing emitted static assets. An
            absolute URL is valid when it resolves to a file under this root.

    Returns:
        A list of BrokenLink instances for every internal link that doesn't
        match a known page route.
    """
    known = set(pages)
    known_site = {"/"} | (site_routes or set())
    broken: list[BrokenLink] = []

    mdx_files = sorted(content_dir.rglob("*.mdx"))

    for mdx_path in mdx_files:
        source_route = _route_from_mdx_path(mdx_path, content_dir)
        text = mdx_path.read_text(encoding="utf-8")

        for line_number, line in enumerate(text.splitlines(), start=1):
            line = _strip_inline_code(line)
            for href in _links_in_line(line):
                normalized = _normalize_target(href, source_route, docs_route_base)
                if normalized is None:
                    continue
                if normalized.startswith("/"):
                    # Site-absolute target (landing root or a registry view).
                    site_target = normalized.rstrip("/") or "/"
                    if site_target in known_site:
                        continue
                    raw_site_target = href.split("#", 1)[0].split("?", 1)[0]
                    if _static_target_exists(
                        site_target, static_root
                    ) or _static_target_exists(raw_site_target, static_root):
                        continue
                    broken.append(
                        BrokenLink(
                            source_page=source_route,
                            target=href,
                            line_number=line_number,
                        )
                    )
                    continue
                # Strip trailing slash
                normalized = normalized.rstrip("/")
                # A directory of pages is addressed by its directory: a link
                # to `plugins/kanban` is the `plugins/kanban/index` page, and
                # writing the `/index` out loud is not what anyone links to.
                if normalized not in known and f"{normalized}/index" not in known:
                    broken.append(
                        BrokenLink(
                            source_page=source_route,
                            target=href,
                            line_number=line_number,
                        )
                    )

    return broken
