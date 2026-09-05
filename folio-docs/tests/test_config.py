from pathlib import Path
import re
import warnings

import pytest
import yaml

from folio_docs.config import load_config


def test_load_config_from_file():
    fixture = Path(__file__).parent / "fixtures" / "docs.yaml"
    config = load_config(fixture)
    assert config.project_name == "TestProject"
    assert config.project_version == "1.0.0"
    assert config.project_repo == "https://github.com/test/test"
    assert config.project_repo_ref == "main"
    assert config.python_sources == ["src/"]
    assert config.python_excludes == ["src/tests/"]
    assert config.doc_sources == ["docs/"]
    assert config.output_dir == "_site"
    assert config.dark_mode is True
    assert config.theme_preset == "organic-editorial"
    assert config.nav == ["Introduction", "API Reference"]
    assert config.generate_llms_txt is True
    assert config.generate_llms_full_txt is True


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/docs.yaml"))


def test_load_config_minimal(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Minimal"

source:
  python:
    paths:
      - "src/"
"""
    )
    config = load_config(cfg_file)
    assert config.project_name == "Minimal"
    assert config.project_version == "0.0.0"
    assert config.output_dir == "_site"
    assert config.dark_mode is True
    assert config.theme_preset == "organic-editorial"
    assert config.nav == []
    assert config.generate_llms_txt is True
    assert config.landing_enabled is False
    assert config.landing_hero_variant == "docs-map"
    assert config.landing_comparison is False
    assert config.project_repo_ref == "main"
    assert config.docstring_style == "auto"


@pytest.mark.parametrize("section", ["project", "source", "theme", "llm"])
def test_load_config_rejects_non_mapping_core_sections(
    tmp_path: Path, section: str
):
    cfg_file = tmp_path / "docs.yaml"
    config = {"project": {"name": "Test"}, section: "not-a-mapping"}
    cfg_file.write_text(yaml.safe_dump(config))

    with pytest.raises(ValueError, match=rf"^{section} must be a mapping$"):
        load_config(cfg_file)


@pytest.mark.parametrize("project_name", ["", 42, None])
def test_load_config_defaults_invalid_project_name(
    tmp_path: Path, project_name: object
):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(yaml.safe_dump({"project": {"name": project_name}}))

    with pytest.warns(UserWarning, match="project.name must be a non-empty string"):
        config = load_config(cfg_file)

    assert config.project_name == "Untitled"


@pytest.mark.parametrize(
    ("config", "field"),
    [
        ({"source": {"docs": "docs"}}, "source.docs"),
        ({"source": {"python": {"paths": "src"}}}, "source.python.paths"),
        ({"source": {"python": {"exclude": "tests"}}}, "source.python.exclude"),
        ({"nav": "Guide"}, "nav"),
    ],
)
def test_load_config_rejects_strings_for_list_fields(
    tmp_path: Path, config: dict, field: str
):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(yaml.safe_dump({"project": {"name": "Test"}, **config}))

    with pytest.raises(ValueError, match=rf"^{re.escape(field)} must be a list"):
        load_config(cfg_file)


def test_load_config_theme_preset(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ThemeDocs"

theme:
  preset: "beacon"
  dark_mode: true
"""
    )
    config = load_config(cfg_file)
    assert config.theme_preset == "beacon"


def test_load_config_project_theme_contract(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ThemeDocs"

theme:
  preset: "p2pfl"
  name: "P2PFL"
  description: "Operational docs theme"
  scene: "Maintainers inspect experiments, nodes, and APIs in one compact surface."
  preview:
    light: "oklch(0.490 0.130 285)"
    dark: "oklch(0.720 0.100 285)"
  radius: "0.5rem"
  tune:
    font: "sans"
    accent: "ink"
    surface: "preset"
    shell: "flush"
    width: "wide"
    rhythm: "compact"
    borders: "fine"
    code: "terminal"
  style:
    "--content-max-width": "74rem"
    "--body-line-height": "1.58"
  tokens:
    light:
      "--background": "oklch(0.985 0.008 80)"
      "--foreground": "oklch(0.175 0.008 75)"
      "--status-running": "oklch(0.680 0.110 160)"
    dark:
      "--background": "oklch(0.155 0.010 75)"
      "--foreground": "oklch(0.950 0.008 80)"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.theme_preset == "p2pfl"
    assert config.theme_name == "P2PFL"
    assert config.theme_description == "Operational docs theme"
    assert config.theme_scene.startswith("Maintainers inspect")
    assert config.theme_preview == {
        "light": "oklch(0.490 0.130 285)",
        "dark": "oklch(0.720 0.100 285)",
    }
    assert config.theme_radius == "0.5rem"
    assert config.theme_tune == {
        "fontId": "sans",
        "colorId": "ink",
        "surfaceColorId": "preset",
        "shellPaddingId": "flush",
        "contentWidthId": "wide",
        "rhythmId": "compact",
        "borderId": "fine",
        "codeTreatmentId": "terminal",
    }
    assert config.theme_style == {
        "--content-max-width": "74rem",
        "--body-line-height": "1.58",
    }
    assert config.theme_tokens["light"]["--status-running"] == "oklch(0.680 0.110 160)"
    assert resolved.theme_tokens == config.theme_tokens
    assert resolved.theme_tune == config.theme_tune


def test_load_config_project_theme_variants_and_header_contract(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ThemeDocs"

theme:
  preset: "p2pfl"
  header:
    brand: "p2pfl"
    badge: "Web Services"
    repo: "https://github.com/pguijas/p2pfl"
    theme_toggle: true
    action_label: "Dashboard"
    action_href: "/dashboard"
    search: false
  variants:
    palette:
      label: "Palette"
      default: "default"
      options:
        default:
          label: "Default"
          swatch: "oklch(0.490 0.130 285)"
          preview:
            light: "oklch(0.490 0.130 285)"
            dark: "oklch(0.720 0.100 285)"
        midnight:
          label: "Midnight"
          swatch: "oklch(0.680 0.180 200)"
          preview:
            light: "oklch(0.480 0.160 200)"
            dark: "oklch(0.680 0.180 200)"
          tokens:
            light:
              "--background": "oklch(0.985 0.008 250)"
              "--primary": "oklch(0.480 0.160 200)"
            dark:
              "--background": "oklch(0.095 0.020 250)"
              "--primary": "oklch(0.680 0.180 200)"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.theme_header == {
        "brand": "p2pfl",
        "badge": "Web Services",
        "repo": "https://github.com/pguijas/p2pfl",
        "theme_toggle": True,
        "action_label": "Dashboard",
        "action_href": "/dashboard",
        "search": False,
    }
    assert config.theme_variants == {
        "palette": {
            "label": "Palette",
            "default": "default",
            "description": "",
            "options": {
                "default": {
                    "label": "Default",
                    "description": "",
                    "swatch": "oklch(0.490 0.130 285)",
                    "preview": {
                        "light": "oklch(0.490 0.130 285)",
                        "dark": "oklch(0.720 0.100 285)",
                    },
                    "style": {},
                    "tokens": {},
                },
                "midnight": {
                    "label": "Midnight",
                    "description": "",
                    "swatch": "oklch(0.680 0.180 200)",
                    "preview": {
                        "light": "oklch(0.480 0.160 200)",
                        "dark": "oklch(0.680 0.180 200)",
                    },
                    "style": {},
                    "tokens": {
                        "light": {
                            "--background": "oklch(0.985 0.008 250)",
                            "--primary": "oklch(0.480 0.160 200)",
                        },
                        "dark": {
                            "--background": "oklch(0.095 0.020 250)",
                            "--primary": "oklch(0.680 0.180 200)",
                        },
                    },
                },
            },
        },
    }
    assert resolved.theme_header == config.theme_header
    assert resolved.theme_variants == config.theme_variants


def test_load_config_rejects_unsafe_project_theme_tokens(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ThemeDocs"

theme:
  tokens:
    light:
      "background": "oklch(1 0 0)"
"""
    )

    with pytest.raises(ValueError, match="theme.tokens.light"):
        load_config(cfg_file)


@pytest.mark.parametrize("key", ["repo", "action_href"])
def test_load_config_rejects_unsafe_theme_header_href(tmp_path: Path, key: str):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "ThemeDocs"

theme:
  header:
    {key}: "javascript:alert(1)"
"""
    )

    with pytest.raises(ValueError, match=f"theme.header.{key}"):
        load_config(cfg_file)


def test_load_config_allows_relative_theme_header_href(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ThemeDocs"

theme:
  header:
    repo: "https://github.com/acme/docs"
    action_href: "/dashboard"
"""
    )

    config = load_config(cfg_file)
    assert config.theme_header["repo"] == "https://github.com/acme/docs"
    assert config.theme_header["action_href"] == "/dashboard"


@pytest.mark.parametrize(
    "repo",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
    ],
)
def test_load_config_rejects_unsafe_project_repo(tmp_path: Path, repo: str):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "ThemeDocs"
  repo: {repo!r}
"""
    )

    with pytest.raises(ValueError, match="project.repo"):
        load_config(cfg_file)


@pytest.mark.parametrize(
    "repo",
    [
        "https://github.com/acme/docs",
        "ssh://git@github.com/acme/docs.git",
        "git://github.com/acme/docs.git",
        "git+https://github.com/acme/docs.git",
        "git@github.com:acme/docs.git",
        "acme/docs",
    ],
)
def test_load_config_accepts_common_repo_url_forms(tmp_path: Path, repo: str):
    """Regression: project.repo accepts non-http(s) git URL forms verbatim."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "RepoDocs"
  repo: {repo!r}
"""
    )

    config = load_config(cfg_file)
    assert config.project_repo == repo


@pytest.mark.parametrize(
    "package",
    ["../outside", ".build", ".build/theme", "_site", "_site/theme"],
)
def test_resolve_paths_rejects_unsafe_theme_package(tmp_path: Path, package: str):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "ThemePackDocs"

theme:
  package: "{package}"
"""
    )

    config = load_config(cfg_file)
    with pytest.raises(ValueError, match="theme.package"):
        config.resolve_paths(tmp_path)


def test_resolve_paths_rejects_absolute_theme_package(tmp_path: Path):
    outside = tmp_path.parent / "evil-theme"
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "ThemePackDocs"

theme:
  package: "{outside}"
"""
    )

    config = load_config(cfg_file)
    with pytest.raises(ValueError, match="theme.package"):
        config.resolve_paths(tmp_path)


def test_load_config_template_path_and_params(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "TemplateDocs"

template:
  path: "docs-template"
  params:
    navbarVariant: "dense"
    productName: "Acme SDK"
    showBetaBadge: true
"""
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert not any("template" in str(warning.message) for warning in caught)
    assert config.template_path == "docs-template"
    assert config.template_params == {
        "navbarVariant": "dense",
        "productName": "Acme SDK",
        "showBetaBadge": True,
    }
    assert resolved.template_path == str(tmp_path / "docs-template")
    assert resolved.template_params == config.template_params


def test_load_config_template_overlay_path(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "OverlayDocs"

template:
  overlay_path: "overlay"
"""
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert not any("template" in str(warning.message) for warning in caught)
    assert config.template_overlay_path == "overlay"
    assert config.template_path == ""
    assert resolved.template_overlay_path == str(tmp_path / "overlay")


def test_template_overlay_path_ignored_when_template_path_set(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "OverlayDocs"

template:
  path: "docs-template"
  overlay_path: "overlay"
"""
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = load_config(cfg_file)

    # The full-replacement path wins; the overlay is dropped with a warning.
    assert config.template_path == "docs-template"
    assert config.template_overlay_path == ""
    assert any(
        "template.overlay_path is ignored when template.path is set"
        in str(warning.message)
        for warning in caught
    )


def test_template_params_absent_defaults_to_empty(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "TemplateDocs"

template:
  path: "docs-template"
"""
    )

    config = load_config(cfg_file)
    assert config.template_params == {}


def test_template_params_null_defaults_to_empty(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "TemplateDocs"

template:
  path: "docs-template"
  params: null
"""
    )

    config = load_config(cfg_file)
    assert config.template_params == {}


def test_template_params_non_mapping_warns_and_defaults_to_empty(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "TemplateDocs"

template:
  path: "docs-template"
  params:
    - dense
    - compact
"""
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = load_config(cfg_file)

    assert config.template_params == {}
    assert any(
        "template.params must be a mapping" in str(warning.message)
        for warning in caught
    )


def test_template_params_non_serializable_raises(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    # A YAML local tag that ``safe_load`` cannot resolve still parses to a
    # non-JSON-serializable object, so the params fail the contract.
    cfg_file.write_text(
        """
project:
  name: "TemplateDocs"

template:
  path: "docs-template"
  params:
    when: 2024-01-01
"""
    )

    with pytest.raises(ValueError, match="template.params must be JSON-serializable"):
        load_config(cfg_file)


def test_resolve_paths_deep_copies_template_params(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "TemplateDocs"

template:
  path: "docs-template"
  params:
    nested:
      flag: true
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert resolved.template_params == config.template_params

    # Mutating a nested value in the resolved config must not leak back into the
    # original config (parity with theme_variants deep-copy behavior).
    resolved.template_params["nested"]["flag"] = False
    assert config.template_params["nested"]["flag"] is True


def test_load_config_theme_package_path(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ThemePackDocs"

theme:
  package: "docs/theme/p2pfl"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.theme_package_path == "docs/theme/p2pfl"
    assert resolved.theme_package_path == str(tmp_path / "docs/theme/p2pfl")


def test_load_config_template_docs_route_base(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "RouteDocs"

template:
  docs_route_base: "/reference/docs/"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.docs_route_base == "/reference/docs"
    assert resolved.docs_route_base == "/reference/docs"


def test_load_config_project_repo_ref(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BranchDocs"
  repo: "https://github.com/acme/branch-docs"
  repo_ref: "release/2.x"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.project_repo_ref == "release/2.x"
    assert resolved.project_repo_ref == "release/2.x"


def test_load_config_deploy_settings(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "DeployDocs"

deploy:
  provider: "github-pages"
  base_path: "docs"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.deploy_provider == "github-pages"
    assert config.deploy_base_path == "/docs"
    assert resolved.deploy_provider == "github-pages"
    assert resolved.deploy_base_path == "/docs"


def test_load_config_sidebar_default_collapsed(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "CollapsedDocs"

sidebar:
  default_collapsed: true
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.sidebar_default_collapsed is True
    assert resolved.sidebar_default_collapsed is True


def test_load_config_sidebar_collapsed_by_default(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "DefaultDocs"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.sidebar_default_collapsed is True
    assert resolved.sidebar_default_collapsed is True


def test_load_config_sidebar_default_collapsed_opt_out(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ExpandedDocs"

sidebar:
  default_collapsed: false
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.sidebar_default_collapsed is False
    assert resolved.sidebar_default_collapsed is False


def test_load_config_landing_enabled_toggle(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "DocsOnly"

landing:
  enabled: false
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_enabled is False
    assert resolved.landing_enabled is False


def test_load_config_landing_hero_variant_is_applied(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "SourcePipeline"

landing:
  hero:
    variant: "source-pipeline"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_enabled is True
    assert config.landing_hero_variant == "source-pipeline"
    assert resolved.landing_hero_variant == "source-pipeline"


def test_load_config_landing_unknown_hero_variant_falls_back(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BadVariant"

landing:
  hero:
    variant: "hologram"
"""
    )

    config = load_config(cfg_file)

    assert config.landing_hero_variant == "docs-map"


def test_load_config_landing_empty_tagline_is_preserved(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoKicker"

landing:
  hero:
    tagline: ""
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_hero_tagline == ""
    assert resolved.landing_hero_tagline == ""


def test_load_config_without_landing_key_disables_landing(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text('project:\n  name: "DocsFirst"\n')

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_enabled is False
    assert resolved.landing_enabled is False


def test_load_config_landing_comparison_toggle(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoComparison"

landing:
  comparison: false
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_comparison is False
    assert resolved.landing_comparison is False


def test_load_config_landing_sections_catalog_is_applied(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Catalog"

landing:
  sections:
    - type: "stats"
      eyebrow: "Project scale"
      title: "Generated docs, measured"
      items:
        - value: "3"
          label: "commands"
        - value: "1"
          label: "config file"
    - type: "cta"
      title: "Start from the docs"
      actions:
        - title: "Read the docs"
          href: "/docs/"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert [section["type"] for section in config.landing_sections] == [
        "stats",
        "cta",
    ]
    assert resolved.landing_sections == config.landing_sections


def test_load_config_landing_build_pipeline_hero_variant_is_accepted(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BuildPipeline"

landing:
  hero:
    variant: "build-pipeline"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_hero_variant == "build-pipeline"
    assert resolved.landing_hero_variant == "build-pipeline"


def test_load_config_landing_heartbeat_hero_variant_is_accepted(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Heartbeat"

landing:
  hero:
    variant: "heartbeat"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_hero_variant == "heartbeat"
    assert resolved.landing_hero_variant == "heartbeat"


def test_load_config_landing_boards_section_defaults(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Boards"

landing:
  sections:
    - type: "boards"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["type"] == "boards"
    assert section["roadmap_url"] == "/roadmap"
    assert section["roadmap_link_text"] == "Full roadmap"
    assert section["narrow"] is False


def test_load_config_landing_boards_narrow_and_statement_size(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "CalmLanding"

landing:
  sections:
    - type: "boards"
      narrow: true
    - type: "statement"
      size: "md"
      text: "Thesis."
      description: "Lead paragraph."
    - type: "statement"
      size: "huge"
      text: "Closer."
"""
    )

    config = load_config(cfg_file)

    boards, thesis, closer = config.landing_sections
    assert boards["narrow"] is True
    assert thesis["size"] == "md"
    assert thesis["description"] == "Lead paragraph."
    # invalid size degrades to the default scale
    assert "size" not in closer


def test_load_config_landing_boards_section_unsafe_href_degrades(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BoardsUnsafe"

landing:
  sections:
    - type: "boards"
      roadmap_url: "javascript:alert(1)"
      title: 123
"""
    )

    with pytest.warns(UserWarning, match="roadmap_url"):
        config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["roadmap_url"] == "/roadmap"
    # Non-string heading fields degrade to absent, not crash.
    assert "title" not in section


def test_load_config_landing_cells_section_is_normalized(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Cells"

landing:
  sections:
    - type: "cells"
      items:
        - label: "Agents"
          title: "llms.txt output"
          description: "Every build emits llms.txt."
          href: "/llms.txt"
          link_text: "See this site's llms.txt"
          visual: "llms"
        - title: "No link cell"
          visual: "hologram"
        - description: "missing title, dropped"
        - "not-an-item"
        - title: "Unsafe"
          href: "javascript:alert(1)"
"""
    )

    with pytest.warns(UserWarning, match="Unsafe"):
        config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["items"] == [
        {
            "title": "llms.txt output",
            "label": "Agents",
            "description": "Every build emits llms.txt.",
            "link_text": "See this site's llms.txt",
            "visual": "llms",
            "href": "/llms.txt",
        },
        # Unknown vignette kinds are dropped; the cell itself survives.
        {"title": "No link cell", "label": "", "description": "", "link_text": ""},
        # The unsafe href is dropped; the cell itself survives.
        {"title": "Unsafe", "label": "", "description": "", "link_text": ""},
    ]


def test_load_config_landing_cells_section_tolerates_junk(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "CellsJunk"

landing:
  sections:
    - type: "cells"
      title: [1, 2]
      items: "not-a-list"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert "title" not in section
    assert section["items"] == []


def test_load_config_landing_mechanism_section_is_normalized(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Mechanism"

landing:
  sections:
    - type: "mechanism"
      code: |-
        source:
        + docs: ["docs/"]
      commits:
        - hash: "a3f92c1"
          message: "docs: move guide source"
        - "not-a-commit"
        - hash: 42
          message: 42
      pills: ["push", 7, "build"]
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["code_title"] == "docs.yaml"
    assert section["code"] == 'source:\n+ docs: ["docs/"]'
    assert section["commits"] == [
        {"hash": "a3f92c1", "message": "docs: move guide source"}
    ]
    assert section["pills"] == ["push", "build"]
    assert section["caption"] == ""


def test_load_config_landing_mechanism_section_defaults(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "MechanismDefaults"

landing:
  sections:
    - type: "mechanism"
      pills: "not-a-list"
      commits: "not-a-list"
      code: 42
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["pills"] == ["git push", "folio build", "deploy"]
    assert section["commits"] == []
    assert section["code"] == ""


def test_load_config_landing_statement_section_is_normalized(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Statement"

landing:
  sections:
    - type: "statement"
      text: "If it breaks, our own docs break first."
      accent: "our own docs"
      actions:
        - title: "Read the docs"
          href: "/docs"
        - title: "See the plan"
          href: "/roadmap"
        - title: "Broken"
          href: "javascript:alert(1)"
        - "not-an-action"
"""
    )

    with pytest.warns(UserWarning, match="Broken"):
        config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["text"] == "If it breaks, our own docs break first."
    assert section["accent"] == "our own docs"
    # Unsafe/malformed actions are dropped; the first kept one is primary.
    assert section["actions"] == [
        {"title": "Read the docs", "href": "/docs", "primary": True},
        {"title": "See the plan", "href": "/roadmap"},
    ]


def test_load_config_landing_statement_section_tolerates_junk(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "StatementJunk"

landing:
  sections:
    - type: "statement"
      text: [1, 2]
      accent: {a: 1}
      actions: "nope"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["text"] == ""
    assert section["accent"] == ""
    assert section["actions"] == []


def test_load_config_landing_funnel_section_defaults(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "FunnelDefaults"

landing:
  sections:
    - type: "funnel"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["type"] == "funnel"
    assert section["command"] == "folio build"
    assert section["command_notes"] == [
        "reads source · never runs it",
        "one build → every surface",
    ]
    assert section["caption"] == ""
    # Empty stays empty: the template renders its built-in folio defaults;
    # the plugin never injects them.
    assert section["inputs"] == []
    assert section["outputs"] == []
    assert section["guarantees"] == []


def test_load_config_landing_funnel_empty_command_notes_stay_empty(tmp_path: Path):
    """An explicit empty list suppresses the build node's gloss; only a missing
    key falls back to the bundled defaults."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "FunnelNoNotes"

landing:
  sections:
    - type: "funnel"
      command_notes: []
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["command_notes"] == []


def test_load_config_landing_funnel_section_is_normalized(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Funnel"

landing:
  sections:
    - type: "funnel"
      eyebrow: "The mechanism"
      title: "One build, every surface"
      caption: "FIG. 01 — the build funnel"
      command: "folio build --strict"
      command_notes:
        - "reads source only"
        - 42
      inputs:
        - label: "docstrings"
          detail: "parsed, never executed"
          chip: "roadmap 0.9"
        - label: "docs/*.md"
          ghost: true
        - label: "maybe.ts"
          ghost: "yes"
        - detail: "missing label, dropped"
        - "not-an-input"
      outputs:
        - label: "site/"
          detail: "static HTML"
        - detail: "missing label, dropped"
      guarantees:
        - title: "Deterministic"
          detail: "same source, same site"
        - detail: "missing title, dropped"
        - "not-a-guarantee"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    (section,) = config.landing_sections
    assert section["command"] == "folio build --strict"
    assert section["command_notes"] == ["reads source only"]
    assert section["caption"] == "FIG. 01 — the build funnel"
    assert section["inputs"] == [
        {
            "label": "docstrings",
            "detail": "parsed, never executed",
            "ghost": False,
            "chip": "roadmap 0.9",
        },
        {"label": "docs/*.md", "detail": "", "ghost": True},
        # ghost is coerced strictly: only a boolean true counts.
        {"label": "maybe.ts", "detail": "", "ghost": False},
    ]
    assert section["outputs"] == [{"label": "site/", "detail": "static HTML"}]
    assert section["guarantees"] == [
        {"title": "Deterministic", "detail": "same source, same site"}
    ]
    assert resolved.landing_sections == config.landing_sections


def test_load_config_landing_section_actions_are_normalized(tmp_path: Path):
    """``actions`` is a shared section field, so every section type must
    normalize it.

    ``cta`` had no entry in the normalizer table, so its actions reached the
    template exactly as written. An action without ``href`` then dereferenced
    ``undefined.startsWith`` in ``normalizeAction`` and aborted ``next build``.
    """
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Actions"
landing:
  sections:
    - type: "cta"
      title: "Next"
      actions:
        - title: "Explore the docs"
          href: "/docs"
          primary: true
        - title: "Missing href, dropped"
        - href: "/no-title-dropped"
        - title: "Unsafe scheme"
          href: "javascript:alert(1)"
        - "not-a-mapping"
""",
        encoding="utf-8",
    )

    with pytest.warns(UserWarning):
        config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["actions"] == [
        {"title": "Explore the docs", "href": "/docs", "primary": True},
    ]


def test_load_config_landing_funnel_icons_are_whitelisted(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "FunnelIcons"

landing:
  sections:
    - type: "funnel"
      inputs:
        - label: "folio/**/*.py"
          icon: "python"
        - label: "mystery"
          icon: "not-a-mark"
        - label: "wrong-type"
          icon: 7
      outputs:
        - label: "_site/"
          icon: "folder"
        - label: "elsewhere"
          icon: "nope"
      guarantees:
        - title: "Read, never run."
          icon: "python"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["inputs"] == [
        {"label": "folio/**/*.py", "detail": "", "ghost": False, "icon": "python"},
        # Unknown and non-string marks drop rather than reaching the template,
        # where an undefined icon would throw at render.
        {"label": "mystery", "detail": "", "ghost": False},
        {"label": "wrong-type", "detail": "", "ghost": False},
    ]
    assert section["outputs"] == [
        {"label": "_site/", "detail": "", "icon": "folder"},
        {"label": "elsewhere", "detail": ""},
    ]
    # Guarantees are apparatus copy, not diagram nodes: no marks.
    assert section["guarantees"] == [{"title": "Read, never run.", "detail": ""}]


def test_load_config_landing_harness_section_is_normalized(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Harness"

landing:
  sections:
    - type: "harness"
      thesis: "A harness over harnesses."
      docs_label: "Folio Docs"
      docs_detail: 42
      agents_label: "Folio for Agents"
      agents_detail: "Shared project state."
      harnesses:
        - label: "Coding agents"
          detail: "work in the checkout"
        - detail: "missing label, dropped"
        - "not-a-node"
      unifies:
        - label: "Context"
        - label: "Rules"
          detail: "contracts in the repo"
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    (section,) = config.landing_sections
    assert section["type"] == "harness"
    assert section["thesis"] == "A harness over harnesses."
    assert section["docs_label"] == "Folio Docs"
    assert "docs_detail" not in section
    assert section["agents_label"] == "Folio for Agents"
    assert section["agents_detail"] == "Shared project state."
    assert section["harnesses"] == [
        {
            "label": "Coding agents",
            "detail": "work in the checkout",
        }
    ]
    assert section["unifies"] == [
        {"label": "Context", "detail": ""},
        {"label": "Rules", "detail": "contracts in the repo"},
    ]
    assert resolved.landing_sections == config.landing_sections


def test_load_config_landing_features_variant_and_visuals(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "FeaturesBento"

landing:
  sections:
    - type: "features"
      variant: "bento"
      features:
        - title: "Receipts"
          description: "Build output, itemized."
          visual: "receipt"
        - title: "No vignette"
          visual: "sparkles"
    - type: "features"
      variant: "grid"
"""
    )

    config = load_config(cfg_file)

    bento, legacy = config.landing_sections
    assert bento["variant"] == "bento"
    receipt, plain = bento["features"]
    assert receipt["visual"] == "receipt"
    # Unknown vignette kinds are dropped; the card renders copy-only.
    assert "visual" not in plain
    # Unknown variants degrade to absent (legacy rows layout).
    assert "variant" not in legacy


def test_load_config_landing_stage_labels(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Staged"

landing:
  hero:
    stage: "  The premise  "
  sections:
    - type: "statement"
      stage: "The mechanism"
      text: "Thesis."
    - type: "boards"
      stage: ""
    - type: "cta"
      stage: 42
"""
    )

    config = load_config(cfg_file)

    assert config.extra["landing"]["hero"]["stage"] == "The premise"
    statement, boards, cta = config.landing_sections
    assert statement["stage"] == "The mechanism"
    # Blank and non-string stages degrade to absent: no stage rail renders.
    assert "stage" not in boards
    assert "stage" not in cta


def test_load_config_landing_hero_without_stage_stays_bare(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Unstaged"

landing:
  hero:
    headline: "No stage rail"
"""
    )

    config = load_config(cfg_file)

    assert "stage" not in config.extra["landing"]["hero"]


def test_config_resolve_paths(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Test"

source:
  python:
    paths:
      - "src/"
  docs:
    - "docs/"

output: "out"
"""
    )
    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)
    assert resolved.python_sources == [str(tmp_path / "src")]
    assert resolved.doc_sources == [str(tmp_path / "docs")]
    assert resolved.output_dir == str(tmp_path / "out")


@pytest.mark.parametrize("output", ["../outside", ".", ""])
def test_config_resolve_paths_rejects_unsafe_output(
    tmp_path: Path,
    output: str,
) -> None:
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f'project:\n  name: "Test"\noutput: "{output}"\n',
        encoding="utf-8",
    )

    config = load_config(cfg_file)

    with pytest.raises(ValueError, match="Output directory"):
        config.resolve_paths(tmp_path)


def test_config_resolve_paths_rejects_absolute_output(tmp_path: Path) -> None:
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f'project:\n  name: "Test"\noutput: "{tmp_path / "outside"}"\n',
        encoding="utf-8",
    )

    config = load_config(cfg_file)

    with pytest.raises(ValueError, match="Output directory"):
        config.resolve_paths(tmp_path)


@pytest.mark.parametrize(
    "output, expected",
    [
        # The build rmtree's output_dir after a successful export, so an
        # output that *is* a source directory destroys the sources it just
        # read - and `output: docs` is a plausible typo next to the
        # documented `source.docs: ["docs/"]` default.
        ("docs", "source directory"),
        ("src", "source directory"),
        # An output that is an *ancestor* of a source directory takes the
        # source down with it.
        (".", "Output directory"),
        # Nothing may put the repository itself in the blast radius.
        (".git", "must not"),
    ],
)
def test_config_resolve_paths_rejects_output_that_would_delete_sources(
    tmp_path: Path,
    output: str,
    expected: str,
) -> None:
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        "project:\n"
        '  name: "Test"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "src/"\n'
        "  docs:\n"
        '    - "docs/"\n'
        f'output: "{output}"\n',
        encoding="utf-8",
    )

    config = load_config(cfg_file)

    with pytest.raises(ValueError, match=expected):
        config.resolve_paths(tmp_path)


def test_config_resolve_paths_allows_output_beside_the_sources(
    tmp_path: Path,
) -> None:
    """The guard must not break the normal layout or a rebuild into _site."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        "project:\n"
        '  name: "Test"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "src/"\n'
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )
    (tmp_path / "_site").mkdir()

    resolved = load_config(cfg_file).resolve_paths(tmp_path)

    assert resolved.output_dir == str(tmp_path / "_site")


def test_load_config_i18n_is_ignored(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "I18nProject"

source:
  python:
    paths:
      - "src/"

i18n:
  default_locale: "en"
  locales:
    - code: "en"
      name: "English"
    - code: "es"
      name: "Espanol"
"""
    )
    config = load_config(cfg_file)
    assert config.i18n_default_locale == ""
    assert config.i18n_locales == []


def test_load_config_no_i18n(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoI18n"

source:
  python:
    paths:
      - "src/"
"""
    )
    config = load_config(cfg_file)
    assert config.i18n_default_locale == ""
    assert config.i18n_locales == []


def test_load_config_mvp_ignores_experimental_keys_but_loads_plugins(
    tmp_path: Path,
):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "MvpProject"

plugins:
  - "folio_docs.docs.integrations.roadmap"

components:
  - "docs/components"

i18n:
  default_locale: "en"
  locales:
    - code: "en"
      name: "English"

landing:
  enabled: true

roadmap:
  phases:
    - id: "foundation"
      title: "Foundation"

versions:
  - label: "latest"
    path: "latest"
"""
    )

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        config = load_config(cfg_file)

    # Plugins and components are released: both keys load without a warning;
    # the remaining experimental keys are still silently ignored.
    assert [str(record.message) for record in records] == []
    assert config.plugins == ["folio_docs.docs.integrations.roadmap"]
    assert config.component_dirs == ["docs/components"]
    assert config.component_specs == []
    assert config.i18n_default_locale == ""
    assert config.i18n_locales == []
    # The landing plugin is released: its `landing:` section applies.
    assert config.landing_enabled is True
    # The roadmap plugin is released: it loads (as a default plugin, deduped
    # against the explicit listing) and claims its config key.
    assert config.extra["roadmap"]["phases"][0]["id"] == "foundation"
    assert config.versions == []


def test_load_config_search_defaults(tmp_path: Path):
    """Search is enabled with no placeholder by default."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoSearch"

source:
  python:
    paths:
      - "src/"
"""
    )
    config = load_config(cfg_file)
    assert config.search_enabled is True
    assert config.search_placeholder == ""


def test_load_config_search_disabled(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "SearchOff"

search:
  enabled: false
"""
    )
    config = load_config(cfg_file)
    assert config.search_enabled is False
    assert config.search_placeholder == ""


def test_load_config_search_placeholder(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "CustomSearch"

search:
  enabled: true
  placeholder: "Search the docs..."
"""
    )
    config = load_config(cfg_file)
    assert config.search_enabled is True
    assert config.search_placeholder == "Search the docs..."


def test_load_config_file_plugin_paths_are_relative_to_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "local_plugin.py").write_text(
        "from folio_docs.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def config_keys():\n"
        "    return ['local_value']\n"
        "\n"
        "@hookimpl\n"
        "def configure(config, raw_config):\n"
        "    config.extra['local_value'] = raw_config['local_value']\n",
        encoding="utf-8",
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "PluginProject"

plugins:
  - "./plugins/local_plugin.py"

local_value: "loaded"
""",
        encoding="utf-8",
    )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    config = load_config(cfg_file)

    # The plugin path resolves against the config file, not the cwd.
    assert config.plugins == ["./plugins/local_plugin.py"]
    assert config.extra["local_value"] == "loaded"


def test_load_config_without_plugins_key_does_not_warn_about_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text('project:\n  name: "NoPlugins"\n', encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config = load_config(cfg_file)

    assert config.plugins == []


def test_config_plugins_load_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "local_plugin.py").write_text(
        "from folio_docs.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def config_keys():\n"
        "    return ['local_value']\n"
        "\n"
        "@hookimpl\n"
        "def configure(config, raw_config):\n"
        "    config.extra['local_value'] = raw_config['local_value']\n",
        encoding="utf-8",
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "PluginProject"

plugins:
  - "./plugins/local_plugin.py"

local_value: "loaded"
""",
        encoding="utf-8",
    )

    config = load_config(cfg_file)

    assert config.plugins == ["./plugins/local_plugin.py"]
    assert config.extra["local_value"] == "loaded"


def test_configure_hook_sees_absolute_project_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plugins must see config.project_dir during configure (before resolve_paths)."""
    monkeypatch.delenv("FOLIO_EXPERIMENTAL", raising=False)
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "dir_plugin.py").write_text(
        "from folio_docs.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def configure(config, raw_config):\n"
        "    config.extra['seen_project_dir'] = config.project_dir\n",
        encoding="utf-8",
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "PluginProject"

plugins:
  - "./plugins/dir_plugin.py"
""",
        encoding="utf-8",
    )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    config = load_config(cfg_file)

    assert config.extra["seen_project_dir"] == str(tmp_path.resolve())
    # resolve_paths keeps the same absolute directory (idempotent).
    resolved = config.resolve_paths(tmp_path)
    assert resolved.project_dir == str(tmp_path.resolve())


def test_load_config_roadmap_plugin_claims_roadmap_key(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "RoadmapProject"

plugins:
  - "folio_docs.docs.integrations.roadmap"

roadmap:
  routes:
    docs: true
    public: true
  phases:
    - id: "foundation"
      version: "0.1"
      title: "Foundation"
      status: "shipped"
      layer: "Source analysis"
      summary: "Parse source files into docs."
      command: "folio build"
      features:
        - "Parser"
        - "Search"
"""
    )

    config = load_config(cfg_file)

    assert config.plugins == ["folio_docs.docs.integrations.roadmap"]
    assert config.extra["roadmap"]["phases"][0]["id"] == "foundation"


def test_default_roadmap_plugin_loads_without_plugins_entry(tmp_path: Path):
    """Default plugins are always loaded: `roadmap:` activates the plugin
    with no `plugins:` entry and no unknown-key warning."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "DefaultPluginProject"

roadmap:
  phases:
    - id: "foundation"
      title: "Foundation"
"""
    )

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        config = load_config(cfg_file)

    assert [str(record.message) for record in records] == []
    assert config.plugins == []
    assert config.extra["roadmap"]["phases"][0]["id"] == "foundation"
    assert config.extra["roadmap"]["routes"] == {"docs": True, "public": False}


def test_default_plugin_explicit_listing_is_not_double_registered(tmp_path: Path):
    from folio_docs.config import load_config_with_plugins

    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "DedupProject"

plugins:
  - "folio_docs.docs.integrations.roadmap"

roadmap:
  phases: []
"""
    )

    config, pm = load_config_with_plugins(cfg_file)

    registered = [getattr(plugin, "__name__", "") for plugin in pm.pm.get_plugins()]
    assert registered.count("folio_docs.docs.integrations.roadmap") == 1
    # A single config_keys() hookimpl answers per default plugin.
    assert sorted(pm.call_isolated("config_keys")) == [["landing"], ["roadmap"]]
    assert config.plugins == ["folio_docs.docs.integrations.roadmap"]


def test_project_plugin_configure_overrides_default_landing_plugin(tmp_path: Path):
    """Default plugins parse their config keys first (tryfirst), so a project
    plugin's configure() runs after them and its landing_* overrides stick."""
    from folio_docs.config import load_config_with_plugins

    (tmp_path / "enable_plugin.py").write_text(
        "from folio_docs.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def configure(config, raw_config):\n"
        "    config.landing_enabled = True\n"
        "    config.landing_hero_headline = 'From plugin'\n",
        encoding="utf-8",
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "OverrideProject"

plugins:
  - "./enable_plugin.py"
""",
        encoding="utf-8",
    )

    config, _pm = load_config_with_plugins(cfg_file)

    # No `landing:` key: the default landing plugin forces landing off, but
    # the project plugin runs after it and re-enables it.
    assert config.landing_enabled is True
    assert config.landing_hero_headline == "From plugin"


def test_project_plugin_configure_can_disable_yaml_enabled_landing(tmp_path: Path):
    from folio_docs.config import load_config_with_plugins

    (tmp_path / "disable_plugin.py").write_text(
        "from folio_docs.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def configure(config, raw_config):\n"
        "    config.landing_enabled = False\n",
        encoding="utf-8",
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "StagingProject"

landing:
  hero:
    headline: "From YAML"

plugins:
  - "./disable_plugin.py"
""",
        encoding="utf-8",
    )

    config, _pm = load_config_with_plugins(cfg_file)

    # The default plugin parsed `landing:` first; a project plugin that
    # force-disables the landing page (e.g. staging builds) is not overridden.
    assert config.landing_enabled is False
    assert config.landing_hero_headline == "From YAML"


def test_load_config_rejects_non_list_plugins(tmp_path: Path):
    """`plugins: my_plugin` (scalar instead of list) must fail the build
    loudly instead of silently never loading the user's plugin."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ScalarPlugins"

plugins: "my_plugin"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="plugins: must be a YAML list"):
        load_config(cfg_file)


def test_load_config_tolerates_empty_plugins_key(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "EmptyPlugins"

plugins:
""",
        encoding="utf-8",
    )

    config = load_config(cfg_file)

    assert config.plugins == []


def test_default_plugin_load_failure_degrades_to_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """A broken default plugin must not take down builds of projects that
    never asked for it (no `plugins:` key, no landing:/roadmap: section)."""
    import importlib

    real_import = importlib.import_module

    def broken_import(name, *args, **kwargs):
        if name == "folio_docs.docs.integrations.landing":
            raise ImportError("broken install")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", broken_import)

    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoPlugins"
""",
        encoding="utf-8",
    )

    with pytest.warns(UserWarning, match="Skipping default plugin"):
        config = load_config(cfg_file)

    assert config.project_name == "NoPlugins"


def test_default_plugin_is_inert_without_its_config_key(tmp_path: Path):
    from folio_docs.config import load_config_with_plugins, plugin_config_keys

    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoRoadmapProject"
"""
    )

    config, pm = load_config_with_plugins(cfg_file)

    # Loaded (its config key is claimed) but inert: no extra entry is written.
    assert "roadmap" in plugin_config_keys(pm)
    assert "roadmap" not in config.extra


def test_load_config_parses_component_dirs_and_named_specs(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ComponentProject"

components:
  - "docs/components"
  - name: "Hero"
    from: "docs/components/hero.tsx"
    export: "Hero"
    expose:
      mdx: true
      landing: true
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.component_dirs == ["docs/components"]
    # Unknown expose keys (landing) are dropped; mdx is preserved.
    assert config.component_specs == [
        {
            "name": "Hero",
            "from": "docs/components/hero.tsx",
            "export": "Hero",
            "expose": {"mdx": True},
        }
    ]
    # resolve_paths anchors both forms to the project directory.
    assert resolved.component_dirs == [str(tmp_path / "docs/components")]
    assert resolved.component_specs[0]["from"] == str(
        tmp_path / "docs/components/hero.tsx"
    )


def test_load_config_rejects_malformed_components_entries(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ComponentProject"

components:
  - 42
"""
    )

    with pytest.raises(ValueError, match="components entries must be"):
        load_config(cfg_file)


def test_load_config_rejects_non_list_components(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "ComponentProject"

components: "docs/components"
"""
    )

    with pytest.raises(ValueError, match="components must be a list"):
        load_config(cfg_file)


def test_load_config_does_not_model_template_overrides(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "OverrideProject"

overrides: "docs/overrides"
"""
    )

    with pytest.warns(UserWarning, match="overrides"):
        config = load_config(cfg_file)

    assert not hasattr(config, "override_dir")


def test_config_uses_shared_tune_contract():
    from folio_docs import config
    from folio_docs.schemas import theme_contract as tc

    assert config._THEME_TUNE_KEYS is tc.THEME_TUNE_KEYS
    assert config._THEME_TUNE_ALIASES is tc.THEME_TUNE_ALIASES


@pytest.mark.parametrize("value", ["/..", "/../../x", "/a/../b", "/docs/.", "/./docs"])
def test_normalize_docs_route_base_rejects_traversal(value: str):
    from folio_docs.config import normalize_docs_route_base

    with pytest.raises(ValueError, match="cannot contain '.' or '..'"):
        normalize_docs_route_base(value)


def test_normalize_docs_route_base_happy_path_intact():
    from folio_docs.config import normalize_docs_route_base

    assert normalize_docs_route_base("/reference/docs/") == "/reference/docs"


def test_load_config_rejects_docs_route_base_traversal(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "TraversalDocs"

template:
  docs_route_base: "/a/../b"
"""
    )

    with pytest.raises(ValueError, match="cannot contain '.' or '..'"):
        load_config(cfg_file)


def test_theme_header_warns_on_unknown_key():
    from folio_docs.config import _theme_header

    with pytest.warns(UserWarning, match="Unknown theme.header key 'bogus'"):
        header = _theme_header({"brand": "Acme", "bogus": "x"})

    assert header == {"brand": "Acme"}


def test_theme_header_known_keys_do_not_warn():
    from folio_docs.config import _theme_header

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        header = _theme_header(
            {"brand": "Acme", "theme_toggle": True, "action_href": "/x"}
        )

    assert header == {"brand": "Acme", "theme_toggle": True, "action_href": "/x"}


def test_theme_preview_warns_on_unknown_key():
    from folio_docs.config import _theme_preview

    with pytest.warns(UserWarning, match="Unknown theme.preview key 'bogus'"):
        preview = _theme_preview({"light": "oklch(0.5 0 0)", "bogus": "x"})

    assert preview == {"light": "oklch(0.5 0 0)"}


def test_theme_preview_known_keys_do_not_warn():
    from folio_docs.config import _theme_preview

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        preview = _theme_preview({"light": "l", "dark": "d"})

    assert preview == {"light": "l", "dark": "d"}


def _variants_with_option_counts(*counts: int) -> dict:
    return {
        f"control{index}": {
            "options": {f"opt{option}": {} for option in range(count)},
        }
        for index, count in enumerate(counts)
    }


def test_theme_variants_combination_limit_boundary_ok():
    from folio_docs.config import _theme_variants

    # 4 controls x 4 options = 256 combinations: exactly at the limit.
    variants = _theme_variants(_variants_with_option_counts(4, 4, 4, 4))
    assert len(variants) == 4


def test_theme_variants_combination_limit_exceeded():
    from folio_docs.config import _theme_variants

    # A single control with 257 options exceeds the 256-combination limit.
    with pytest.raises(ValueError, match=r"257 option combinations.*limit of 256"):
        _theme_variants(_variants_with_option_counts(257))


def test_theme_variants_combination_limit_exceeded_across_controls():
    from folio_docs.config import _theme_variants

    # 6 controls x 5 options = 15625 combinations.
    with pytest.raises(ValueError, match=r"15625 option combinations.*limit of 256"):
        _theme_variants(_variants_with_option_counts(5, 5, 5, 5, 5, 5))


@pytest.mark.parametrize("radius", ["0", "0.3rem", "0.5rem", "0.75rem", "1rem"])
def test_load_config_accepts_valid_theme_radius(tmp_path: Path, radius: str):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "RadiusDocs"

theme:
  radius: "{radius}"
"""
    )

    config = load_config(cfg_file)
    assert config.theme_radius == radius


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("none", "0"),
        ("sm", "0.3rem"),
        ("md", "0.5rem"),
        ("lg", "0.75rem"),
        ("full", "1rem"),
        ("SM", "0.3rem"),
    ],
)
def test_load_config_maps_named_theme_radius_aliases(
    tmp_path: Path, alias: str, expected: str
):
    """Legacy docs published named radii (e.g. tune: {radius: "sm"});
    they must keep loading and map onto the fixed scale."""
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "RadiusDocs"

theme:
  radius: "{alias}"
"""
    )

    config = load_config(cfg_file)
    assert config.theme_radius == expected


def test_load_config_maps_named_theme_tune_radius_alias(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "RadiusDocs"

theme:
  tune:
    radius: "sm"
"""
    )

    config = load_config(cfg_file)
    assert config.theme_radius == "0.3rem"


@pytest.mark.parametrize("radius", ["0.4rem", "2rem", "8px", "medium"])
def test_load_config_rejects_unknown_theme_radius(tmp_path: Path, radius: str):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        f"""
project:
  name: "RadiusDocs"

theme:
  radius: "{radius}"
"""
    )

    with pytest.raises(ValueError, match="theme.radius must be one of"):
        load_config(cfg_file)


def test_load_config_rejects_unknown_theme_tune_radius_alias(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "RadiusDocs"

theme:
  tune:
    radius: "0.4rem"
"""
    )

    with pytest.raises(ValueError, match="theme.radius must be one of"):
        load_config(cfg_file)


def test_load_config_theme_radius_defaults_to_empty(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "RadiusDocs"
"""
    )

    config = load_config(cfg_file)
    assert config.theme_radius == ""


def test_resolve_contained_dir_happy_path(tmp_path: Path):
    from folio_docs.paths import resolve_contained_dir

    target = tmp_path / "docs" / "theme"
    target.mkdir(parents=True)

    resolved = resolve_contained_dir(
        "docs/theme", tmp_path, tmp_path / "_site", "theme.package"
    )
    assert resolved == target.resolve()


def test_resolve_contained_dir_must_exist(tmp_path: Path):
    from folio_docs.paths import resolve_contained_dir

    with pytest.raises(FileNotFoundError, match="theme.package does not exist"):
        resolve_contained_dir(
            "missing", tmp_path, tmp_path / "_site", "theme.package", must_exist=True
        )

    resolved = resolve_contained_dir(
        "missing", tmp_path, tmp_path / "_site", "theme.package", must_exist=False
    )
    assert resolved == (tmp_path / "missing").resolve()


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ("../outside", "must stay within the project directory"),
        (".build/theme", "cannot point inside the .build directory"),
        ("_site/theme", "cannot point inside the output directory"),
    ],
)
def test_resolve_contained_dir_rejects_escapes(tmp_path: Path, raw: str, message: str):
    from folio_docs.paths import resolve_contained_dir

    with pytest.raises(ValueError, match=f"template.path {message}"):
        resolve_contained_dir(
            raw, tmp_path, tmp_path / "_site", "template.path", must_exist=False
        )


def test_load_config_landing_bento_header_fields(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BentoHeader"

landing:
  sections:
    - type: "features"
      variant: "bento"
      title: "Strong beat."
      title_muted: "Muted beat."
      actions:
        - title: "Explore"
          href: "/docs"
        - title: "Bad"
          href: "javascript:alert(1)"
      features:
        - title: "A"
          description: "d"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["title_muted"] == "Muted beat."
    assert section["actions"] == [{"title": "Explore", "href": "/docs"}]


def test_load_config_landing_bento_header_fields_degrade(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BentoHeaderDegrade"

landing:
  sections:
    - type: "features"
      variant: "bento"
      title_muted: 42
      actions: "nope"
      features:
        - title: "A"
          description: "d"
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert "title_muted" not in section
    assert section["actions"] == []


def test_load_config_landing_hero_notice(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoticeDocs"

landing:
  hero:
    notice:
      text: "New — v1.2 released"
      link: "/docs/changelog"
"""
    )

    config = load_config(cfg_file)

    assert config.landing_notice_text == "New — v1.2 released"
    assert config.landing_notice_link == "/docs/changelog"


def test_load_config_landing_hero_notice_list_rotates(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoticeList"

landing:
  hero:
    notice:
      text:
        - "v0.3 shipped"
        - ""
        - "Two products now"
      link: "/roadmap"
"""
    )

    config = load_config(cfg_file)

    assert config.landing_notice_text == ["v0.3 shipped", "Two products now"]
    assert config.landing_notice_link == "/roadmap"


def test_load_config_landing_hero_notice_list_caps_at_three(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoticeCap"

landing:
  hero:
    notice:
      text: ["one", "two", "three", "four"]
"""
    )

    with pytest.warns(UserWarning, match="cap at three"):
        config = load_config(cfg_file)

    assert config.landing_notice_text == ["one", "two", "three"]


def test_load_config_landing_hero_notice_single_item_list_is_plain(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoticeSingle"

landing:
  hero:
    notice:
      text: ["only message"]
"""
    )

    config = load_config(cfg_file)

    assert config.landing_notice_text == "only message"


def test_load_config_landing_hero_notice_degrades(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoticeDegrade"

landing:
  hero:
    notice:
      text: ""
      link: "javascript:alert(1)"
"""
    )

    config = load_config(cfg_file)

    assert config.landing_notice_text == ""
    assert config.landing_notice_link == ""


def test_load_config_landing_comparison_table_normalizes(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "OwnTable"

landing:
  comparison:
    caption: "  Capability  "
    tools: ["Ours", "  Theirs  ", "", 42]
    rows:
      - feature: "  Static export  "
        values: [true, "no"]
        note: "  both ship files  "
      - feature: "Partial states"
        values: ["~", ~]
      - feature: "Word forms"
        values: ["YES", "False"]
"""
    )

    config = load_config(cfg_file)
    resolved = config.resolve_paths(tmp_path)

    assert config.landing_comparison == {
        "caption": "Capability",
        "tools": ["Ours", "Theirs"],
        "rows": [
            {
                "feature": "Static export",
                "values": [True, False],
                "note": "both ship files",
            },
            {"feature": "Partial states", "values": ["~", "~"]},
            {"feature": "Word forms", "values": [True, False]},
        ],
    }
    assert resolved.landing_comparison == config.landing_comparison


def test_load_config_landing_comparison_drops_malformed_rows(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Malformed"

landing:
  comparison:
    tools: ["Ours", "Theirs"]
    rows:
      - feature: "Kept"
        values: [true, false]
      - feature: "Too few values"
        values: [true]
      - values: [true, true]
      - feature: "Values are not a list"
        values: "true"
      - "not-a-row"
"""
    )

    with pytest.warns(UserWarning, match="Too few values"):
        config = load_config(cfg_file)

    assert config.landing_comparison == {
        "caption": "",
        "tools": ["Ours", "Theirs"],
        "rows": [{"feature": "Kept", "values": [True, False]}],
    }


def test_load_config_landing_comparison_without_usable_table_is_off(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "NoTable"

landing:
  comparison:
    caption: "Capability"
    tools: []
"""
    )

    with pytest.warns(UserWarning, match="comparison needs a `tools:` list"):
        config = load_config(cfg_file)

    assert config.landing_comparison is False


def test_load_config_landing_comparison_bool_still_works_and_warns(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "LegacyBool"

landing:
  comparison: true
"""
    )

    with pytest.warns(UserWarning, match="deprecated and will be removed") as caught:
        config = load_config(cfg_file)

    assert config.landing_comparison is True
    message = str(caught[0].message)
    assert "`comparison: true`" in message
    assert "tools: [...]" in message
    assert "rows: [{feature, values: [...], note}]" in message


def test_load_config_landing_comparison_section_carries_its_own_table(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "SectionTable"

landing:
  sections:
    - type: "comparison"
      title: "Where this fits"
      caption: "Capability"
      tools: ["Ours", "Theirs"]
      rows:
        - feature: "Runs offline"
          values: [true, false]
"""
    )

    config = load_config(cfg_file)

    (section,) = config.landing_sections
    assert section["title"] == "Where this fits"
    assert section["caption"] == "Capability"
    assert section["tools"] == ["Ours", "Theirs"]
    assert section["rows"] == [{"feature": "Runs offline", "values": [True, False]}]


def test_load_config_landing_comparison_section_without_table_warns(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "BareSection"

landing:
  sections:
    - type: "comparison"
      caption: "Capability"
"""
    )

    with pytest.warns(UserWarning, match="deprecated and will be removed"):
        config = load_config(cfg_file)

    (section,) = config.landing_sections
    # The keys are dropped so the template falls back to the bundled matrix
    # instead of rendering an empty table shell.
    assert "caption" not in section
    assert "tools" not in section
    assert "rows" not in section


def test_load_config_landing_comparison_false_stays_off(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "Off"

landing:
  comparison: false
  sections:
    - type: "features"
      features:
        - title: "A"
          description: "d"
"""
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        config = load_config(cfg_file)

    assert config.landing_comparison is False
