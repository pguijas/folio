from __future__ import annotations

import html
import json
import logging
import os
import re
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from folio_docs.config import Config, normalize_base_path
from folio_docs.features import is_feature_enabled
from folio_docs.agent_output.contract import (
    FOLIO_MDX_CONTRACT_VERSION,
    render_mdx_contract_module,
)
from folio_docs.docs.theme_package_validator import validate_and_raise
from folio_docs.schemas.theme_contract import (
    PROJECT_THEME_BASE_STYLE as _PROJECT_THEME_BASE_STYLE,
    THEME_RADIUS_OPTIONS as _THEME_RADIUS_OPTIONS,
    THEME_STYLE_PROPERTIES as _THEME_STYLE_PROPERTIES,
    THEME_TUNE_STYLE_OVERRIDES as _PROJECT_THEME_TUNE_STYLE,
    _PROJECT_THEME_BASE_LIGHT,
    _PROJECT_THEME_BASE_DARK,
)

# Map legacy (pre-`--folio-*`) Folio style-property names onto their namespaced
# equivalents so user-supplied `theme_style` overrides keyed by the old names
# keep working after the WP3 namespacing rename.
_LEGACY_STYLE_KEY_ALIASES: dict[str, str] = {
    f"--{name[len('--folio-') :]}": name
    for name in _THEME_STYLE_PROPERTIES
    if name.startswith("--folio-")
}


def _namespace_style_key(key: str) -> str:
    return _LEGACY_STYLE_KEY_ALIASES.get(key, key)


_REPO_IMPORTS_BLOCK_RE = re.compile(
    r"(?ms)^[ \t]*// __PROJECT_REPO_IMPORTS_START__\n"
    r".*?"
    r"^[ \t]*// __PROJECT_REPO_IMPORTS_END__\n?"
)
_REPO_LINK_BLOCK_RE = re.compile(
    r"(?ms)^[ \t]*\{/\* __PROJECT_REPO_LINK_START__ \*/\}\n"
    r".*?"
    r"^[ \t]*\{/\* __PROJECT_REPO_LINK_END__ \*/\}\n?"
)
_REPO_MARKER_LINE_RE = re.compile(
    r"(?m)^[ \t]*(?:// __PROJECT_REPO_IMPORTS_(?:START|END)__|"
    r"\{/\* __PROJECT_REPO_LINK_(?:START|END)__ \*/\})\n?"
)
_HEADER_LOGO_BLOCK_RE = re.compile(
    r"(?ms)([ \t]*)\{/\* __PROJECT_HEADER_LOGO_START__ \*/\}\n"
    r".*?"
    r"^[ \t]*\{/\* __PROJECT_HEADER_LOGO_END__ \*/\}"
)
_HEADER_LOGO_MARKER_LINE_RE = re.compile(
    r"(?m)^[ \t]*\{/\* __PROJECT_HEADER_LOGO_(?:START|END)__ \*/\}\n?"
)
_HEADER_ACTION_IMPORT_BLOCK_RE = re.compile(
    r"(?ms)([ \t]*)// __PROJECT_HEADER_ACTION_IMPORTS_START__\n"
    r".*?"
    r"^[ \t]*// __PROJECT_HEADER_ACTION_IMPORTS_END__"
)
_HEADER_ACTION_IMPORT_MARKER_LINE_RE = re.compile(
    r"(?m)^[ \t]*// __PROJECT_HEADER_ACTION_IMPORTS_(?:START|END)__\n?"
)
_HEADER_ACTION_BLOCK_RE = re.compile(
    r"(?ms)([ \t]*)\{/\* __PROJECT_HEADER_ACTIONS_START__ \*/\}\n"
    r".*?"
    r"^[ \t]*\{/\* __PROJECT_HEADER_ACTIONS_END__ \*/\}"
)
_HEADER_ACTION_MARKER_LINE_RE = re.compile(
    r"(?m)^[ \t]*\{/\* __PROJECT_HEADER_ACTIONS_(?:START|END)__ \*/\}\n?"
)
_BUILTIN_THEME_PRESETS = {
    "aperture",
    "atlas",
    "beacon",
    "canopy",
    "carbon",
    "draftline",
    "ledger",
    "organic-editorial",
    "proof",
    "stacks",
    "workshop",
}

logger = logging.getLogger("folio_docs.template")

# Load-bearing injection markers: the marker string that MUST appear verbatim in
# the file it belongs to, keyed by the file's path (relative to the template
# root). The injector consumes each of these unconditionally for every build, so
# a missing marker silently drops required project metadata. Optional markers
# with documented fallbacks (e.g. the repo/header paired blocks that are stripped
# when the feature is off, the `mdx-components.tsx` component markers that fall
# back to a `...components,` spread, or markers that only live in optional files
# such as the landing page and theme configurator) are intentionally excluded —
# only failures that always break a build are listed here.
REQUIRED_INJECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "app/layout.tsx": (
        "__PROJECT_NAME__",
        "__PROJECT_DESCRIPTION__",
        "__SITE_URL__",
    ),
    "app/docs/layout.tsx": ("__PROJECT_NAME__",),
    "app/docs/[[...mdxPath]]/page.jsx": (
        "__PROJECT_NAME__",
        "__PROJECT_DESCRIPTION__",
        "__SITE_URL__",
        "__DOCS_INDEX_CANONICAL_PATH__",
    ),
    "next.config.mjs": ("const configuredBasePath = '' // __FOLIO_BASE_PATH__",),
}


def validate_template_marker_contract(
    template_dir: str | Path,
) -> list[tuple[str, str]]:
    """Return ``(file, marker)`` pairs whose required marker is missing.

    Each load-bearing marker in :data:`REQUIRED_INJECTION_MARKERS` must be
    present verbatim in its expected file. A missing file surfaces every marker
    it owns as missing, mirroring the "missing required files" / MDX-contract
    checks so a custom template fails fast instead of building with silently
    dropped project metadata.
    """
    root = Path(template_dir)
    missing: list[tuple[str, str]] = []
    for rel_path, markers in REQUIRED_INJECTION_MARKERS.items():
        file_path = root / rel_path
        if not file_path.exists():
            missing.extend((rel_path, marker) for marker in markers)
            continue
        content = file_path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                missing.append((rel_path, marker))
    return missing


class TemplateWorkspace:
    def __init__(
        self,
        template_dir: str | Path,
        build_dir: str | Path,
        content_dir: str | Path | None = None,
    ) -> None:
        self.template_dir = Path(template_dir)
        self.build_dir = Path(build_dir)
        self.content_dir = (
            Path(content_dir) if content_dir is not None else self.build_dir / "content"
        )

    def prepare(self, clean: bool = False) -> None:
        if clean and self.build_dir.exists():
            shutil.rmtree(self.build_dir)

        ignore = copytree_ignore()

        _reject_symlinks(self.template_dir, "template.path")

        if not self.build_dir.exists():
            shutil.copytree(self.template_dir, self.build_dir, ignore=ignore)
        else:
            if clean and self.content_dir.exists():
                shutil.rmtree(self.content_dir)
            shutil.copytree(
                self.template_dir, self.build_dir, ignore=ignore, dirs_exist_ok=True
            )

        self._remove_template_content()
        self.content_dir.mkdir(exist_ok=True)

    def _remove_template_content(self) -> None:
        template_content = self.template_dir / "content"
        if not template_content.exists() or not self.content_dir.exists():
            return

        template_paths = sorted(
            template_content.rglob("*"),
            key=lambda path: len(path.relative_to(template_content).parts),
            reverse=True,
        )
        for source_path in template_paths:
            target_path = self.content_dir / source_path.relative_to(template_content)
            if source_path.is_file() or source_path.is_symlink():
                if target_path.is_file() or target_path.is_symlink():
                    target_path.unlink()
            elif source_path.is_dir() and target_path.is_dir():
                try:
                    target_path.rmdir()
                except OSError:
                    pass


# Directories excluded from every template/theme/overlay copytree; their
# contents are never published, so symlinks within them are harmless. All
# ``shutil.ignore_patterns`` calls derive from this set (via
# :func:`copytree_ignore`) so the symlink scan and the copy always agree on
# which subtrees are skipped.
_COPY_IGNORED_DIRS = frozenset(
    {"node_modules", ".next", "__pycache__", ".git", "content"}
)

# Marker file written into staging directories that Folio creates and may
# delete on the next build (see folio_docs.build._materialize_overlay_template).
# It is excluded from every copy so it never propagates into .build/.
FOLIO_STAGING_MARKER = ".folio-staging"


def copytree_ignore():
    """Ignore callable for every template/theme/overlay ``copytree`` call.

    Single-sourced from :data:`_COPY_IGNORED_DIRS` (plus the staging marker
    file) so the symlink scan and the copy can never drift apart.
    """
    return shutil.ignore_patterns(*sorted(_COPY_IGNORED_DIRS), FOLIO_STAGING_MARKER)


def _walk_copied_entries(root: Path):
    """Yield every path under ``root`` that a Folio copytree would copy.

    Uses ``os.walk`` and prunes :data:`_COPY_IGNORED_DIRS` in place so large
    excluded trees (``node_modules``, ``.git``, ...) are never descended into.
    Directories are yielded before their contents.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in _COPY_IGNORED_DIRS]
        base = Path(dirpath)
        for name in dirnames:
            yield base / name
        for name in filenames:
            yield base / name


def _reject_symlinks(root: Path, label: str) -> None:
    """Raise if any copied entry under ``root`` is a symlink.

    ``shutil.copytree`` dereferences symlinks (``symlinks=False``), so an
    untrusted tree containing a symlink could copy files from outside the tree
    into the published site. Scan the tree and refuse to copy if any symlink is
    present. Entries inside directories excluded from the copy are skipped, since
    they are never published.
    """
    for entry in _walk_copied_entries(root):
        if entry.is_symlink():
            raise ValueError(
                f"{label} must not contain symlinks: {entry.relative_to(root)}"
            )


def collect_copyable_files(root: Path, label: str) -> set[Path]:
    """Collect copied file paths (relative to ``root``) in a single traversal.

    Combines the symlink rejection of :func:`_reject_symlinks` with file
    collection so callers that need both (e.g. the theme.package overlay) walk
    the tree once instead of twice. Raises ``ValueError`` on the first symlink.
    """
    files: set[Path] = set()
    for entry in _walk_copied_entries(root):
        if entry.is_symlink():
            raise ValueError(
                f"{label} must not contain symlinks: {entry.relative_to(root)}"
            )
        if entry.is_file():
            files.add(entry.relative_to(root))
    return files


# Defensive default when a radius value is not on the shared scale. Config
# validation (folio_docs.config._theme_radius) rejects unknown theme.radius values,
# so this is unreachable through normal config loading; it only guards direct
# Config construction with an off-scale value.
_DEFAULT_THEME_RADIUS = "0.5rem"


def _theme_radius_index(radius: str) -> int:
    try:
        return _THEME_RADIUS_OPTIONS.index(radius)
    except ValueError:
        logger.warning(
            "theme radius %r is not on the shared radius scale; falling back to %s",
            radius,
            _DEFAULT_THEME_RADIUS,
        )
        return _THEME_RADIUS_OPTIONS.index(_DEFAULT_THEME_RADIUS)


def _has_project_theme_preset(config: Config) -> bool:
    if config.theme_preset in _BUILTIN_THEME_PRESETS:
        return bool(
            config.theme_name
            or config.theme_description
            or config.theme_scene
            or config.theme_preview
            or config.theme_tokens
            or config.theme_style
            or config.theme_variants
        )
    return bool(
        config.theme_name
        or config.theme_description
        or config.theme_scene
        or config.theme_preview
        or config.theme_tokens
        or config.theme_style
        or config.theme_variants
        or config.theme_radius
    )


def _project_theme_default_config(config: Config) -> dict[str, object]:
    default_config: dict[str, object] = {"presetId": config.theme_preset}
    if config.theme_radius:
        default_config["radiusIndex"] = _theme_radius_index(config.theme_radius)
    if config.theme_tune:
        default_config["customization"] = dict(config.theme_tune)
    if _has_project_theme_preset(config):
        default_config["optionsByPreset"] = {
            config.theme_preset: _project_theme_default_options(config)
        }
    return default_config


def _project_theme_default_options(config: Config) -> dict[str, str]:
    return {
        control_id: str(control["default"])
        for control_id, control in config.theme_variants.items()
    }


def _project_theme_controls(config: Config) -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []
    for control_id, control in config.theme_variants.items():
        controls.append(
            {
                "id": control_id,
                "label": control["label"],
                "description": control["description"],
                "options": [
                    {
                        "label": option["label"],
                        "value": option_id,
                        **(
                            {"swatch": option["swatch"]} if option.get("swatch") else {}
                        ),
                        **(
                            {"description": option["description"]}
                            if option["description"]
                            else {}
                        ),
                    }
                    for option_id, option in control["options"].items()
                ],
            }
        )
    return controls


def _project_theme_variant_themes(config: Config) -> dict[str, dict[str, object]]:
    variant_themes: dict[str, dict[str, object]] = {}
    for control_id, control in config.theme_variants.items():
        variant_themes[control_id] = {}
        for option_id, option in control["options"].items():
            option_theme: dict[str, object] = {}
            preview = _project_theme_option_preview(option)
            if "light" in preview and "dark" in preview:
                option_theme["preview"] = preview
            if option["style"]:
                # Apply the same legacy-key aliasing as top-level theme.style so
                # documented keys like --content-max-width work inside variants.
                option_theme["style"] = {
                    _namespace_style_key(key): value
                    for key, value in option["style"].items()
                }
            light_tokens = option["tokens"].get("light", {})
            dark_tokens = option["tokens"].get("dark", {})
            if light_tokens:
                option_theme["light"] = light_tokens
            if dark_tokens:
                option_theme["dark"] = dark_tokens
            variant_themes[control_id][option_id] = option_theme
    return variant_themes


def _project_theme_option_preview(option: dict[str, Any]) -> dict[str, str]:
    preview = dict(option["preview"])
    swatch = option.get("swatch", "")
    if swatch:
        preview.setdefault("light", swatch)
        preview.setdefault("dark", swatch)
    return preview


def _project_theme_style(config: Config) -> dict[str, str]:
    tuned_style: dict[str, str] = {}
    font_style = _PROJECT_THEME_TUNE_STYLE.get(config.theme_tune.get("fontId", ""))
    if font_style:
        tuned_style.update(font_style)
    for key, value in config.theme_style.items():
        tuned_style[_namespace_style_key(key)] = value
    return tuned_style


def _render_project_header_logo(config: Config, fallback_name: str) -> str:
    if not config.theme_header:
        return ""

    brand = config.theme_header.get("brand") or fallback_name
    badge = config.theme_header.get("badge", "")
    lines = [
        f'<span className="text-sm font-semibold tracking-tight">{{{json.dumps(brand)}}}</span>'
    ]
    if badge:
        lines.append(
            '<span className="rounded-full bg-primary/10 px-2 py-0.5 '
            'text-[10px] font-medium text-primary">'
            f"{{{json.dumps(badge)}}}</span>"
        )
    return "\n".join(lines)


def _has_project_header_actions(config: Config) -> bool:
    return any(
        key in config.theme_header
        for key in ("repo", "theme_toggle", "action_label", "action_href", "search")
    )


def _render_project_header_actions(config: Config) -> str:
    if not _has_project_header_actions(config):
        return ""

    repo_href = config.theme_header.get("repo") or config.project_repo
    theme_toggle = bool(config.theme_header.get("theme_toggle"))
    action_href = config.theme_header.get("action_href", "")
    action_label = config.theme_header.get("action_label", "")
    props: list[str] = []
    if repo_href:
        props.append(f"repoHref={{{json.dumps(repo_href)}}}")
    if theme_toggle:
        props.append("themeToggle")
    if action_href and action_label:
        props.append(f"actionHref={{{json.dumps(action_href)}}}")
        props.append(f"actionLabel={{{json.dumps(action_label)}}}")

    prop_lines = "\n".join(f"  {prop}" for prop in props)
    if prop_lines:
        return f"<ProjectHeaderActions\n{prop_lines}\n/>\n<VersionSelector />"
    return "<VersionSelector />"


def _render_project_theme_module(config: Config) -> str:
    default_config = _project_theme_default_config(config)
    has_project_preset = _has_project_theme_preset(config)
    lines = [
        'import type { ThemePreset, ThemeStyle, ThemeVars } from "./preset-types"',
        "",
    ]

    if has_project_preset:
        light_tokens = config.theme_tokens.get("light", {})
        dark_tokens = config.theme_tokens.get("dark", {})
        preview = {
            "light": config.theme_preview.get(
                "light",
                light_tokens.get(
                    "--primary",
                    _PROJECT_THEME_BASE_LIGHT["--primary"],
                ),
            ),
            "dark": config.theme_preview.get(
                "dark",
                dark_tokens.get(
                    "--primary",
                    _PROJECT_THEME_BASE_DARK["--primary"],
                ),
            ),
        }
        radius = (
            config.theme_radius
            or _THEME_RADIUS_OPTIONS[int(default_config.get("radiusIndex", 2))]
        )
        default_options = _project_theme_default_options(config)
        preset = {
            "id": config.theme_preset,
            "name": config.theme_name or config.project_name,
            "description": config.theme_description
            or f"{config.project_name} project theme",
            "scene": config.theme_scene
            or f"{config.project_name} documentation uses a project-owned visual system.",
            "preview": preview,
            "defaultOptions": default_options,
            "defaultRadiusIndex": _theme_radius_index(radius),
            "defaultCustomization": config.theme_tune,
            "controls": _project_theme_controls(config),
        }
        lines.extend(
            [
                "const projectBaseStyle: ThemeStyle = "
                f"{json.dumps(_PROJECT_THEME_BASE_STYLE, indent=2)}",
                "",
                "const projectBaseLight: ThemeVars = "
                f"{json.dumps(_PROJECT_THEME_BASE_LIGHT, indent=2)}",
                "",
                "const projectBaseDark: ThemeVars = "
                f"{json.dumps(_PROJECT_THEME_BASE_DARK, indent=2)}",
                "",
                "const projectStyleOverrides: Record<string, string> = "
                f"{json.dumps(_project_theme_style(config), indent=2)}",
                "",
                "const projectLightOverrides: ThemeVars = "
                f"{json.dumps(light_tokens, indent=2)}",
                "",
                "const projectDarkOverrides: ThemeVars = "
                f"{json.dumps(dark_tokens, indent=2)}",
                "",
                "const projectVariantThemes: Record<string, Record<string, {",
                "  preview?: { light: string; dark: string }",
                "  style?: Record<string, string>",
                "  light?: ThemeVars",
                "  dark?: ThemeVars",
                f"}}>> = {json.dumps(_project_theme_variant_themes(config), indent=2)}",
                "",
                'const projectPresetConfig: Omit<ThemePreset, "resolve"> = '
                f"{json.dumps(preset, indent=2)}",
                "",
                "const projectResolvedTheme = {",
                f"  preview: {json.dumps(preview)},",
                f"  radius: {json.dumps(radius)},",
                "  style: { ...projectBaseStyle, ...projectStyleOverrides },",
                "  light: { ...projectBaseLight, ...projectLightOverrides },",
                "  dark: { ...projectBaseDark, ...projectDarkOverrides },",
                "}",
                "",
                "function resolveProjectTheme(options: Record<string, string>) {",
                "  let preview = projectResolvedTheme.preview",
                "  let style = projectResolvedTheme.style",
                "  let light = projectResolvedTheme.light",
                "  let dark = projectResolvedTheme.dark",
                "",
                "  for (const control of projectPresetConfig.controls) {",
                "    const selectedValue = options[control.id] ?? projectPresetConfig.defaultOptions[control.id]",
                "    const variant = projectVariantThemes[control.id]?.[selectedValue]",
                "    if (!variant) continue",
                "    preview = variant.preview ?? preview",
                "    style = { ...style, ...(variant.style ?? {}) }",
                "    light = { ...light, ...(variant.light ?? {}) }",
                "    dark = { ...dark, ...(variant.dark ?? {}) }",
                "  }",
                "",
                "  return { preview, radius: projectResolvedTheme.radius, style, light, dark }",
                "}",
                "",
                "export const projectThemePreset: ThemePreset | null = {",
                "  ...projectPresetConfig,",
                "  resolve(options) {",
                "    return resolveProjectTheme(options)",
                "  },",
                "}",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "export const projectThemePreset: ThemePreset | null = null",
                "",
            ]
        )

    lines.extend(
        [
            "export const projectThemeDefaultConfig: {",
            "  presetId?: string",
            "  radiusIndex?: number",
            "  optionsByPreset?: Record<string, Record<string, string>>",
            "  customization?: Record<string, string>",
            f"}} = {json.dumps(default_config, indent=2)}",
            "",
        ]
    )
    return "\n".join(lines)


class TemplateConfigInjector:
    def __init__(self, config: Config, build_dir: str | Path) -> None:
        self.config = config
        self.build_dir = Path(build_dir)
        self._theme_package_files: set[Path] = set()
        self._injected_files: set[str] = set()

    def _record_injected(self, path: Path) -> None:
        """Track a build file the injector actually wrote to, for the summary."""
        try:
            rel = path.resolve().relative_to(self.build_dir.resolve())
        except ValueError:
            rel = path
        self._injected_files.add(rel.as_posix())

    def _note_skip(self, target: str, reason: str) -> None:
        """Log that an optional injection target was skipped.

        Required markers/files are pre-validated in
        :func:`folio_docs.build._resolve_template_dir`, so reaching a skip here always
        concerns a genuinely optional target (an absent optional file, or a
        feature that is not configured). Surface it at debug level instead of
        silently no-op'ing.
        """
        logger.debug("template injection skipped %s: %s", target, reason)

    def _plugin_view_owns_root(self) -> bool:
        """Check if a plugin view owns the root route (/).

        Plugin sections conventionally expose public views through
        ``routes.public``. Inspect every normalized plugin section instead of
        naming a product-specific key, so optional integrations remain outside
        the Docs runtime boundary.

        When a plugin view owns `/`, the injector skips the docs-index wrapper at
        `app/page.tsx`, sets the docs canonical path to "/docs/", and includes
        the docs index in the sitemap (no duplicate roots).
        """
        for section in self.config.extra.values():
            if not isinstance(section, dict):
                continue
            routes = section.get("routes")
            if not isinstance(routes, dict):
                continue
            public_route = routes.get("public")
            if not isinstance(public_route, str):
                continue
            stripped = public_route.strip()
            if stripped and "/" + stripped.strip("/") == "/":
                return True
        return False

    def inject(self) -> None:
        name = self.config.project_name

        self._apply_theme_package()
        self._inject_root_layout(name)
        self._inject_docs_layout(name)
        self._inject_docs_route_page(name)
        self._inject_og_image(name)
        self._inject_landing_page(name)
        self._inject_previews_page(name)
        self._inject_sitemap()
        self._inject_search_postbuild()
        self._inject_theme_config()
        self._inject_i18n()
        self._inject_versions()
        self._write_template_context()
        self._relocate_docs_route()

        if self._injected_files:
            logger.info(
                "template injection applied to %d file(s): %s",
                len(self._injected_files),
                ", ".join(sorted(self._injected_files)),
            )
        else:
            logger.info("template injection applied to no files")

    def _docs_route_base(self) -> str:
        return self.config.docs_route_base.rstrip("/") or "/docs"

    def _docs_route_with_trailing_slash(self) -> str:
        return f"{self._docs_route_base()}/"

    def _docs_route_path(self, suffix: str) -> str:
        suffix = suffix.strip("/")
        if not suffix:
            return self._docs_route_with_trailing_slash()
        return f"{self._docs_route_base()}/{suffix}"

    def _docs_route_segments(self) -> list[str]:
        return [part for part in self._docs_route_base().strip("/").split("/") if part]

    def _docs_app_import_path(self) -> str:
        return "./" + "/".join(self._docs_route_segments())

    def _apply_theme_package(self) -> None:
        if not self.config.theme_package_path:
            return

        package_path = Path(self.config.theme_package_path)
        if not package_path.exists():
            raise FileNotFoundError(f"Theme package not found: {package_path}")
        if not package_path.is_dir():
            raise ValueError(f"Theme package must be a directory: {package_path}")

        # Defense-in-depth: theme.package containment is enforced in
        # Config.resolve_paths, but re-verify here right before we copy in case
        # the resolved path was set through another code path.
        resolved_package = package_path.resolve()
        build_root = self.build_dir.resolve()
        if resolved_package == build_root or resolved_package.is_relative_to(
            build_root
        ):
            raise ValueError("theme.package cannot point inside the build directory")

        # Single traversal: reject symlinks (shutil.copytree dereferences them,
        # so an untrusted package could otherwise pull outside files into the
        # published site) and collect the package-owned files in one walk.
        self._theme_package_files = collect_copyable_files(
            package_path, "theme.package"
        )

        validate_and_raise(package_path)

        shutil.copytree(
            package_path,
            self.build_dir,
            ignore=copytree_ignore(),
            dirs_exist_ok=True,
        )

    def _inject_root_layout(self, name: str) -> None:
        layout_path = self.build_dir / "app" / "layout.tsx"
        if not layout_path.exists():
            self._note_skip("app/layout.tsx", "file not present")
            return
        content = layout_path.read_text(encoding="utf-8")

        description = f"Documentation for {name}"
        content = content.replace("__PROJECT_NAME__", name)
        content = content.replace("__PROJECT_DESCRIPTION__", description)
        site_url = self.config.site_url.rstrip("/") if self.config.site_url else ""
        if site_url and "metadataBase:" not in content:
            content = content.replace(
                "export const metadata = {\n",
                (
                    "export const metadata = {\n"
                    f"  metadataBase: new URL({json.dumps(site_url)}),\n"
                ),
                1,
            )
        content = content.replace("__SITE_URL__", site_url)

        self._inject_favicon(name)

        layout_path.write_text(content, encoding="utf-8")
        self._record_injected(layout_path)

    def _inject_favicon(self, name: str) -> None:
        default_icon = self.build_dir / "app" / "icon.svg"

        if self.config.favicon:
            favicon_src = Path(self.config.favicon)
            if favicon_src.exists():
                ext = favicon_src.suffix or ".svg"
                favicon_dest = self.build_dir / "app" / f"icon{ext}"
                shutil.copy2(favicon_src, favicon_dest)
                if ext != ".svg" and default_icon.exists():
                    # Drop the template default so the stale monogram icon
                    # does not ship alongside the configured favicon.
                    default_icon.unlink()
                return

        if default_icon.exists():
            monogram = name[:2].lower()
            content = default_icon.read_text(encoding="utf-8")
            default_icon.write_text(
                content.replace("__PROJECT_MONOGRAM__", monogram),
                encoding="utf-8",
            )

    def _write_template_context(self) -> None:
        context = {
            "project": {
                "name": self.config.project_name,
                "version": self.config.project_version,
                "repo": self.config.project_repo,
                "repoRef": self.config.project_repo_ref,
                "url": self.config.site_url,
            },
            "docs": {
                "routeBase": self._docs_route_base(),
                "mdxContractVersion": FOLIO_MDX_CONTRACT_VERSION,
            },
            "template": {
                "params": self.config.template_params,
                "docsRouteBase": self._docs_route_base(),
                "mdxContractVersion": FOLIO_MDX_CONTRACT_VERSION,
            },
        }
        lib_dir = self.build_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        content = (
            "export const folioProject = "
            f"{json.dumps(context['project'], indent=2)} as const\n\n"
            "export const folioTemplateParams = "
            f"{json.dumps(context['template']['params'], indent=2)} as const\n\n"
            "export const folioDocs = "
            f"{json.dumps(context['docs'], indent=2)} as const\n\n"
            "export const folioTemplateContext = "
            f"{json.dumps(context, indent=2)} as const\n"
        )
        (lib_dir / "folio-template.ts").write_text(content, encoding="utf-8")
        (lib_dir / "folio-mdx-contract.ts").write_text(
            render_mdx_contract_module(),
            encoding="utf-8",
        )
        self._record_injected(lib_dir / "folio-template.ts")
        self._record_injected(lib_dir / "folio-mdx-contract.ts")

    def _inject_docs_layout(self, name: str) -> None:
        layout_path = self.build_dir / "app" / "docs" / "layout.tsx"
        if not layout_path.exists():
            self._note_skip("app/docs/layout.tsx", "file not present")
            return
        content = layout_path.read_text(encoding="utf-8")

        monogram = name[:2].lower()
        content = content.replace("__PROJECT_NAME__", name)
        content = content.replace("__PROJECT_MONOGRAM__", monogram)
        content = self._inject_project_header_logo(content, name)
        content = self._inject_project_header_actions(content)
        content = content.replace(
            'url: "/docs/opengraph-image"',
            f"url: {json.dumps(self._docs_route_path('opengraph-image'))}",
        )
        content = content.replace(
            'images: ["/docs/opengraph-image"]',
            f"images: [{json.dumps(self._docs_route_path('opengraph-image'))}]",
        )
        content = content.replace(
            'getPageMap("/docs")',
            f"getPageMap({json.dumps(self._docs_route_base())})",
        )
        content = self._inject_docs_repo_link(content)

        if self.config.project_repo:
            repo = self.config.project_repo
            # `docsRepositoryBase` stays: the feedback link and the 404 page
            # are built from it, and without it Nextra defaults them to its
            # own repository.
            #
            # `editLink` goes. Nextra builds it as base + the page's
            # `filePath`, and `filePath` is the *generated* page —
            # `content/<route>.mdx` — not the Markdown or the Python the page
            # was built from. Every link it produced was a 404:
            # `https://github.com/<owner>/<repo>/content/index.mdx`, with no
            # `blob/<ref>` and naming a directory that exists only inside
            # `.build/`. A link that never resolves is worse than no link.
            # Restoring it means mapping a generated page back to its source,
            # which folio knows per page and Nextra has no way to accept.
            content = content.replace(
                "footer={<Footer />}",
                f'docsRepositoryBase="{repo}"\n'
                "            editLink={null}\n"
                "            footer={<Footer />}",
            )

        if self.config.logo:
            logo_src = Path(self.config.logo)
            if logo_src.exists():
                logo_dest = self.build_dir / "public" / logo_src.name
                logo_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(logo_src, logo_dest)

        content = self._inject_search_config(content)

        layout_path.write_text(content, encoding="utf-8")
        self._record_injected(layout_path)

    def _inject_project_header_logo(self, content: str, name: str) -> str:
        logo = _render_project_header_logo(self.config, name)
        if not logo:
            return _HEADER_LOGO_MARKER_LINE_RE.sub("", content)

        def replace(match: re.Match[str]) -> str:
            indent = match.group(1)
            return "\n".join(f"{indent}{line}" for line in logo.splitlines())

        return _HEADER_LOGO_BLOCK_RE.sub(replace, content)

    def _inject_project_header_actions(self, content: str) -> str:
        actions = _render_project_header_actions(self.config)
        if not actions:
            content = _HEADER_ACTION_IMPORT_MARKER_LINE_RE.sub("", content)
            return _HEADER_ACTION_MARKER_LINE_RE.sub("", content)

        def replace_import(match: re.Match[str]) -> str:
            indent = match.group(1)
            return (
                f"{indent}import {{ ProjectHeaderActions }} "
                'from "@/components/project-header-actions"'
            )

        def replace_actions(match: re.Match[str]) -> str:
            indent = match.group(1)
            return "\n".join(f"{indent}{line}" for line in actions.splitlines())

        content = _HEADER_ACTION_IMPORT_BLOCK_RE.sub(replace_import, content)
        return _HEADER_ACTION_BLOCK_RE.sub(replace_actions, content)

    def _inject_docs_route_page(self, name: str) -> None:
        page_path = self.build_dir / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
        if not page_path.exists():
            self._note_skip("app/docs/[[...mdxPath]]/page.jsx", "file not present")
            return

        description = f"Documentation for {name}"
        site_url = self.config.site_url.rstrip("/") if self.config.site_url else ""
        content = page_path.read_text(encoding="utf-8")
        docs_og_path = self._docs_route_path("opengraph-image")
        docs_index_path = self._docs_route_with_trailing_slash()
        content = content.replace("__PROJECT_NAME__", name)
        content = content.replace("__PROJECT_DESCRIPTION__", description)
        content = content.replace("__SITE_URL__", site_url)
        content = content.replace(
            'from "../../../mdx-components"',
            'from "@/mdx-components"',
        )
        content = content.replace(
            "`${siteUrl}/docs/opengraph-image`",
            f"`${{siteUrl}}{docs_og_path}`",
        )
        content = content.replace(
            '"/docs/opengraph-image"',
            json.dumps(docs_og_path),
        )
        content = content.replace(
            'docsIndexCanonicalPath === "/" ? "/" : "/docs/"',
            f'docsIndexCanonicalPath === "/" ? "/" : {json.dumps(docs_index_path)}',
        )
        content = content.replace(
            '`/docs/${mdxPath.join("/")}/`',
            f'`{self._docs_route_base()}/${{mdxPath.join("/")}}/`',
        )
        # When landing is enabled, canonical is the docs index route.
        # When landing is disabled but a plugin view owns root, canonical is
        # the docs route (not root, which would be the plugin view).
        # Otherwise, canonical is root (the docs-index wrapper).
        if self.config.landing_enabled:
            canonical = docs_index_path
        elif self._plugin_view_owns_root():
            canonical = docs_index_path
        else:
            canonical = "/"
        content = content.replace("__DOCS_INDEX_CANONICAL_PATH__", canonical)
        page_path.write_text(content, encoding="utf-8")
        self._record_injected(page_path)

    def _inject_previews_page(self, name: str) -> None:
        # The previews layout mirrors the docs layout (same Nextra shell), so
        # it is injected with the same replacements: project identity, the
        # optional repo link block, and the search component.
        layout_path = self.build_dir / "app" / "previews" / "layout.tsx"
        if not layout_path.exists():
            return
        monogram = name[:2].lower()
        content = layout_path.read_text(encoding="utf-8")
        content = content.replace("__PROJECT_NAME__", name)
        content = content.replace("__PROJECT_MONOGRAM__", monogram)
        content = self._inject_docs_repo_link(content)
        content = self._inject_search_config(content)
        layout_path.write_text(content, encoding="utf-8")

    def _inject_docs_repo_link(self, content: str) -> str:
        repo = self.config.project_repo
        if not repo:
            content = _REPO_IMPORTS_BLOCK_RE.sub("", content)
            content = _REPO_LINK_BLOCK_RE.sub("", content)
            return content.replace("__PROJECT_REPO__", "")

        content = content.replace("__PROJECT_REPO__", html.escape(repo, quote=True))
        return _REPO_MARKER_LINE_RE.sub("", content)

    def _inject_search_config(self, content: str) -> str:
        if (
            not self.config.search_enabled
            or self.config.theme_header.get("search") is False
        ):
            return self._inject_layout_search_null(content)

        content = self._inject_search_command_import(content)
        return self._inject_layout_search_component(content)

    @staticmethod
    def _inject_layout_search_null(content: str) -> str:
        if "search={" in content:
            return content
        return content.replace(
            "pageMap={await getPageMap",
            "search={null}\n      pageMap={await getPageMap",
            1,
        )

    @staticmethod
    def _inject_search_command_import(content: str) -> str:
        import_line = 'import { SearchCommand } from "@/components/search-command"'
        if import_line in content:
            return content
        page_map_import = 'import { getPageMap } from "nextra/page-map"'
        if page_map_import in content:
            return content.replace(
                page_map_import, f"{page_map_import}\n{import_line}", 1
            )
        return f"{import_line}\n{content}"

    def _inject_layout_search_component(self, content: str) -> str:
        if "search={" in content:
            return content

        placeholder = self.config.search_placeholder
        if placeholder:
            escaped = html.escape(placeholder, quote=True)
            component = f'<SearchCommand placeholder="{escaped}" />'
        else:
            component = "<SearchCommand />"

        return content.replace(
            "pageMap={await getPageMap",
            f"search={{{component}}}\n      pageMap={{await getPageMap",
            1,
        )

    def _inject_og_image(self, name: str) -> None:
        monogram = name[:2].lower()
        description = f"Documentation for {name}"
        og_paths = [
            self.build_dir / "app" / "opengraph-image.tsx",
            self.build_dir / "app" / "docs" / "opengraph-image.tsx",
        ]

        for og_path in og_paths:
            if not og_path.exists():
                self._note_skip(
                    og_path.relative_to(self.build_dir).as_posix(),
                    "optional Open Graph image file not present",
                )
                continue
            content = og_path.read_text(encoding="utf-8")
            content = content.replace("__PROJECT_NAME__", name)
            content = content.replace("__PROJECT_MONOGRAM__", monogram)
            content = content.replace("__PROJECT_DESCRIPTION__", description)
            og_path.write_text(content, encoding="utf-8")
            self._record_injected(og_path)

    def _inject_landing_page(self, name: str) -> None:
        monogram = name[:2].lower()
        cfg = self.config

        # The navbar ships on every public view, not just the landing, so it
        # is filled before the gate below can return early.
        self._inject_landing_navbar(name)

        if not cfg.landing_enabled:
            # When a plugin view owns the root, skip the docs-index wrapper at
            # app/page.tsx — the plugin's view will be written there instead.
            if not self._plugin_view_owns_root():
                self._inject_docs_index_page()
            return

        tagline = (
            cfg.landing_hero_tagline
            if cfg.landing_hero_tagline is not None
            else f".py \u2192 {name.lower()}"
        )
        headline = cfg.landing_hero_headline or f"Documentation for {name}"
        description = (
            cfg.landing_hero_description
            or "Beautiful, modern docs. Zero configuration."
        )
        cta_primary_text = cfg.landing_cta_primary_text
        cta_primary_link = cfg.landing_cta_primary_link
        if cta_primary_link in {"/docs", "/docs/"}:
            cta_primary_link = self._docs_route_base()
        cta_secondary_link = cfg.landing_cta_secondary_link or cfg.project_repo
        cta_secondary_text = cfg.landing_cta_secondary_text or (
            "GitHub" if cta_secondary_link else ""
        )
        cta_secondary_link_json = (
            json.dumps(cta_secondary_link, ensure_ascii=True)
            if cta_secondary_link
            else "null"
        )

        install_commands = cfg.landing_install_commands or [
            f"pip install {name.lower().replace(' ', '-')}",
            f"{name.lower().replace(' ', '-')} init",
            f"{name.lower().replace(' ', '-')} serve",
        ]

        default_features = [
            {
                "title": "Automatic API Reference",
                "description": "Parse Python source and docstrings into classes, functions, type annotations, and parameter tables.",
                "wide": True,
            },
            {
                "title": "One Config File",
                "description": "A single docs.yaml replaces conf.py, Makefile, and requirements.txt. About thirty lines.",
            },
            {
                "title": "Plugin System",
                "description": "Register components, write typed data, generate views, and run post-build hooks.",
            },
            {
                "title": "Dark Mode, Search, Responsive",
                "description": "Full docs site with dark mode, search, and mobile support out of the box.",
                "wide": True,
            },
            {
                "title": "LLM-Friendly Output",
                "description": "Generates llms.txt following the llmstxt.org spec so AI assistants understand your library.",
            },
            {
                "title": "Markdown + API in One Site",
                "description": "Write guides in Markdown alongside auto-generated API reference. One cohesive site.",
                "wide": True,
            },
        ]
        features = cfg.landing_features or default_features
        sections = cfg.landing_sections or self._default_landing_sections(features)

        page_path = self.build_dir / "app" / "page.tsx"
        if page_path.exists():
            content = page_path.read_text(encoding="utf-8")
            content = content.replace(
                "__PROJECT_NAME_JSON__", json.dumps(name, ensure_ascii=True)
            )
            content = content.replace(
                "__PROJECT_MONOGRAM_JSON__", json.dumps(monogram, ensure_ascii=True)
            )
            content = content.replace(
                "__PROJECT_VERSION_JSON__",
                json.dumps(self.config.project_version or "", ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_TAGLINE_JSON__", json.dumps(tagline, ensure_ascii=True)
            )
            content = content.replace(
                "__LANDING_NOTICE_TEXT_JSON__",
                json.dumps(cfg.landing_notice_text, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_NOTICE_LINK_JSON__",
                json.dumps(cfg.landing_notice_link, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_HEADLINE_JSON__", json.dumps(headline, ensure_ascii=True)
            )
            content = content.replace(
                "__LANDING_DESCRIPTION_JSON__",
                json.dumps(description, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_CTA_PRIMARY_TEXT_JSON__",
                json.dumps(cta_primary_text, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_CTA_PRIMARY_LINK_JSON__",
                json.dumps(cta_primary_link, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_CTA_SECONDARY_TEXT_JSON__",
                json.dumps(cta_secondary_text, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_CTA_SECONDARY_LINK_JSON__", cta_secondary_link_json
            )
            content = content.replace(
                "__LANDING_HERO_VARIANT_JSON__",
                json.dumps(cfg.landing_hero_variant, ensure_ascii=True),
            )
            content = content.replace(
                "__LANDING_SECTIONS__", json.dumps(sections, ensure_ascii=True)
            )
            content = content.replace("__PROJECT_NAME__", name)
            content = content.replace("__PROJECT_MONOGRAM__", monogram)
            content = content.replace("__LANDING_TAGLINE__", tagline)
            content = content.replace("__LANDING_HEADLINE__", headline)
            content = content.replace("__LANDING_DESCRIPTION__", description)
            content = content.replace("__LANDING_CTA_PRIMARY_TEXT__", cta_primary_text)
            content = content.replace("__LANDING_CTA_PRIMARY_LINK__", cta_primary_link)
            content = content.replace(
                "__LANDING_CTA_SECONDARY_TEXT__", cta_secondary_text
            )
            content = content.replace(
                "__LANDING_CTA_SECONDARY_LINK__", cta_secondary_link or ""
            )
            content = content.replace(
                "__LANDING_INSTALL_COMMANDS__", json.dumps(install_commands)
            )
            content = content.replace("__LANDING_FEATURES__", json.dumps(features))
            page_path.write_text(content, encoding="utf-8")
            self._record_injected(page_path)
        else:
            self._note_skip("app/page.tsx", "optional landing page file not present")

        # A theme package may keep a lightweight chooser at `/` and move the
        # configured landing to another route. Fill any optional page that
        # explicitly carries landing markers from the same source of truth,
        # instead of forcing the theme to duplicate `docs.yaml` in TypeScript.
        theme_page_replacements = {
            "__PROJECT_NAME_JSON__": json.dumps(name, ensure_ascii=True),
            "__PROJECT_MONOGRAM_JSON__": json.dumps(monogram, ensure_ascii=True),
            "__PROJECT_VERSION_JSON__": json.dumps(
                self.config.project_version or "", ensure_ascii=True
            ),
            "__LANDING_TAGLINE_JSON__": json.dumps(tagline, ensure_ascii=True),
            "__LANDING_NOTICE_TEXT_JSON__": json.dumps(
                cfg.landing_notice_text, ensure_ascii=True
            ),
            "__LANDING_NOTICE_LINK_JSON__": json.dumps(
                cfg.landing_notice_link, ensure_ascii=True
            ),
            "__LANDING_HEADLINE_JSON__": json.dumps(headline, ensure_ascii=True),
            "__LANDING_DESCRIPTION_JSON__": json.dumps(description, ensure_ascii=True),
            "__LANDING_CTA_PRIMARY_TEXT_JSON__": json.dumps(
                cta_primary_text, ensure_ascii=True
            ),
            "__LANDING_CTA_PRIMARY_LINK_JSON__": json.dumps(
                cta_primary_link, ensure_ascii=True
            ),
            "__LANDING_CTA_SECONDARY_TEXT_JSON__": json.dumps(
                cta_secondary_text, ensure_ascii=True
            ),
            "__LANDING_CTA_SECONDARY_LINK_JSON__": cta_secondary_link_json,
            "__LANDING_HERO_VARIANT_JSON__": json.dumps(
                cfg.landing_hero_variant, ensure_ascii=True
            ),
            "__LANDING_SECTIONS__": json.dumps(sections, ensure_ascii=True),
            "__PROJECT_NAME__": name,
            "__PROJECT_MONOGRAM__": monogram,
            "__LANDING_TAGLINE__": tagline,
            "__LANDING_HEADLINE__": headline,
            "__LANDING_DESCRIPTION__": description,
            "__LANDING_CTA_PRIMARY_TEXT__": cta_primary_text,
            "__LANDING_CTA_PRIMARY_LINK__": cta_primary_link,
            "__LANDING_CTA_SECONDARY_TEXT__": cta_secondary_text,
            "__LANDING_CTA_SECONDARY_LINK__": cta_secondary_link or "",
            "__LANDING_INSTALL_COMMANDS__": json.dumps(install_commands),
            "__LANDING_FEATURES__": json.dumps(features),
        }
        for theme_page_path in sorted((self.build_dir / "app").rglob("page.tsx")):
            if theme_page_path == page_path:
                continue
            theme_content = theme_page_path.read_text(encoding="utf-8")
            if not any(marker in theme_content for marker in theme_page_replacements):
                continue
            for marker, replacement in theme_page_replacements.items():
                theme_content = theme_content.replace(marker, replacement)
            theme_page_path.write_text(theme_content, encoding="utf-8")
            self._record_injected(theme_page_path)

    def _inject_landing_navbar(self, name: str) -> None:
        """Fill the navbar's placeholders, landing or no landing.

        This used to live inside ``_inject_landing_page``, behind its
        ``landing_enabled`` gate. But ``PublicLayout`` renders
        ``LandingNavbar`` on every public plugin view, so a project with a
        board and no ``landing:`` key shipped a navbar still containing
        ``__PROJECT_NAME_JSON__`` and died at prerender with a
        ReferenceError. The navbar belongs to the site, not to the landing
        page.

        Every value below is a config read with its own fallback, so this is
        correct whether or not the landing is enabled.
        """
        cfg = self.config
        monogram = name[:2].lower()
        cta_primary_text = cfg.landing_cta_primary_text
        cta_primary_link = cfg.landing_cta_primary_link
        if cta_primary_link in {"/docs", "/docs/"}:
            cta_primary_link = self._docs_route_base()
        cta_secondary_link = cfg.landing_cta_secondary_link or cfg.project_repo
        cta_secondary_text = cfg.landing_cta_secondary_text or (
            "GitHub" if cta_secondary_link else ""
        )
        cta_secondary_link_json = (
            json.dumps(cta_secondary_link, ensure_ascii=True)
            if cta_secondary_link
            else "null"
        )

        navbar_path = self.build_dir / "components" / "landing-navbar.tsx"
        if navbar_path.exists():
            navbar_content = navbar_path.read_text(encoding="utf-8")
            navbar_content = navbar_content.replace(
                "__PROJECT_NAME_JSON__", json.dumps(name, ensure_ascii=True)
            )
            navbar_content = navbar_content.replace(
                "__PROJECT_MONOGRAM_JSON__", json.dumps(monogram, ensure_ascii=True)
            )
            navbar_content = navbar_content.replace(
                "__LANDING_CTA_PRIMARY_TEXT_JSON__",
                json.dumps(cta_primary_text, ensure_ascii=True),
            )
            navbar_content = navbar_content.replace(
                "__LANDING_CTA_PRIMARY_LINK_JSON__",
                json.dumps(cta_primary_link, ensure_ascii=True),
            )
            navbar_content = navbar_content.replace(
                "__LANDING_CTA_SECONDARY_TEXT_JSON__",
                json.dumps(cta_secondary_text, ensure_ascii=True),
            )
            navbar_content = navbar_content.replace(
                "__LANDING_CTA_SECONDARY_LINK_JSON__", cta_secondary_link_json
            )
            navbar_content = navbar_content.replace("__PROJECT_NAME__", name)
            navbar_content = navbar_content.replace("__PROJECT_MONOGRAM__", monogram)
            navbar_content = navbar_content.replace(
                "__LANDING_CTA_SECONDARY_LINK__", cta_secondary_link or ""
            )
            navbar_path.write_text(navbar_content, encoding="utf-8")
            self._record_injected(navbar_path)
        else:
            self._note_skip(
                "components/landing-navbar.tsx",
                "optional landing navbar file not present",
            )

    def _default_landing_sections(self, features: list[dict]) -> list[dict]:
        sections: list[dict] = []
        if features:
            sections.append({"type": "features", "features": features})
        if self.config.landing_hero_variant == "docs-map":
            sections.append({"type": "routes"})
        if (
            self.config.landing_comparison
            and self.config.landing_hero_variant == "source-pipeline"
        ):
            # A mapping carries the project's own table into the section; the
            # legacy `comparison: true` carries nothing and the template falls
            # back to Folio's deprecated bundled matrix.
            comparison = self.config.landing_comparison
            section = {"type": "comparison"}
            if isinstance(comparison, dict):
                section.update(comparison)
            sections.append(section)
        sections.extend([{"type": "output"}, {"type": "cta"}])
        return sections

    def _inject_docs_index_page(self) -> None:
        page_path = self.build_dir / "app" / "page.tsx"
        if not page_path.exists():
            return
        docs_app_path = self._docs_app_import_path()
        content = """import DocsLayout from "__DOCS_APP_PATH__/layout"
import DocsPage, { generateMetadata as generateDocsMetadata } from "__DOCS_APP_PATH__/[[...mdxPath]]/page"

function rootDocsProps() {
  return {
    params: Promise.resolve({ mdxPath: [] as string[] }),
  }
}

export async function generateMetadata() {
  return generateDocsMetadata(rootDocsProps())
}

export default function Home() {
  return (
    <DocsLayout>
      <DocsPage {...rootDocsProps()} />
    </DocsLayout>
  )
}
""".replace("__DOCS_APP_PATH__", docs_app_path)
        page_path.write_text(
            content,
            encoding="utf-8",
        )
        self._record_injected(page_path)

    def _inject_sitemap(self) -> None:
        site_url = self.config.site_url.rstrip("/") if self.config.site_url else ""
        for site_route in ("sitemap.ts", "robots.ts"):
            route_path = self.build_dir / "app" / site_route
            if not route_path.exists():
                self._note_skip(
                    f"app/{site_route}", "optional sitemap/robots file not present"
                )
                continue
            content = route_path.read_text(encoding="utf-8")
            content = content.replace("__SITE_URL__", site_url)
            content = content.replace("__DOCS_ROUTE_BASE__", self._docs_route_base())
            # Include the docs index in the sitemap when landing is enabled or
            # when a plugin view owns root (no duplicate roots in sitemap).
            include_docs_index = (
                self.config.landing_enabled or self._plugin_view_owns_root()
            )
            content = content.replace(
                "__INCLUDE_DOCS_INDEX__",
                "true" if include_docs_index else "false",
            )
            route_path.write_text(content, encoding="utf-8")
            self._record_injected(route_path)

    def _inject_search_postbuild(self) -> None:
        if self.config.search_enabled:
            return

        package_path = self.build_dir / "package.json"
        if not package_path.exists():
            self._note_skip("package.json", "file not present")
            return

        package_json = json.loads(package_path.read_text(encoding="utf-8"))
        scripts = package_json.get("scripts")
        if not isinstance(scripts, dict):
            return

        scripts.pop("postbuild", None)
        package_path.write_text(
            json.dumps(package_json, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self._record_injected(package_path)

    def _is_package_owned(self, rel_path: str) -> bool:
        """True when the theme.package overlay already ships this file."""
        return Path(rel_path) in self._theme_package_files

    def _inject_theme_config(self) -> None:
        self._write_project_theme_module()
        self._inject_theme_configurator_mount()
        if self._is_package_owned("components/theme-configurator.tsx"):
            self._note_skip(
                "components/theme-configurator.tsx",
                "provided by theme.package overlay",
            )
            return
        theme_path = self.build_dir / "components" / "theme-configurator.tsx"
        if not theme_path.exists():
            self._note_skip(
                "components/theme-configurator.tsx",
                "optional theme configurator file not present",
            )
            return
        content = theme_path.read_text(encoding="utf-8")
        content = content.replace(
            'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__',
            f"const configuredDefaultPresetId = {json.dumps(self.config.theme_preset)}",
        )
        theme_path.write_text(content, encoding="utf-8")
        self._record_injected(theme_path)

    def _write_project_theme_module(self) -> None:
        theme_dir = self.build_dir / "theme"
        theme_dir.mkdir(parents=True, exist_ok=True)

        if self._is_package_owned("theme/project-theme.ts"):
            # A theme package may own the preset implementation (documented in
            # theme-packages.md); keep the package's module untouched.
            self._note_skip(
                "theme/project-theme.ts", "provided by theme.package overlay"
            )
        else:
            (theme_dir / "project-theme.ts").write_text(
                _render_project_theme_module(self.config),
                encoding="utf-8",
            )
            self._record_injected(theme_dir / "project-theme.ts")

        # The generated TypeScript contract is Folio-owned and must always be
        # regenerated, even when the package owns project-theme.ts — otherwise
        # the contract would freeze at whatever version was bundled last.
        # Packages may never ship it (enforced via RESERVED_PATHS).
        from folio_docs.docs.theme_contract_codegen import generate_typescript_contract

        (theme_dir / "theme-contract.generated.ts").write_text(
            generate_typescript_contract(),
            encoding="utf-8",
        )
        self._record_injected(theme_dir / "theme-contract.generated.ts")

    def _inject_theme_configurator_mount(self) -> None:
        if is_feature_enabled("theme_configurator"):
            return
        layout_path = self.build_dir / "app" / "docs" / "layout.tsx"
        if not layout_path.exists():
            self._note_skip("app/docs/layout.tsx", "file not present")
            return
        content = layout_path.read_text(encoding="utf-8")
        content = content.replace(
            'import { ThemeConfigurator } from "@/components/theme-configurator"\n',
            "",
        )
        content = content.replace("          <ThemeConfigurator />\n", "")
        content = content.replace("      <ThemeConfigurator />\n", "")
        content = content.replace("      darkMode={false}\n", "")
        layout_path.write_text(content, encoding="utf-8")
        self._record_injected(layout_path)

    def _inject_i18n(self) -> None:
        config_path = self.build_dir / "next.config.mjs"
        if not config_path.exists():
            self._note_skip("next.config.mjs", "file not present")
            return
        content = config_path.read_text(encoding="utf-8")
        content = content.replace(
            "const configuredBasePath = '' // __FOLIO_BASE_PATH__",
            f"const configuredBasePath = {json.dumps(self._configured_base_path())}",
        )
        content = content.replace("__FOLIO_DOCS_ROUTE_BASE__", self._docs_route_base())
        content = re.sub(
            r"contentDirBasePath:\s*(['\"])/docs\1",
            f"contentDirBasePath: {json.dumps(self._docs_route_base())}",
            content,
        )
        content = content.replace(
            'NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? "",',
            (
                'NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? "",\n'
                f"    NEXT_PUBLIC_FOLIO_DOCS_ROUTE_BASE: "
                f"{json.dumps(self._docs_route_base())},"
            ),
        )

        if self.config.i18n_locales and self.config.i18n_default_locale:
            locale_codes = [loc["code"] for loc in self.config.i18n_locales]
            locales_js = ", ".join(f"'{code}'" for code in locale_codes)
            default_locale = self.config.i18n_default_locale
            i18n_block = (
                f"i18n: {{\n"
                f"    locales: [{locales_js}],\n"
                f"    defaultLocale: '{default_locale}',\n"
                f"  }},"
            )
            content = content.replace("__I18N_CONFIG__", i18n_block)
        else:
            content = content.replace("__I18N_CONFIG__\n", "")
            content = content.replace("__I18N_CONFIG__", "")

        config_path.write_text(content, encoding="utf-8")
        self._record_injected(config_path)

    def _configured_base_path(self) -> str:
        return resolve_base_path(self.config)

    def _inject_versions(self) -> None:
        vs_path = self.build_dir / "components" / "version-selector.tsx"
        if not vs_path.exists():
            self._note_skip(
                "components/version-selector.tsx",
                "optional version selector file not present",
            )
            return
        content = vs_path.read_text(encoding="utf-8")
        versions_data = []
        for version in self.config.versions:
            version_data = {
                "label": version.get("label", version.get("path", "")),
                "path": version.get("path", ""),
            }
            if version.get("default_path"):
                version_data["defaultPath"] = version["default_path"]
            versions_data.append(version_data)
        content = content.replace("__VERSIONS__", json.dumps(versions_data))
        content = content.replace(
            "__CURRENT_VERSION_PATH__",
            json.dumps(self.config.current_version_path),
        )
        vs_path.write_text(content, encoding="utf-8")
        self._record_injected(vs_path)

    def _relocate_docs_route(self) -> None:
        source = self.build_dir / "app" / "docs"
        target = self.build_dir / "app" / Path(*self._docs_route_segments())
        if source == target or not source.exists():
            return
        if target.is_relative_to(source):
            self._remove_nested_relocation_residue(source, target)
            temp = self.build_dir / "app" / "__folio_docs_route"
            if temp.exists():
                shutil.rmtree(temp)
            shutil.move(str(source), str(temp))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp), str(target))
            return
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))

    @staticmethod
    def _remove_nested_relocation_residue(source: Path, target: Path) -> None:
        """Drop leftovers of a previous relocation nested inside ``source``.

        With a route base nested under ``/docs`` (e.g. ``/docs/v2``), a warm
        rebuild merges the template's ``app/docs`` over a ``.build`` tree whose
        ``app/docs`` still contains the previously relocated route dir. Without
        this cleanup the whole tree — old relocated copy included — is moved
        again, nesting one level deeper on every warm rebuild
        (``app/docs/v2/v2/...``). A directory at the nested target that holds
        the docs catch-all page can only be such residue: the relocation itself
        put it there, so remove the residue chain before relocating again.
        """
        if not (target / "[[...mdxPath]]" / "page.jsx").exists():
            return
        residue_root = source / target.relative_to(source).parts[0]
        shutil.rmtree(residue_root)


def resolve_base_path(
    config: Config,
    env: Mapping[str, str] | None = None,
) -> str:
    values = os.environ if env is None else env

    if "FOLIO_BASE_PATH" in values:
        return normalize_base_path(values.get("FOLIO_BASE_PATH", ""))
    if config.deploy_base_path:
        return normalize_base_path(config.deploy_base_path)
    if _is_github_pages_deploy(config, values):
        return _github_pages_base_path(values.get("GITHUB_REPOSITORY", ""))
    return ""


def _is_github_pages_deploy(config: Config, env: Mapping[str, str]) -> bool:
    provider = config.deploy_provider.strip().lower()
    env_provider = env.get("FOLIO_DEPLOY_PROVIDER", "").strip().lower()
    if provider != "github-pages" and env_provider != "github-pages":
        return False
    return env.get("GITHUB_ACTIONS", "").strip().lower() == "true"


def _github_pages_base_path(repository: str) -> str:
    owner, _, repo = repository.partition("/")
    if not owner or not repo:
        return ""
    if repo.lower() == f"{owner.lower()}.github.io":
        return ""
    return normalize_base_path(repo)
