import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _imports(source: Path) -> list[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    return imported


def test_product_core_runtimes_do_not_import_each_other() -> None:
    agents_dir = ROOT / "folio-agents" / "folio_agents"
    docs_dir = ROOT / "folio-docs" / "folio_docs"

    agent_core = [
        source
        for source in agents_dir.rglob("*.py")
        if "integrations" not in source.relative_to(agents_dir).parts
    ]
    for source in agent_core:
        assert not any(
            name == "folio_docs" or name.startswith("folio_docs.")
            for name in _imports(source)
        ), source

    for source in docs_dir.rglob("*.py"):
        assert not any(
            name == "folio_agents" or name.startswith("folio_agents.")
            for name in _imports(source)
        ), source


def test_docs_template_does_not_bundle_the_agents_canvas() -> None:
    template = ROOT / "folio-docs" / "template"

    assert not (template / "components" / "kanban-board.tsx").exists()
    assert not (template / "lib" / "kanban-data.ts").exists()


def test_products_share_monorepo_scaffolding_and_one_template() -> None:
    assert (ROOT / ".github" / "workflows").is_dir()
    assert (ROOT / "folio-docs" / "template").is_dir()
    assert not (ROOT / "folio-agents" / "template").exists()

    repository_files = {
        "AGENTS.md",
        "CLAUDE.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
    }
    for product in (ROOT / "folio-docs", ROOT / "folio-agents"):
        assert not any((product / name).exists() for name in repository_files)
        assert not any(path.is_file() for path in (product / ".github").rglob("*"))
