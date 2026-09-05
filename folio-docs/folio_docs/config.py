from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
from typing import Any
import warnings

import yaml

from folio_docs.features import is_feature_enabled
from folio_docs.paths import resolve_contained_dir
from folio_docs.plugin import (
    PluginManager,
    normalize_config_key_names,
    user_plugin_names,
)
from folio_docs.schemas.theme_contract import (
    THEME_RADIUS_OPTIONS as _THEME_RADIUS_OPTIONS,
    THEME_TUNE_ALIASES as _THEME_TUNE_ALIASES,
    THEME_TUNE_KEYS as _THEME_TUNE_KEYS,
)

DEFAULT_DOCSTRING_STYLE = "auto"
_EXPERIMENTAL_CONFIG_FEATURES = {
    "i18n": "i18n",
    "versions": "versions",
}
_CSS_CUSTOM_PROPERTY_RE = re.compile(r"^--[A-Za-z0-9][A-Za-z0-9-]*$")
_UNSAFE_CSS_VALUE_RE = re.compile(r"[;{}\n\r<>]")
_THEME_VARIANT_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_UNSAFE_THEME_TEXT_RE = re.compile(r"[<>\n\r]")
# Schemes allowed for theme/project hrefs. Relative paths (no scheme) are also
# permitted; everything else (e.g. ``javascript:``) is rejected to avoid
# self-XSS via injected links.
_SAFE_HREF_SCHEME_RE = re.compile(r"^(?:https?|mailto):", re.IGNORECASE)
_HREF_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
# Schemes rejected for repository URLs. Repo URLs legitimately use non-web
# schemes (ssh://, git://, git+https://) and the scp-style git@host:path form,
# so only genuinely dangerous schemes are blocked.
_DANGEROUS_URL_SCHEME_RE = re.compile(
    r"^(?:javascript|data|vbscript|file):", re.IGNORECASE
)
# Cap on the cartesian product of theme.variants option counts. Every
# combination is resolved and embedded into each generated page's HTML
# (theme-configurator bootstrap presets), so an unbounded product would bloat
# every page by megabytes.
_THEME_VARIANT_COMBINATION_LIMIT = 256


def _normalize_project_repo_ref(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "main"


@dataclass
class Config:
    project_name: str
    project_version: str = "0.0.0"
    project_repo: str = ""
    project_repo_ref: str = "main"
    site_url: str = ""
    deploy_provider: str = ""
    deploy_base_path: str = ""
    docstring_style: str = DEFAULT_DOCSTRING_STYLE
    python_sources: list[str] = field(default_factory=list)
    python_excludes: list[str] = field(default_factory=list)
    doc_sources: list[str] = field(default_factory=list)
    output_dir: str = "_site"
    dark_mode: bool = True
    theme_preset: str = "organic-editorial"
    theme_name: str = ""
    theme_description: str = ""
    theme_scene: str = ""
    theme_preview: dict[str, str] = field(default_factory=dict)
    theme_radius: str = ""
    theme_tune: dict[str, str] = field(default_factory=dict)
    theme_style: dict[str, str] = field(default_factory=dict)
    theme_tokens: dict[str, dict[str, str]] = field(default_factory=dict)
    theme_header: dict[str, Any] = field(default_factory=dict)
    theme_variants: dict[str, dict[str, Any]] = field(default_factory=dict)
    theme_package_path: str = ""
    logo: str = ""
    favicon: str = ""
    template_path: str = ""
    template_overlay_path: str = ""
    template_params: dict[str, Any] = field(default_factory=dict)
    docs_route_base: str = "/docs"
    nav: list[str] = field(default_factory=list)
    sidebar_default_collapsed: bool = True
    generate_llms_txt: bool = True
    generate_llms_full_txt: bool = True
    plugins: list[str] = field(default_factory=list)
    search_enabled: bool = True
    search_placeholder: str = ""
    component_dirs: list[str] = field(default_factory=list)
    component_specs: list[dict[str, Any]] = field(default_factory=list)
    i18n_default_locale: str = ""
    i18n_locales: list[dict] = field(default_factory=list)
    # The landing_* fields are owned by the first-party landing plugin
    # (folio/docs/integrations/landing.py): its configure() hook parses the `landing:`
    # docs.yaml key and populates them at load_config time; core never parses
    # the key. landing_enabled defaults to True for direct Config construction
    # (tests/embedders building a workspace without docs.yaml); the plugin
    # forces it to False when docs.yaml has no `landing:` key.
    landing_enabled: bool = True
    landing_hero_variant: str = "docs-map"
    # ``None`` means the project omitted the field and gets the template
    # fallback. An explicit empty string intentionally removes the kicker.
    landing_hero_tagline: str | None = None
    landing_hero_headline: str = ""
    landing_hero_description: str = ""
    # One message, or a list of up to three the hero chip cycles through.
    landing_notice_text: str | list[str] = ""
    landing_notice_link: str = ""
    landing_cta_primary_text: str = "Get Started"
    landing_cta_primary_link: str = "/docs"
    landing_cta_secondary_text: str = ""
    landing_cta_secondary_link: str = ""
    landing_install_commands: list[str] = field(default_factory=list)
    landing_features: list[dict] = field(default_factory=list)
    landing_sections: list[dict] = field(default_factory=list)
    # `True` selects Folio's deprecated bundled matrix; a mapping carries the
    # project's own `{caption, tools, rows}` table.
    landing_comparison: bool | dict[str, Any] = False
    extra: dict[str, Any] = field(default_factory=dict)
    versions: list[dict] = field(default_factory=list)
    current_version_path: str = ""
    project_dir: str = ""

    def __post_init__(self) -> None:
        self.project_repo_ref = _normalize_project_repo_ref(self.project_repo_ref)

    def resolve_paths(self, base: Path) -> Config:
        output_dir = resolve_output_dir(
            base,
            self.output_dir,
            source_paths=[*self.python_sources, *self.doc_sources],
        )
        return Config(
            project_name=self.project_name,
            project_version=self.project_version,
            project_repo=self.project_repo,
            project_repo_ref=self.project_repo_ref,
            site_url=self.site_url,
            deploy_provider=self.deploy_provider,
            deploy_base_path=self.deploy_base_path,
            docstring_style=self.docstring_style,
            python_sources=[str(base / p) for p in self.python_sources],
            python_excludes=[str(base / p) for p in self.python_excludes],
            doc_sources=[str(base / p) for p in self.doc_sources],
            output_dir=str(output_dir),
            dark_mode=self.dark_mode,
            theme_preset=self.theme_preset,
            theme_name=self.theme_name,
            theme_description=self.theme_description,
            theme_scene=self.theme_scene,
            theme_preview=dict(self.theme_preview),
            theme_radius=self.theme_radius,
            theme_tune=dict(self.theme_tune),
            theme_style=dict(self.theme_style),
            theme_tokens={
                mode: dict(tokens) for mode, tokens in self.theme_tokens.items()
            },
            theme_header=dict(self.theme_header),
            theme_variants=json.loads(json.dumps(self.theme_variants)),
            theme_package_path=resolve_theme_package_path(
                base, self.theme_package_path, str(output_dir)
            ),
            logo=self.logo,
            favicon=self.favicon,
            template_path=str(base / self.template_path) if self.template_path else "",
            template_overlay_path=str(base / self.template_overlay_path)
            if self.template_overlay_path
            else "",
            template_params=json.loads(json.dumps(self.template_params)),
            docs_route_base=self.docs_route_base,
            nav=list(self.nav),
            sidebar_default_collapsed=self.sidebar_default_collapsed,
            generate_llms_txt=self.generate_llms_txt,
            generate_llms_full_txt=self.generate_llms_full_txt,
            search_enabled=self.search_enabled,
            search_placeholder=self.search_placeholder,
            plugins=list(self.plugins),
            component_dirs=[str(base / d) for d in self.component_dirs],
            component_specs=_resolve_component_specs(self.component_specs, base),
            i18n_default_locale=self.i18n_default_locale,
            i18n_locales=list(self.i18n_locales),
            landing_enabled=self.landing_enabled,
            landing_hero_variant=self.landing_hero_variant,
            landing_hero_tagline=self.landing_hero_tagline,
            landing_hero_headline=self.landing_hero_headline,
            landing_hero_description=self.landing_hero_description,
            landing_notice_text=list(self.landing_notice_text)
            if isinstance(self.landing_notice_text, list)
            else self.landing_notice_text,
            landing_notice_link=self.landing_notice_link,
            landing_cta_primary_text=self.landing_cta_primary_text,
            landing_cta_primary_link=self.landing_cta_primary_link,
            landing_cta_secondary_text=self.landing_cta_secondary_text,
            landing_cta_secondary_link=self.landing_cta_secondary_link,
            landing_install_commands=list(self.landing_install_commands),
            landing_features=list(self.landing_features),
            landing_sections=list(self.landing_sections),
            landing_comparison=self.landing_comparison,
            extra=dict(self.extra),
            versions=list(self.versions),
            current_version_path=self.current_version_path,
            # Resolve so the value matches what load_config_with_plugins set
            # before the configure hook (idempotent w.r.t. project_dir).
            project_dir=str(base.resolve()),
        )


def resolve_output_dir(
    base: Path,
    output_dir: str,
    *,
    source_paths: Sequence[str] = (),
) -> Path:
    """Resolve ``output:`` and refuse anything the build would destroy.

    A successful export ends in ``shutil.rmtree(output_dir)`` followed by a
    copy, and ``folio clean`` removes the same path. Containment inside the
    project is therefore not enough: an output that *is* a source directory,
    or that contains one, deletes the very files the build just read. Callers
    that know the configured sources should pass them as ``source_paths``.
    """
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ValueError("Output directory must be a non-empty relative path")

    output_path = Path(output_dir)
    if output_path.is_absolute():
        raise ValueError("Output directory must be relative to the project directory")

    project_root = base.resolve()
    resolved = (project_root / output_path).resolve()
    if resolved == project_root or not resolved.is_relative_to(project_root):
        raise ValueError("Output directory must stay within the project directory")

    git_dir = (project_root / ".git").resolve()
    if git_dir == resolved or git_dir.is_relative_to(resolved):
        raise ValueError(
            f"Output directory {output_dir!r} must not contain the repository's "
            ".git directory; the build removes the output directory before "
            "writing to it"
        )

    for raw_source in source_paths:
        if not isinstance(raw_source, str) or not raw_source.strip():
            continue
        source = (project_root / raw_source).resolve()
        if source == resolved or source.is_relative_to(resolved):
            raise ValueError(
                f"Output directory {output_dir!r} would delete the source "
                f"directory {raw_source!r}; the build removes the output "
                "directory before writing to it. Choose an output path that "
                "is not a source directory and does not contain one"
            )

    return resolved


def resolve_theme_package_path(
    base: Path, theme_package_path: str, output_dir: str
) -> str:
    """Resolve theme.package against the project root with containment checks.

    Delegates to :func:`folio_docs.paths.resolve_contained_dir` (the same guard used
    for ``template.path``): the path is resolved relative to the project root
    and rejected if it escapes the project directory (absolute paths or ``..``
    traversal) or lands inside the ``.build`` or output directories. Existence
    is not required here because ``folio_docs.build`` validates it later.
    """
    if not theme_package_path:
        return ""

    resolved = resolve_contained_dir(
        theme_package_path,
        base,
        output_dir,
        "theme.package",
        must_exist=False,
    )
    return str(resolved)


def _load_config_plugins(plugin_names: Any, base_dir: Path) -> PluginManager:
    """Load first-party default plugins, then the project's `plugins:` entries.

    Default plugins are loaded for every build via ``load_default_plugins``
    (imported directly, never through entry-point lookup; a broken default
    degrades to a warning instead of failing the build); a project listing one
    of them explicitly does not register it twice. A non-list ``plugins:``
    value raises ``ValueError`` so the misconfiguration fails loudly.
    """
    pm = PluginManager(base_dir=base_dir)
    pm.load_default_plugins()
    names = user_plugin_names(plugin_names)
    if names:
        pm.load_plugins(names, base_dir=base_dir)
    return pm


def plugin_config_keys(pm: PluginManager) -> set[str]:
    """Collect the extra config keys declared by loaded plugins.

    Shared by config loading and the CLI (version-matrix sync) so both treat
    an invalid ``config_keys()`` result the same way: warn and skip.
    """
    keys: set[str] = set()
    for result in pm.call_isolated("config_keys", policy="warn_skip"):
        try:
            keys.update(normalize_config_key_names(result))
        except Exception as exc:
            warnings.warn(f"Plugin config_keys() returned invalid keys: {exc}")
    return keys


def _split_components(raw_components: Any) -> tuple[list[str], list[dict[str, Any]]]:
    if raw_components in (None, []):
        return [], []
    if not isinstance(raw_components, list):
        raise ValueError(
            "components must be a list of directory paths or component specs"
        )
    dirs: list[str] = []
    specs: list[dict[str, Any]] = []
    for entry in raw_components:
        if isinstance(entry, str):
            dirs.append(entry)
        elif isinstance(entry, dict):
            specs.append(_normalize_component_spec(entry))
        else:
            raise ValueError(
                "components entries must be directory path strings or "
                f"{{name, from}} mappings; got: {entry!r}"
            )
    return dirs, specs


def _normalize_component_spec(entry: dict[str, Any]) -> dict[str, Any]:
    spec = dict(entry)
    expose = spec.get("expose")
    if isinstance(expose, dict):
        normalized_expose = {}
        if "mdx" in expose:
            normalized_expose["mdx"] = expose["mdx"]
        if normalized_expose:
            spec["expose"] = normalized_expose
        else:
            spec.pop("expose", None)
    return spec


def _resolve_component_specs(
    specs: list[dict[str, Any]],
    base: Path,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for spec in specs:
        item = dict(spec)
        source = item.get("from", item.get("path"))
        if isinstance(source, str):
            key = "from" if "from" in item else "path"
            item[key] = str(base / source)
        resolved.append(item)
    return resolved


def _disabled_known_config_keys(raw: dict[str, Any]) -> set[str]:
    return {
        key
        for key, feature in _EXPERIMENTAL_CONFIG_FEATURES.items()
        if key in raw and not is_feature_enabled(feature)
    }


def _theme_string(raw_value: Any) -> str:
    return raw_value if isinstance(raw_value, str) else ""


def _theme_preview(raw_preview: Any) -> dict[str, str]:
    if not isinstance(raw_preview, dict):
        return {}
    for key in set(raw_preview) - {"light", "dark"}:
        warnings.warn(f"Unknown theme.preview key {key!r}; ignoring it")
    preview: dict[str, str] = {}
    for mode in ("light", "dark"):
        value = raw_preview.get(mode)
        if isinstance(value, str) and value.strip():
            preview[mode] = value.strip()
    return preview


def _theme_swatch(raw_value: Any, path: str) -> str:
    if raw_value in (None, ""):
        return ""
    return _validate_theme_css_value(raw_value, path)


def _theme_text(raw_value: Any, path: str) -> str:
    if raw_value in (None, ""):
        return ""
    if not isinstance(raw_value, str):
        raise ValueError(f"{path} must be a string")
    stripped = raw_value.strip()
    if _UNSAFE_THEME_TEXT_RE.search(stripped):
        raise ValueError(f"{path} contains unsafe text")
    return stripped


def _theme_href(raw_value: Any, path: str) -> str:
    """Sanitize a URL/path value, rejecting unsafe schemes (e.g. javascript:).

    Builds on :func:`_theme_text` (unsafe-character rejection), then requires
    either an ``http(s)``/``mailto`` URL or a scheme-less relative path. Any
    other scheme (``javascript:``, ``data:``, ``vbscript:``, ...) is rejected.
    """
    value = _theme_text(raw_value, path)
    if not value:
        return ""
    if _HREF_SCHEME_RE.match(value) and not _SAFE_HREF_SCHEME_RE.match(value):
        raise ValueError(f"{path} must be an http(s) URL or a relative path")
    return value


def _repo_url(raw_value: Any, path: str) -> str:
    """Validate a repository URL without restricting it to web schemes.

    Unlike :func:`_theme_href` (which guards values rendered as ``<a href>``),
    repository URLs commonly use ``ssh://``, ``git://``, ``git+https://``, the
    scp-style ``git@host:path`` form, or plain strings, all of which are
    accepted verbatim. Only schemes that could execute script or read local
    files (``javascript:``, ``data:``, ``vbscript:``, ``file:``) are rejected.
    """
    value = _theme_text(raw_value, path)
    if not value:
        return ""
    if _DANGEROUS_URL_SCHEME_RE.match(value):
        raise ValueError(
            f"{path} cannot use the javascript:, data:, vbscript:, or file: scheme"
        )
    return value


# Named radius aliases published in older docs (e.g. `tune: { radius: "sm" }`).
# They map onto the configurator's fixed scale in the same order as the drawer
# labels (None / Sm / Md / Lg / Full) so upgrading never breaks a build.
_THEME_RADIUS_ALIASES = {
    "none": "0",
    "sm": "0.3rem",
    "md": "0.5rem",
    "lg": "0.75rem",
    "full": "1rem",
}


def _theme_radius(raw_value: Any) -> str:
    """Validate theme.radius against the fixed radius scale.

    The template maps the configured radius onto a fixed index scale; any
    value outside the scale would silently render as the 0.5rem default, so
    unknown values are rejected up front. Legacy named values (``none``,
    ``sm``, ``md``, ``lg``, ``full``) are accepted as aliases for the scale
    values so configs written against older docs keep building.
    """
    value = _theme_string(raw_value).strip()
    if not value:
        return ""
    alias = _THEME_RADIUS_ALIASES.get(value.lower())
    if alias is not None:
        return alias
    if value not in _THEME_RADIUS_OPTIONS:
        options = ", ".join(repr(option) for option in _THEME_RADIUS_OPTIONS)
        aliases = ", ".join(repr(alias) for alias in _THEME_RADIUS_ALIASES)
        raise ValueError(
            f"theme.radius must be one of {options} "
            f"(or a named alias: {aliases}); got {value!r}"
        )
    return value


def _theme_bool(raw_value: Any, path: str) -> bool | None:
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        normalized = raw_value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    raise ValueError(f"{path} must be a boolean")


def _validate_theme_css_value(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} values must be strings")
    stripped = value.strip()
    if not stripped or _UNSAFE_CSS_VALUE_RE.search(stripped):
        raise ValueError(f"{path} contains an unsafe CSS value")
    return stripped


def _theme_css_vars(raw_vars: Any, path: str) -> dict[str, str]:
    if raw_vars in (None, ""):
        return {}
    if not isinstance(raw_vars, dict):
        raise ValueError(f"{path} must be a mapping of CSS custom properties")

    normalized: dict[str, str] = {}
    for key, value in raw_vars.items():
        if not isinstance(key, str) or not _CSS_CUSTOM_PROPERTY_RE.match(key):
            raise ValueError(f"{path} contains invalid CSS custom property {key!r}")
        normalized[key] = _validate_theme_css_value(value, path)
    return normalized


def _theme_tokens(raw_tokens: Any) -> dict[str, dict[str, str]]:
    if raw_tokens in (None, ""):
        return {}
    if not isinstance(raw_tokens, dict):
        raise ValueError("theme.tokens must be a mapping")

    tokens: dict[str, dict[str, str]] = {}
    for mode in ("light", "dark"):
        mode_tokens = _theme_css_vars(raw_tokens.get(mode), f"theme.tokens.{mode}")
        if mode_tokens:
            tokens[mode] = mode_tokens
    return tokens


def _theme_header(raw_header: Any) -> dict[str, Any]:
    if raw_header in (None, ""):
        return {}
    if not isinstance(raw_header, dict):
        raise ValueError("theme.header must be a mapping")

    text_keys = ("brand", "badge", "action_label", "repo", "action_href")
    bool_keys = ("theme_toggle", "search")
    for key in set(raw_header) - set(text_keys) - set(bool_keys):
        warnings.warn(f"Unknown theme.header key {key!r}; ignoring it")

    header: dict[str, Any] = {}
    for key in ("brand", "badge", "action_label"):
        value = _theme_text(raw_header.get(key, ""), f"theme.header.{key}")
        if value:
            header[key] = value
    for key in ("repo", "action_href"):
        value = _theme_href(raw_header.get(key, ""), f"theme.header.{key}")
        if value:
            header[key] = value
    for key in ("theme_toggle", "search"):
        value = _theme_bool(raw_header.get(key), f"theme.header.{key}")
        if value is not None:
            header[key] = value
    return header


def _theme_variant_id(raw_id: Any, path: str) -> str:
    if not isinstance(raw_id, str) or not _THEME_VARIANT_ID_RE.match(raw_id):
        raise ValueError(
            f"{path} must start with a letter and contain only letters, "
            "numbers, underscores, or hyphens"
        )
    return raw_id


def _theme_variant_option(raw_option: Any, path: str) -> dict[str, Any]:
    if not isinstance(raw_option, dict):
        raise ValueError(f"{path} must be a mapping")
    return {
        "label": _theme_text(raw_option.get("label", ""), f"{path}.label"),
        "description": _theme_text(
            raw_option.get("description", ""),
            f"{path}.description",
        ),
        "swatch": _theme_swatch(raw_option.get("swatch", ""), f"{path}.swatch"),
        "preview": _theme_preview(raw_option.get("preview", {})),
        "style": _theme_css_vars(raw_option.get("style", {}), f"{path}.style"),
        "tokens": _theme_tokens(raw_option.get("tokens", {})),
    }


def _theme_variants(raw_variants: Any) -> dict[str, dict[str, Any]]:
    if raw_variants in (None, ""):
        return {}
    if not isinstance(raw_variants, dict):
        raise ValueError("theme.variants must be a mapping")

    variants: dict[str, dict[str, Any]] = {}
    for raw_control_id, raw_control in raw_variants.items():
        control_id = _theme_variant_id(raw_control_id, "theme.variants key")
        if not isinstance(raw_control, dict):
            raise ValueError(f"theme.variants.{control_id} must be a mapping")
        raw_options = raw_control.get("options", {})
        if not isinstance(raw_options, dict) or not raw_options:
            raise ValueError(
                f"theme.variants.{control_id}.options must be a non-empty mapping"
            )

        options: dict[str, dict[str, Any]] = {}
        for raw_option_id, raw_option in raw_options.items():
            option_id = _theme_variant_id(
                raw_option_id,
                f"theme.variants.{control_id}.options key",
            )
            option = _theme_variant_option(
                raw_option,
                f"theme.variants.{control_id}.options.{option_id}",
            )
            if not option["label"]:
                option["label"] = option_id.replace("-", " ").replace("_", " ").title()
            options[option_id] = option

        default = _theme_text(
            raw_control.get("default", ""),
            f"theme.variants.{control_id}.default",
        ) or next(iter(options))
        if default not in options:
            raise ValueError(
                f"theme.variants.{control_id}.default must match an option"
            )

        variants[control_id] = {
            "label": _theme_text(
                raw_control.get("label", ""),
                f"theme.variants.{control_id}.label",
            )
            or control_id.replace("-", " ").replace("_", " ").title(),
            "description": _theme_text(
                raw_control.get("description", ""),
                f"theme.variants.{control_id}.description",
            ),
            "default": default,
            "options": options,
        }

    combinations = math.prod(len(control["options"]) for control in variants.values())
    if combinations > _THEME_VARIANT_COMBINATION_LIMIT:
        raise ValueError(
            f"theme.variants define {combinations} option combinations across "
            f"all controls, which exceeds the limit of "
            f"{_THEME_VARIANT_COMBINATION_LIMIT}. Every combination is resolved "
            "and embedded into each generated page's HTML, so large products "
            "bloat every page. Reduce the number of controls or options."
        )
    return variants


def _theme_tune(raw_tune: Any) -> dict[str, str]:
    if raw_tune in (None, ""):
        return {}
    if not isinstance(raw_tune, dict):
        raise ValueError("theme.tune must be a mapping")

    normalized: dict[str, str] = {}
    for key, value in raw_tune.items():
        if not isinstance(key, str):
            raise ValueError("theme.tune keys must be strings")
        canonical = _THEME_TUNE_ALIASES.get(key, key)
        if canonical == "radius":
            continue
        if canonical not in _THEME_TUNE_KEYS:
            warnings.warn(f"Unknown theme.tune key {key!r}; ignoring it")
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"theme.tune.{key} must be a non-empty string")
        normalized[canonical] = value.strip()
    return normalized


def _theme_package_path(raw_theme: Any) -> str:
    if not isinstance(raw_theme, dict):
        return ""
    path = raw_theme.get("package", raw_theme.get("path", ""))
    return path if isinstance(path, str) else ""


def _template_path(raw_template: Any) -> str:
    if not isinstance(raw_template, dict):
        return ""
    path = raw_template.get("path", "")
    return path if isinstance(path, str) else ""


def _template_overlay_path(raw_template: Any) -> str:
    """Validate the opt-in ``template.overlay_path`` partial-override key.

    ``template.overlay_path`` layers user-owned files on top of the bundled
    template (user wins, missing files fall back to the bundled template). It is
    mutually exclusive with ``template.path`` (a full replacement): configuring
    both is ambiguous, so the overlay is ignored with a warning and the full
    replacement wins. See ``docs/guide/theming/custom-templates.md``.
    """
    if not isinstance(raw_template, dict):
        return ""
    path = raw_template.get("overlay_path", "")
    if not isinstance(path, str) or not path:
        return ""
    if isinstance(raw_template.get("path", ""), str) and raw_template.get("path", ""):
        warnings.warn(
            "template.overlay_path is ignored when template.path is set; "
            "template.path is a full replacement"
        )
        return ""
    return path


def _template_params(raw_template: Any) -> dict[str, Any]:
    """Validate ``template.params`` against its documented contract.

    ``template.params`` is an arbitrary JSON-serializable mapping that Folio
    emits verbatim into ``lib/folio-template.ts`` as ``folioTemplateParams``;
    Folio never interprets the values. The contract is:

    - absent (``template`` not a mapping or no ``params`` key) -> ``{}``
    - ``null`` -> ``{}``
    - a non-mapping value (list, string, number, ...) -> ``{}`` with a warning,
      because the template can still build with empty params
    - a mapping that is not JSON-serializable -> a clear ``ValueError``, because
      it cannot be emitted into ``folio-template.ts`` and would break the build

    See ``docs/guide/theming/custom-templates.md`` for the full contract.
    """
    if not isinstance(raw_template, dict):
        return {}
    params = raw_template.get("params", {})
    if params is None:
        return {}
    if not isinstance(params, dict):
        warnings.warn("template.params must be a mapping; ignoring it")
        return {}
    try:
        json.dumps(params)
    except (TypeError, ValueError) as exc:
        raise ValueError("template.params must be JSON-serializable") from exc
    return dict(params)


def _template_docs_route_base(raw_template: Any) -> str:
    if not isinstance(raw_template, dict):
        return "/docs"
    return normalize_docs_route_base(raw_template.get("docs_route_base", "/docs"))


def normalize_docs_route_base(value: Any) -> str:
    if not isinstance(value, str):
        return "/docs"
    path = value.strip()
    if not path:
        return "/docs"
    if path == "/":
        raise ValueError("template.docs_route_base must be a non-root URL path")
    if "?" in path or "#" in path:
        raise ValueError("template.docs_route_base cannot include query or fragment")
    path = f"/{path.lstrip('/')}".rstrip("/")
    if path == "/":
        raise ValueError("template.docs_route_base must be a non-root URL path")
    if any(seg in ("..", ".") for seg in path.strip("/").split("/")):
        raise ValueError("template.docs_route_base cannot contain '.' or '..' segments")
    return path


def normalize_base_path(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    path = value.strip()
    if not path or path == "/":
        return ""
    path = f"/{path.lstrip('/')}".rstrip("/")
    return "" if path == "/" else path


def load_config(path: Path) -> Config:
    config, _pm = load_config_with_plugins(path)
    return config


def _config_mapping(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return value


def _config_string_list(value: Any, key: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return value


def load_config_with_plugins(
    path: Path,
    plugin_base_dir: Path | None = None,
) -> tuple[Config, PluginManager]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    plugins = raw.get("plugins", [])
    base_dir = (plugin_base_dir or path.parent).resolve()
    pm = _load_config_plugins(plugins, base_dir=base_dir)

    known_keys = (
        {
            "project",
            "source",
            "output",
            "theme",
            "nav",
            "sidebar",
            "llm",
            "plugins",
            "components",
            "i18n",
            "search",
            "versions",
            "deploy",
            "template",
        }
        | _disabled_known_config_keys(raw)
        | plugin_config_keys(pm)
    )
    unknown = set(raw.keys()) - known_keys
    if unknown:
        warnings.warn(f"Unknown config keys in docs.yaml: {', '.join(sorted(unknown))}")

    project = _config_mapping(raw, "project")
    source = _config_mapping(raw, "source")
    theme = _config_mapping(raw, "theme")
    llm = _config_mapping(raw, "llm")

    project_name = project.get("name")
    if not isinstance(project_name, str) or not project_name.strip():
        warnings.warn(
            "project.name must be a non-empty string in docs.yaml; "
            "defaulting to 'Untitled'"
        )
        project_name = "Untitled"

    sidebar = raw.get("sidebar", {})
    if not isinstance(sidebar, dict):
        sidebar = {}
    search = raw.get("search", {})
    template = raw.get("template", {})
    i18n = raw.get("i18n", {}) if is_feature_enabled("i18n") else {}
    if not isinstance(i18n, dict):
        i18n = {}
    deploy = raw.get("deploy", {}) if isinstance(raw.get("deploy", {}), dict) else {}

    python_cfg = source.get("python", {})
    if isinstance(python_cfg, dict):
        python_sources = _config_string_list(
            python_cfg.get("paths", []), "source.python.paths"
        )
        python_excludes = _config_string_list(
            python_cfg.get("exclude", []), "source.python.exclude"
        )
    elif isinstance(python_cfg, list):
        python_sources = _config_string_list(python_cfg, "source.python")
        python_excludes = []
    elif python_cfg is None:
        python_sources = []
        python_excludes = []
    else:
        raise ValueError("source.python must be a mapping or a list of strings")
    doc_sources = _config_string_list(source.get("docs", []), "source.docs")
    nav = _config_string_list(raw.get("nav", []), "nav")
    component_dirs, component_specs = _split_components(raw.get("components", []))

    config = Config(
        project_name=project_name,
        project_version=project.get("version", "0.0.0"),
        project_repo=_repo_url(project.get("repo", ""), "project.repo"),
        project_repo_ref=_normalize_project_repo_ref(project.get("repo_ref", "main")),
        site_url=project.get("url", ""),
        deploy_provider=deploy.get("provider", "")
        if isinstance(deploy.get("provider", ""), str)
        else "",
        deploy_base_path=normalize_base_path(deploy.get("base_path", "")),
        docstring_style=python_cfg.get("docstring_style", DEFAULT_DOCSTRING_STYLE)
        if isinstance(python_cfg, dict)
        else DEFAULT_DOCSTRING_STYLE,
        python_sources=python_sources,
        python_excludes=python_excludes,
        doc_sources=doc_sources,
        output_dir=raw.get("output", "_site"),
        dark_mode=theme.get("dark_mode", True),
        theme_preset=theme.get("preset", "organic-editorial"),
        theme_name=_theme_string(theme.get("name", "")),
        theme_description=_theme_string(theme.get("description", "")),
        theme_scene=_theme_string(theme.get("scene", "")),
        theme_preview=_theme_preview(theme.get("preview", {})),
        theme_radius=_theme_radius(
            theme.get(
                "radius",
                theme.get("tune", {}).get("radius", "")
                if isinstance(theme.get("tune", {}), dict)
                else "",
            )
        ),
        theme_tune=_theme_tune(theme.get("tune", {})),
        theme_style=_theme_css_vars(theme.get("style", {}), "theme.style"),
        theme_tokens=_theme_tokens(theme.get("tokens", {})),
        theme_header=_theme_header(theme.get("header", {})),
        theme_variants=_theme_variants(theme.get("variants", {})),
        theme_package_path=_theme_package_path(theme),
        logo=theme.get("logo", ""),
        favicon=theme.get("favicon", ""),
        template_path=_template_path(template),
        template_overlay_path=_template_overlay_path(template),
        template_params=_template_params(template),
        docs_route_base=_template_docs_route_base(template),
        nav=nav,
        sidebar_default_collapsed=sidebar.get("default_collapsed", True) is True,
        generate_llms_txt=llm.get("generate_llms_txt", True),
        generate_llms_full_txt=llm.get("generate_llms_full_txt", True),
        search_enabled=search.get("enabled", True)
        if isinstance(search, dict)
        else True,
        search_placeholder=search.get("placeholder", "")
        if isinstance(search, dict)
        else "",
        # _load_config_plugins already rejected non-list values; `or []`
        # covers an empty `plugins:` key (YAML null).
        plugins=list(plugins or []),
        component_dirs=component_dirs,
        component_specs=component_specs,
        i18n_default_locale=i18n.get("default_locale", ""),
        i18n_locales=i18n.get("locales", []),
        # landing_* fields are populated by the first-party landing plugin's
        # configure hook, dispatched below — core does not parse the key.
        versions=raw.get("versions", []) if is_feature_enabled("versions") else [],
        # Set before the configure hook is dispatched so every plugin can
        # resolve relative paths against the project directory; resolve_paths
        # re-derives the same absolute directory later.
        project_dir=str(base_dir),
    )
    pm.call_isolated("configure", policy="fail_fast", config=config, raw_config=raw)
    return config, pm
