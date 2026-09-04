"""Generate TypeScript type definitions from Python theme contract.

This module provides code generation for TypeScript theme types that are
consumed by template/theme/preset-types.ts and written into build workspaces.
"""

from __future__ import annotations

import json

from folio_docs.schemas.theme_contract import (
    THEME_RADIUS_OPTIONS,
    THEME_STYLE_PROPERTIES,
    THEME_TUNE_KEYS,
)


def generate_typescript_contract() -> str:
    """Generate TypeScript type definitions from the Python theme contract.

    Returns:
        TypeScript source code defining ThemeStyle, ThemeTuneKey, ThemeVars,
        and themeRadiusScale.
    """
    lines = [
        "// GENERATED FILE - DO NOT EDIT",
        "// Source: folio/schemas/theme_contract.py",
        "",
        "export interface ThemeStyle {",
    ]

    # Generate ThemeStyle interface with all style properties
    for prop in THEME_STYLE_PROPERTIES:
        lines.append(f'  "{prop}"?: string')

    lines.append("}")
    lines.append("")

    # Generate ThemeTuneKey union type
    lines.append("export type ThemeTuneKey =")
    for key in sorted(THEME_TUNE_KEYS):
        lines.append(f'  | "{key}"')
    lines.append("")

    # Generate ThemeVars type
    lines.append("export type ThemeVars = Record<string, string>")
    lines.append("")

    # Generate the fixed radius scale shared with config validation
    radius_values = ", ".join(json.dumps(value) for value in THEME_RADIUS_OPTIONS)
    lines.append(f"export const themeRadiusScale = [{radius_values}] as const")
    lines.append("")

    return "\n".join(lines)
