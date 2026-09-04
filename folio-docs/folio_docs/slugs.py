"""Shared URL and identifier slug normalization."""

from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Convert human-readable text to a stable URL-friendly slug."""
    slug = text.lower().strip()
    slug = slug.replace(".", "-")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
