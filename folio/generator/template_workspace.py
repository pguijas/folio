from __future__ import annotations

import html
import json
import os
import re
import shutil
from collections.abc import Mapping
from pathlib import Path

from folio.config import Config, normalize_base_path
from folio.features import is_feature_enabled

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

        ignore = shutil.ignore_patterns(
            "node_modules", ".next", "__pycache__", ".git", "content"
        )

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


class TemplateConfigInjector:
    def __init__(self, config: Config, build_dir: str | Path) -> None:
        self.config = config
        self.build_dir = Path(build_dir)

    def inject(self) -> None:
        name = self.config.project_name

        self._inject_root_layout(name)
        self._inject_docs_layout(name)
        self._inject_docs_route_page(name)
        self._inject_og_image(name)
        self._inject_landing_page(name)
        self._inject_sitemap()
        self._inject_search_postbuild()
        self._inject_theme_config()
        self._inject_i18n()
        self._inject_versions()

    def _inject_root_layout(self, name: str) -> None:
        layout_path = self.build_dir / "app" / "layout.tsx"
        if not layout_path.exists():
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

    def _inject_docs_layout(self, name: str) -> None:
        layout_path = self.build_dir / "app" / "docs" / "layout.tsx"
        if not layout_path.exists():
            return
        content = layout_path.read_text(encoding="utf-8")

        monogram = name[:2].lower()
        content = content.replace("__PROJECT_NAME__", name)
        content = content.replace("__PROJECT_MONOGRAM__", monogram)
        content = self._inject_docs_repo_link(content)

        if self.config.project_repo:
            repo = self.config.project_repo
            content = content.replace(
                "footer={<Footer />}",
                f'docsRepositoryBase="{repo}"\n            footer={{<Footer />}}',
            )

        if self.config.logo:
            logo_src = Path(self.config.logo)
            if logo_src.exists():
                logo_dest = self.build_dir / "public" / logo_src.name
                logo_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(logo_src, logo_dest)

        content = self._inject_search_config(content)

        layout_path.write_text(content, encoding="utf-8")

    def _inject_docs_route_page(self, name: str) -> None:
        page_path = self.build_dir / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
        if not page_path.exists():
            return

        description = f"Documentation for {name}"
        site_url = self.config.site_url.rstrip("/") if self.config.site_url else ""
        content = page_path.read_text(encoding="utf-8")
        content = content.replace("__PROJECT_NAME__", name)
        content = content.replace("__PROJECT_DESCRIPTION__", description)
        content = content.replace("__SITE_URL__", site_url)
        content = content.replace(
            "__DOCS_INDEX_CANONICAL_PATH__",
            "/docs/" if self.config.landing_enabled else "/",
        )
        page_path.write_text(content, encoding="utf-8")

    def _inject_docs_repo_link(self, content: str) -> str:
        repo = self.config.project_repo
        if not repo:
            content = _REPO_IMPORTS_BLOCK_RE.sub("", content)
            content = _REPO_LINK_BLOCK_RE.sub("", content)
            return content.replace("__PROJECT_REPO__", "")

        content = content.replace("__PROJECT_REPO__", html.escape(repo, quote=True))
        return _REPO_MARKER_LINE_RE.sub("", content)

    def _inject_search_config(self, content: str) -> str:
        if not self.config.search_enabled:
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
                continue
            content = og_path.read_text(encoding="utf-8")
            content = content.replace("__PROJECT_NAME__", name)
            content = content.replace("__PROJECT_MONOGRAM__", monogram)
            content = content.replace("__PROJECT_DESCRIPTION__", description)
            og_path.write_text(content, encoding="utf-8")

    def _inject_landing_page(self, name: str) -> None:
        monogram = name[:2].lower()
        cfg = self.config

        if not cfg.landing_enabled:
            self._inject_docs_index_page()
            return

        tagline = cfg.landing_hero_tagline or f".py \u2192 {name.lower()}"
        headline = cfg.landing_hero_headline or f"Documentation for {name}"
        description = (
            cfg.landing_hero_description
            or "Beautiful, modern docs. Zero configuration."
        )
        cta_primary_text = cfg.landing_cta_primary_text
        cta_primary_link = cfg.landing_cta_primary_link
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
                "description": "A single docs.yaml replaces conf.py, Makefile, and requirements.txt. Typically under 30 lines.",
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
                "__LANDING_TAGLINE_JSON__", json.dumps(tagline, ensure_ascii=True)
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
            sections.append({"type": "comparison"})
        sections.extend([{"type": "output"}, {"type": "cta"}])
        return sections

    def _inject_docs_index_page(self) -> None:
        page_path = self.build_dir / "app" / "page.tsx"
        if not page_path.exists():
            return
        page_path.write_text(
            """import DocsLayout from "./docs/layout"
import DocsPage, { generateMetadata as generateDocsMetadata } from "./docs/[[...mdxPath]]/page"

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
""",
            encoding="utf-8",
        )

    def _inject_sitemap(self) -> None:
        site_url = self.config.site_url.rstrip("/") if self.config.site_url else ""
        for site_route in ("sitemap.ts", "robots.ts"):
            route_path = self.build_dir / "app" / site_route
            if not route_path.exists():
                continue
            content = route_path.read_text(encoding="utf-8")
            content = content.replace("__SITE_URL__", site_url)
            content = content.replace(
                "__INCLUDE_DOCS_INDEX__",
                "true" if self.config.landing_enabled else "false",
            )
            route_path.write_text(content, encoding="utf-8")

    def _inject_search_postbuild(self) -> None:
        if self.config.search_enabled:
            return

        package_path = self.build_dir / "package.json"
        if not package_path.exists():
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

    def _inject_theme_config(self) -> None:
        self._inject_theme_configurator_mount()
        theme_path = self.build_dir / "components" / "theme-configurator.tsx"
        if not theme_path.exists():
            return
        content = theme_path.read_text(encoding="utf-8")
        content = content.replace(
            'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__',
            f"const configuredDefaultPresetId = {json.dumps(self.config.theme_preset)}",
        )
        theme_path.write_text(content, encoding="utf-8")

    def _inject_theme_configurator_mount(self) -> None:
        if is_feature_enabled("theme_configurator"):
            return
        layout_path = self.build_dir / "app" / "docs" / "layout.tsx"
        if not layout_path.exists():
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

    def _inject_i18n(self) -> None:
        config_path = self.build_dir / "next.config.mjs"
        if not config_path.exists():
            return
        content = config_path.read_text(encoding="utf-8")
        content = content.replace(
            "const configuredBasePath = '' // __FOLIO_BASE_PATH__",
            f"const configuredBasePath = {json.dumps(self._configured_base_path())}",
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

    def _configured_base_path(self) -> str:
        return resolve_base_path(self.config)

    def _inject_versions(self) -> None:
        vs_path = self.build_dir / "components" / "version-selector.tsx"
        if not vs_path.exists():
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
