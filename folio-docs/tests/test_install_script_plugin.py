from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
SHORT_INSTALL_URL = "https://pguijas.github.io/folio/install.sh"
SHORT_INSTALL_COMMAND = f"curl -LsSf {SHORT_INSTALL_URL} | sh"
RAW_INSTALL_URL = "raw.githubusercontent.com/pguijas/folio/main/install.sh"


def test_docs_config_loads_project_install_script_plugin() -> None:
    config = (REPO_ROOT / "docs.yaml").read_text(encoding="utf-8")

    assert "./folio-docs/docs/plugins/install_script.py" in config


def test_install_script_plugin_publishes_installer_at_site_root(
    tmp_path: Path,
) -> None:
    import importlib.util

    plugin_path = ROOT / "docs" / "plugins" / "install_script.py"
    spec = importlib.util.spec_from_file_location("install_script", plugin_path)
    assert spec is not None
    assert spec.loader is not None
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)

    class Builder:
        build_dir = tmp_path / "build"

    plugin.emit_assets(builder=Builder(), config=None)

    copied = tmp_path / "build" / "public" / "install.sh"
    assert copied.read_bytes() == (ROOT / "install.sh").read_bytes()


def test_install_urls_use_the_site_not_raw_github() -> None:
    docs_yaml = (REPO_ROOT / "docs.yaml").read_text(encoding="utf-8")
    installation = (ROOT / "docs" / "guide" / "installation.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    # The landing shows the direct one-liner; README and the installation
    # guide keep their inspect-before-running flow but on the short URL.
    assert SHORT_INSTALL_COMMAND in docs_yaml
    for text in (docs_yaml, installation, readme):
        assert SHORT_INSTALL_URL in text
        assert RAW_INSTALL_URL not in text
