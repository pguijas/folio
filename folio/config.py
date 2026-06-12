from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import warnings

import yaml

from folio.features import is_feature_enabled
from folio.plugin import PluginManager, normalize_config_key_names

DEFAULT_DOCSTRING_STYLE = "auto"
_EXPERIMENTAL_CONFIG_FEATURES = {
    "components": "custom_components",
    "i18n": "i18n",
    "landing": "landing",
    "plugins": "plugins",
    "roadmap": "roadmap",
    "versions": "versions",
}


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
    logo: str = ""
    favicon: str = ""
    nav: list[str] = field(default_factory=list)
    generate_llms_txt: bool = True
    generate_llms_full_txt: bool = True
    plugins: list[str] = field(default_factory=list)
    search_enabled: bool = True
    search_placeholder: str = ""
    component_dirs: list[str] = field(default_factory=list)
    component_specs: list[dict[str, Any]] = field(default_factory=list)
    i18n_default_locale: str = ""
    i18n_locales: list[dict] = field(default_factory=list)
    landing_enabled: bool = True
    landing_hero_variant: str = "docs-map"
    landing_hero_tagline: str = ""
    landing_hero_headline: str = ""
    landing_hero_description: str = ""
    landing_cta_primary_text: str = "Get Started"
    landing_cta_primary_link: str = "/docs"
    landing_cta_secondary_text: str = ""
    landing_cta_secondary_link: str = ""
    landing_install_commands: list[str] = field(default_factory=list)
    landing_features: list[dict] = field(default_factory=list)
    landing_sections: list[dict] = field(default_factory=list)
    landing_comparison: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    versions: list[dict] = field(default_factory=list)
    current_version_path: str = ""

    def __post_init__(self) -> None:
        self.project_repo_ref = _normalize_project_repo_ref(self.project_repo_ref)

    def resolve_paths(self, base: Path) -> Config:
        output_dir = resolve_output_dir(base, self.output_dir)
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
            logo=self.logo,
            favicon=self.favicon,
            nav=list(self.nav),
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
        )


def resolve_output_dir(base: Path, output_dir: str) -> Path:
    if not isinstance(output_dir, str) or not output_dir.strip():
        raise ValueError("Output directory must be a non-empty relative path")

    output_path = Path(output_dir)
    if output_path.is_absolute():
        raise ValueError("Output directory must be relative to the project directory")

    project_root = base.resolve()
    resolved = (project_root / output_path).resolve()
    if resolved == project_root or not resolved.is_relative_to(project_root):
        raise ValueError("Output directory must stay within the project directory")

    return resolved


def _load_config_plugins(plugin_names: list[str], base_dir: Path) -> PluginManager:
    pm = PluginManager(base_dir=base_dir)
    if plugin_names:
        pm.load_plugins(plugin_names, base_dir=base_dir)
    return pm


def _plugin_config_keys(pm: PluginManager) -> set[str]:
    keys: set[str] = set()
    for result in pm.pm.hook.config_keys():
        keys.update(normalize_config_key_names(result))
    return keys


def _split_components(raw_components: Any) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(raw_components, list):
        return [], []
    dirs: list[str] = []
    specs: list[dict[str, Any]] = []
    for entry in raw_components:
        if isinstance(entry, str):
            dirs.append(entry)
        elif isinstance(entry, dict):
            specs.append(_normalize_component_spec(entry))
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


def _landing_enabled(raw_landing: Any) -> bool:
    if isinstance(raw_landing, bool):
        return raw_landing
    if isinstance(raw_landing, dict):
        return raw_landing.get("enabled", True) is not False
    return True


def _disabled_known_config_keys(raw: dict[str, Any]) -> set[str]:
    return {
        key
        for key, feature in _EXPERIMENTAL_CONFIG_FEATURES.items()
        if key in raw and not is_feature_enabled(feature)
    }


def _landing_hero_variant(raw_variant: Any) -> str:
    if raw_variant in {"docs-map", "source-pipeline"}:
        return str(raw_variant)
    return "docs-map"


def _landing_sections(raw_sections: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_sections, list):
        return []
    return [dict(section) for section in raw_sections if isinstance(section, dict)]


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


def load_config_with_plugins(
    path: Path,
    plugin_base_dir: Path | None = None,
) -> tuple[Config, PluginManager]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = yaml.safe_load(path.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    raw_plugins = raw.get("plugins", [])
    plugins = raw_plugins if is_feature_enabled("plugins") else []
    base_dir = (plugin_base_dir or path.parent).resolve()
    pm = _load_config_plugins(plugins, base_dir=base_dir)

    known_keys = (
        {
            "project",
            "source",
            "output",
            "theme",
            "nav",
            "llm",
            "plugins",
            "components",
            "i18n",
            "search",
            "landing",
            "versions",
            "deploy",
        }
        | _disabled_known_config_keys(raw)
        | _plugin_config_keys(pm)
    )
    unknown = set(raw.keys()) - known_keys
    if unknown:
        warnings.warn(f"Unknown config keys in docs.yaml: {', '.join(sorted(unknown))}")

    project = raw.get("project", {})

    if not isinstance(project.get("name"), str) or not project.get("name", "").strip():
        warnings.warn(
            "project.name is missing or empty in docs.yaml, defaulting to 'Untitled'"
        )

    source = raw.get("source", {})
    theme = raw.get("theme", {})
    llm = raw.get("llm", {})
    search = raw.get("search", {})
    i18n = raw.get("i18n", {}) if is_feature_enabled("i18n") else {}
    if not isinstance(i18n, dict):
        i18n = {}
    deploy = raw.get("deploy", {}) if isinstance(raw.get("deploy", {}), dict) else {}

    raw_landing = raw.get("landing", {})
    landing = (
        raw_landing
        if is_feature_enabled("landing") and isinstance(raw_landing, dict)
        else {}
    )
    landing_hero = landing.get("hero", {}) if isinstance(landing, dict) else {}
    landing_cta = landing.get("cta", {}) if isinstance(landing, dict) else {}
    landing_cta_primary = (
        landing_cta.get("primary", {}) if isinstance(landing_cta, dict) else {}
    )
    landing_cta_secondary = (
        landing_cta.get("secondary", {}) if isinstance(landing_cta, dict) else {}
    )
    python_cfg = source.get("python", {})
    if isinstance(python_cfg, dict):
        python_sources = python_cfg.get("paths", [])
        python_excludes = python_cfg.get("exclude", [])
    elif isinstance(python_cfg, list):
        python_sources = python_cfg
        python_excludes = []
    else:
        python_sources = []
        python_excludes = []
    component_dirs, component_specs = (
        _split_components(raw.get("components", []))
        if is_feature_enabled("custom_components")
        else ([], [])
    )

    config = Config(
        project_name=project.get("name", "Untitled"),
        project_version=project.get("version", "0.0.0"),
        project_repo=project.get("repo", ""),
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
        doc_sources=source.get("docs", []),
        output_dir=raw.get("output", "_site"),
        dark_mode=theme.get("dark_mode", True),
        theme_preset=theme.get("preset", "organic-editorial"),
        logo=theme.get("logo", ""),
        favicon=theme.get("favicon", ""),
        nav=raw.get("nav", []),
        generate_llms_txt=llm.get("generate_llms_txt", True),
        generate_llms_full_txt=llm.get("generate_llms_full_txt", True),
        search_enabled=search.get("enabled", True)
        if isinstance(search, dict)
        else True,
        search_placeholder=search.get("placeholder", "")
        if isinstance(search, dict)
        else "",
        plugins=list(plugins),
        component_dirs=component_dirs,
        component_specs=component_specs,
        i18n_default_locale=i18n.get("default_locale", ""),
        i18n_locales=i18n.get("locales", []),
        landing_enabled=(
            _landing_enabled(raw_landing) if is_feature_enabled("landing") else False
        ),
        landing_hero_variant=_landing_hero_variant(landing_hero.get("variant")),
        landing_hero_tagline=landing_hero.get("tagline", ""),
        landing_hero_headline=landing_hero.get("headline", ""),
        landing_hero_description=landing_hero.get("description", ""),
        landing_cta_primary_text=landing_cta_primary.get("text", "Get Started"),
        landing_cta_primary_link=landing_cta_primary.get("link", "/docs"),
        landing_cta_secondary_text=landing_cta_secondary.get("text", ""),
        landing_cta_secondary_link=landing_cta_secondary.get("link", ""),
        landing_install_commands=landing.get("install", [])
        if isinstance(landing, dict)
        else [],
        landing_features=landing.get("features", [])
        if isinstance(landing, dict)
        else [],
        landing_sections=_landing_sections(
            landing.get("sections") if isinstance(landing, dict) else []
        ),
        # Opt-in: the comparison section renders a Folio-branded feature
        # matrix, so third-party projects must request it explicitly.
        landing_comparison=(
            landing.get("comparison") is True
            if is_feature_enabled("landing") and isinstance(landing, dict)
            else False
        ),
        versions=raw.get("versions", []) if is_feature_enabled("versions") else [],
    )
    pm.pm.hook.configure(config=config, raw_config=raw)
    return config, pm
