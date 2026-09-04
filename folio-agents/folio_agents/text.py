"""Small text and link primitives owned by Folio for Agents."""

from __future__ import annotations

import re
from typing import Any

_HREF_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_SAFE_HREF_SCHEME_RE = re.compile(r"^(?:https?|mailto):", re.IGNORECASE)
_UNSAFE_TEXT_RE = re.compile(r"[<>\n\r]")


def slugify(text: str) -> str:
    """Convert human-readable text to a stable file-safe identifier."""
    slug = text.lower().strip().replace(".", "-")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-")


def safe_href(raw_value: Any, path: str) -> str:
    """Accept web URLs and relative paths while rejecting executable schemes."""
    if raw_value in (None, ""):
        return ""
    if not isinstance(raw_value, str):
        raise ValueError(f"{path} must be a string")
    value = raw_value.strip()
    if _UNSAFE_TEXT_RE.search(value):
        raise ValueError(f"{path} contains unsafe text")
    if _HREF_SCHEME_RE.match(value) and not _SAFE_HREF_SCHEME_RE.match(value):
        raise ValueError(f"{path} must be an http(s) URL or a relative path")
    return value
