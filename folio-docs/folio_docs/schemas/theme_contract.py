"""Canonical theme contract for Folio.

This module defines the single source of truth for theme field names, aliases,
and style properties used throughout Folio's theming system.
"""

from __future__ import annotations

# Canonical theme tune keys extracted from config.py (lines 50-59)
THEME_TUNE_KEYS: set[str] = {
    "fontId",
    "colorId",
    "surfaceColorId",
    "shellPaddingId",
    "contentWidthId",
    "rhythmId",
    "borderId",
    "codeTreatmentId",
}

# User-facing aliases for theme tune keys extracted from config.py (lines 28-49)
THEME_TUNE_ALIASES: dict[str, str] = {
    "accent": "colorId",
    "accent_color": "colorId",
    "border": "borderId",
    "borders": "borderId",
    "code": "codeTreatmentId",
    "code_blocks": "codeTreatmentId",
    "code_treatment": "codeTreatmentId",
    "color": "colorId",
    "color_id": "colorId",
    "content_width": "contentWidthId",
    "font": "fontId",
    "font_id": "fontId",
    "reading": "rhythmId",
    "rhythm": "rhythmId",
    "shell": "shellPaddingId",
    "shell_padding": "shellPaddingId",
    "shell_spacing": "shellPaddingId",
    "surface": "surfaceColorId",
    "surface_color": "surfaceColorId",
    "width": "contentWidthId",
}

# Fixed radius scale shared by config validation, the template workspace, and
# the generated TypeScript contract (themeRadiusScale). theme.radius values
# outside this scale are rejected because the template would silently render
# them as the 0.5rem default.
THEME_RADIUS_OPTIONS: list[str] = ["0", "0.3rem", "0.5rem", "0.75rem", "1rem"]

# Base style properties extracted from template_workspace.py (lines 71-107)
PROJECT_THEME_BASE_STYLE: dict[str, str] = {
    "--folio-heading-font-family": 'var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    "--folio-body-font-family": 'var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    "--folio-code-font-family": 'var(--font-mono), ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
    "--folio-heading-letter-spacing": "0",
    "--folio-heading-weight": "700",
    "--folio-body-line-height": "1.62",
    "--folio-font-size-base": "1rem",
    "--folio-card-shadow": "var(--shadow-sm, none)",
    "--folio-card-border-width": "1px",
    "--folio-card-padding": "1.25rem",
    "--folio-card-hover-shadow": "var(--shadow-md, none)",
    "--folio-card-backdrop": "none",
    "--folio-card-opacity": "1",
    "--folio-code-border-radius": "0.5rem",
    "--folio-code-border": "1px solid var(--border)",
    "--folio-code-bg": "color-mix(in oklch, var(--card) 84%, var(--background))",
    "--folio-code-foreground": "inherit",
    "--folio-code-shadow": "var(--shadow-sm, none)",
    "--folio-h2-border": "1px solid var(--border)",
    "--folio-h2-transform": "none",
    "--folio-h2-letter-spacing": "0",
    "--folio-h2-weight": "700",
    "--folio-h2-padding-left": "0",
    "--folio-h2-border-left": "none",
    "--folio-link-decoration": "none",
    "--folio-section-gap": "2.35rem",
    "--folio-content-max-width": "62rem",
    "--folio-workspace-shell-padding": "0px",
    "--folio-workspace-shell-border": "0 solid transparent",
    "--folio-workspace-shell-shadow": "none",
    "--folio-workspace-shell-background": "var(--background)",
    "--folio-workspace-shell-surface": "transparent",
    "--folio-workspace-shell-topbar": "var(--background)",
    "--folio-workspace-shell-topbar-blur": "none",
    "--folio-workspace-shell-topbar-border": "1px solid var(--border)",
}

# Tune-specific style overrides extracted from template_workspace.py (lines 108-116)
THEME_TUNE_STYLE_OVERRIDES: dict[str, dict[str, str]] = {
    "geist": {
        "--font-sans": "var(--font-geist-sans)",
        "--font-mono": "var(--font-geist-mono)",
        "--folio-heading-font-family": 'var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        "--folio-body-font-family": 'var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        "--folio-code-font-family": 'var(--font-geist-mono), ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
    },
}

# Light mode token names extracted from template_workspace.py (lines 117-155)
_PROJECT_THEME_BASE_LIGHT: dict[str, str] = {
    "--background": "oklch(0.985 0.008 80)",
    "--foreground": "oklch(0.175 0.008 75)",
    "--card": "oklch(0.995 0.004 80)",
    "--card-foreground": "oklch(0.175 0.008 75)",
    "--popover": "oklch(0.995 0.004 80)",
    "--popover-foreground": "oklch(0.175 0.008 75)",
    "--primary": "oklch(0.490 0.130 285)",
    "--primary-foreground": "oklch(0.985 0.008 285)",
    "--secondary": "oklch(0.945 0.012 285)",
    "--secondary-foreground": "oklch(0.250 0.020 285)",
    "--muted": "oklch(0.955 0.008 80)",
    "--muted-foreground": "oklch(0.510 0.012 75)",
    "--accent": "oklch(0.490 0.130 285)",
    "--accent-foreground": "oklch(0.985 0.008 285)",
    "--destructive": "oklch(0.570 0.180 25)",
    "--border": "oklch(0.900 0.008 80)",
    "--input": "oklch(0.880 0.010 80)",
    "--ring": "oklch(0.650 0.040 285)",
    "--chart-1": "oklch(0.680 0.120 285)",
    "--chart-2": "oklch(0.680 0.110 200)",
    "--chart-3": "oklch(0.680 0.110 145)",
    "--chart-4": "oklch(0.700 0.110 70)",
    "--chart-5": "oklch(0.680 0.110 340)",
    "--chart-6": "oklch(0.680 0.110 240)",
    "--chart-7": "oklch(0.700 0.100 110)",
    "--chart-8": "oklch(0.680 0.110 315)",
    "--status-running": "oklch(0.680 0.110 160)",
    "--status-completed": "oklch(0.620 0.100 250)",
    "--status-warning": "oklch(0.750 0.120 70)",
    "--sidebar": "oklch(0.975 0.010 80)",
    "--sidebar-foreground": "oklch(0.175 0.008 75)",
    "--sidebar-primary": "oklch(0.490 0.130 285)",
    "--sidebar-primary-foreground": "oklch(0.985 0.008 285)",
    "--sidebar-accent": "oklch(0.945 0.012 285)",
    "--sidebar-accent-foreground": "oklch(0.250 0.020 285)",
    "--sidebar-border": "oklch(0.910 0.008 80)",
    "--sidebar-ring": "oklch(0.650 0.040 285)",
}

# Dark mode token names extracted from template_workspace.py (lines 156-194)
_PROJECT_THEME_BASE_DARK: dict[str, str] = {
    "--background": "oklch(0.155 0.010 75)",
    "--foreground": "oklch(0.950 0.008 80)",
    "--card": "oklch(0.195 0.010 75)",
    "--card-foreground": "oklch(0.950 0.008 80)",
    "--popover": "oklch(0.195 0.010 75)",
    "--popover-foreground": "oklch(0.950 0.008 80)",
    "--primary": "oklch(0.720 0.100 285)",
    "--primary-foreground": "oklch(0.155 0.010 75)",
    "--secondary": "oklch(0.250 0.015 285)",
    "--secondary-foreground": "oklch(0.920 0.008 80)",
    "--muted": "oklch(0.235 0.010 75)",
    "--muted-foreground": "oklch(0.650 0.012 80)",
    "--accent": "oklch(0.720 0.100 285)",
    "--accent-foreground": "oklch(0.155 0.010 75)",
    "--destructive": "oklch(0.680 0.160 25)",
    "--border": "oklch(1 0.005 80 / 10%)",
    "--input": "oklch(1 0.005 80 / 14%)",
    "--ring": "oklch(0.600 0.050 285)",
    "--chart-1": "oklch(0.720 0.100 285)",
    "--chart-2": "oklch(0.720 0.100 200)",
    "--chart-3": "oklch(0.720 0.100 145)",
    "--chart-4": "oklch(0.740 0.100 70)",
    "--chart-5": "oklch(0.720 0.100 340)",
    "--chart-6": "oklch(0.720 0.100 240)",
    "--chart-7": "oklch(0.740 0.090 110)",
    "--chart-8": "oklch(0.720 0.100 315)",
    "--status-running": "oklch(0.720 0.100 160)",
    "--status-completed": "oklch(0.680 0.090 250)",
    "--status-warning": "oklch(0.780 0.110 70)",
    "--sidebar": "oklch(0.145 0.012 75)",
    "--sidebar-foreground": "oklch(0.950 0.008 80)",
    "--sidebar-primary": "oklch(0.720 0.100 285)",
    "--sidebar-primary-foreground": "oklch(0.155 0.010 75)",
    "--sidebar-accent": "oklch(0.220 0.015 285)",
    "--sidebar-accent-foreground": "oklch(0.950 0.008 80)",
    "--sidebar-border": "oklch(1 0.005 80 / 8%)",
    "--sidebar-ring": "oklch(0.600 0.050 285)",
}

# Combined list of all style property names (for validation)
THEME_STYLE_PROPERTIES: list[str] = list(PROJECT_THEME_BASE_STYLE.keys())
