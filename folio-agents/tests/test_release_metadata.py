from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import folio_agents

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


ROOT = Path(__file__).parents[1]


def test_package_version_and_cli_plugin_are_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]

    assert project["name"] == "folio-agents"
    assert project["version"] == folio_agents.__version__
    assert "scripts" not in project
    assert project["entry-points"]["folio.cli"] == {
        "agents": "folio_agents.cli_commands:register"
    }


def test_core_install_does_not_require_folio_docs() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]

    assert all(not item.startswith("folio-docs") for item in project["dependencies"])
    assert project["optional-dependencies"]["docs"] == ["folio-docs>=0.3,<0.4"]
    assert importlib.util.find_spec("folio_agents") is not None


def test_release_checker_accepts_the_agents_tag() -> None:
    env = {
        **os.environ,
        "GITHUB_REF_TYPE": "tag",
        "GITHUB_REF_NAME": f"agents-v{folio_agents.__version__}",
    }
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_release_version.py")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_publishing_assets_ship_inside_the_agents_package() -> None:
    assets = ROOT / "folio_agents" / "assets"

    assert (assets / "kanban-board.tsx").is_file()
    assert (assets / "redirect-page.tsx").is_file()
