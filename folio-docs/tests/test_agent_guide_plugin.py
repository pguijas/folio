import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
PLUGIN_PATH = ROOT / "docs" / "plugins" / "agent_guide.py"


@pytest.fixture(scope="module")
def plugin():
    spec = importlib.util.spec_from_file_location("agent_guide", PLUGIN_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_docs_config_loads_project_agent_guide_plugin() -> None:
    config = (REPO_ROOT / "docs.yaml").read_text(encoding="utf-8")

    assert "./folio-docs/docs/plugins/agent_guide.py" in config


def test_agent_guide_plugin_publishes_the_guide_at_site_root(
    tmp_path: Path, plugin
) -> None:
    class Builder:
        build_dir = tmp_path / "build"

    class Config:
        site_url = "https://example.test/folio"

    plugin.emit_assets(builder=Builder(), config=Config())

    written = tmp_path / "build" / "public" / "agent-guide.md"
    assert written.read_text(encoding="utf-8") == plugin.render(
        "https://example.test/folio"
    )


def test_emit_falls_back_to_the_default_site_url(tmp_path: Path, plugin) -> None:
    class Builder:
        build_dir = tmp_path / "build"

    class Config:
        site_url = ""

    plugin.emit_assets(builder=Builder(), config=Config())

    written = (tmp_path / "build" / "public" / "agent-guide.md").read_text(
        encoding="utf-8"
    )
    assert f"{plugin.DEFAULT_SITE_URL}/docs/cli" in written
    assert plugin.DOCS_TOKEN not in written


def test_guide_addresses_the_reading_agent_and_links_the_canonical_docs(
    plugin,
) -> None:
    guide = plugin.render("https://example.test/folio")

    assert guide.startswith("# Folio agent guide")
    assert "You are reading this because a human asked you to help them" in guide
    assert "https://example.test/folio/docs/" in guide


def test_guide_teaches_the_concept_model_in_order(plugin) -> None:
    guide = plugin.render()

    positions = [
        guide.index(term)
        for term in (
            "**Repository truth**",
            "**`docs.yaml`**",
            "**Sources**",
            "**The build**",
            "**Plugins**",
            "**The output**",
        )
    ]

    assert positions == sorted(positions)


def test_guide_states_the_enforced_toolchain_minimums(plugin) -> None:
    from folio_docs.docs.next_runtime import MIN_NODE_VERSION, MIN_PNPM_VERSION

    guide = plugin.render()

    node = ".".join(str(part) for part in MIN_NODE_VERSION)
    pnpm = str(MIN_PNPM_VERSION[0])
    assert f"Node.js {node} or newer" in guide
    assert f"pnpm {pnpm} or newer" in guide
    assert "uv tool install folio-docs" in guide
    assert "corepack prepare pnpm@10 --activate" in guide


def test_guide_pairs_every_symptom_with_a_command_and_a_docs_link(plugin) -> None:
    guide = plugin.render("https://example.test/folio")
    recipes = guide.split("## Diagnosis by symptom")[1].split("## Rules for you")[0]

    for symptom in (
        "Environment check failed",
        # The stable prefix only: config.py appends the resolved path.
        "Config file not found:",
        "missing from the API reference",
        "has no effect",
        "stale",
        "Port 4321 is already in use",
        "Broken internal links",
        "static export fails",
        "A plugin does nothing",
    ):
        assert symptom in recipes

    assert recipes.count("See https://example.test/folio/docs/") == 9


def test_guide_states_the_agent_rules(plugin) -> None:
    guide = plugin.render()

    assert "Do not invent config keys or CLI flags" in guide
    assert "route the human to the page instead of guessing" in guide
    assert "is the authority on what `docs.yaml` accepts" in guide


def test_guide_points_at_the_board_protocol_without_restating_it(plugin) -> None:
    guide = plugin.render()

    assert "board/SKILL.md" in guide
    # The board protocol is scaffolded into each user's project; Folio's own
    # development board is deliberately not part of the release tree.
    for owned in ("folio kanban move", "## Card schema", "cards/_TEMPLATE.md"):
        assert owned not in guide


# Named in the guide as roadmap, so they must NOT exist on the CLI yet.
ROADMAP_COMMANDS = {"mcp"}
# Belongs to corepack, not to folio_docs.
EXTERNAL_FLAGS = {"--activate"}


def _cli_flags(command) -> set[str]:
    # click adds --help to every command outside `params`.
    flags = {"--help"}
    for param in command.params:
        flags.update(opt for opt in param.opts if opt.startswith("--"))
    for child in getattr(command, "commands", {}).values():
        flags |= _cli_flags(child)
    return flags


def test_guide_only_names_commands_and_flags_that_exist(plugin) -> None:
    import re

    from typer.main import get_command

    from folio_docs.cli import app

    guide = plugin.render()
    command = get_command(app)
    known_commands = set(command.commands)
    known_flags = _cli_flags(command)
    cli_reference = (ROOT / "docs" / "guide" / "cli.md").read_text(encoding="utf-8")

    for name in set(re.findall(r"folio ([a-z][a-z-]*)", guide)):
        if name in ROADMAP_COMMANDS:
            assert name not in known_commands, (
                f"folio {name} shipped; guide is stale"
            )
            continue
        assert name in known_commands, f"unknown command: folio {name}"

    for flag in set(re.findall(r"--[a-z][a-z-]+", guide)):
        if flag in EXTERNAL_FLAGS:
            continue
        assert flag in known_flags, f"unknown flag: {flag}"
        assert f"`{flag}`" in cli_reference, f"undocumented flag: {flag}"


def test_guide_respects_the_project_vocabulary_rules(plugin) -> None:
    guide = plugin.render()
    lowered = guide.lower()

    for banned in ("compile", "compiler", "compiled", "dogfood", "!"):
        assert banned not in lowered
    assert "docs generator" in lowered
