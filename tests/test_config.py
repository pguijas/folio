from pathlib import Path
import warnings

import pytest

from folio.config import load_config


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


def test_load_config_landing_hero_variant_is_ignored(tmp_path: Path):
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

    assert config.landing_hero_variant == "docs-map"
    assert resolved.landing_hero_variant == "docs-map"


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


def test_load_config_landing_sections_catalog_is_ignored(tmp_path: Path):
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

    assert config.landing_sections == []
    assert resolved.landing_sections == config.landing_sections


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


def test_load_config_mvp_silently_ignores_experimental_keys(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "MvpProject"

plugins:
  - "folio.plugins.roadmap"

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

    assert records == []
    assert config.plugins == []
    assert config.component_dirs == []
    assert config.component_specs == []
    assert config.i18n_default_locale == ""
    assert config.i18n_locales == []
    assert config.landing_enabled is False
    assert "roadmap" not in config.extra
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
        "from folio.plugin import hookimpl\n"
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

    assert config.plugins == []
    assert "local_value" not in config.extra


def test_disabled_plugins_do_not_load_plugin_config_keys(
    tmp_path: Path,
) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "bad_plugin.py").write_text(
        "from folio.plugin import hookimpl\n"
        "\n"
        "@hookimpl\n"
        "def config_keys():\n"
        "    return 'roadmap'\n",
        encoding="utf-8",
    )
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "PluginProject"

plugins:
  - "./plugins/bad_plugin.py"
""",
        encoding="utf-8",
    )

    config = load_config(cfg_file)

    assert config.plugins == []


def test_load_config_roadmap_phases_are_ignored(tmp_path: Path):
    cfg_file = tmp_path / "docs.yaml"
    cfg_file.write_text(
        """
project:
  name: "RoadmapProject"

plugins:
  - "folio.plugins.roadmap"

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

    assert config.plugins == []
    assert "roadmap" not in config.extra


def test_load_config_named_component_specs_are_ignored(tmp_path: Path):
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

    assert config.component_dirs == []
    assert config.component_specs == []
    assert resolved.component_specs == []


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
