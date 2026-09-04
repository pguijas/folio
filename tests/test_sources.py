from pathlib import Path

from folio.config import Config
from folio.sources import parse_doc_sources, parse_python_sources


def test_parse_python_sources_uses_configured_paths_excludes_and_docstring_style(
    tmp_path: Path,
) -> None:
    source = tmp_path / "src" / "demo"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text('"""Demo package."""\n')
    (source / "core.py").write_text(
        '"""Core module."""\n\n'
        "def add(a, b):\n"
        '    """Add values.\n\n'
        "    Parameters\n"
        "    ----------\n"
        "    a : int\n"
        "        First value.\n"
        "    b : int\n"
        "        Second value.\n"
        "    Returns\n"
        "    -------\n"
        "    int\n"
        "        Sum.\n"
        '    """\n'
        "    return a + b\n"
    )
    excluded = source / "internal.py"
    excluded.write_text('"""Internal."""\n')
    missing = tmp_path / "missing"
    config = Config(
        project_name="Demo",
        python_sources=[str(source), str(missing)],
        python_excludes=[str(excluded)],
        docstring_style="numpy",
    )

    parsed = parse_python_sources(config)

    assert parsed.missing_paths == [str(missing)]
    assert parsed.scanned_paths == [source]
    assert [module.name for module in parsed.modules] == ["demo", "demo.core"]
    add = parsed.modules[1].functions[0]
    assert add.args[0].description == "First value."
    assert add.returns is not None
    assert add.returns.description == "Sum."


def test_parse_doc_sources_uses_configured_paths_and_reports_missing(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n\nWelcome.\n")
    missing = tmp_path / "missing-docs"
    config = Config(
        project_name="Demo",
        doc_sources=[str(docs), str(missing)],
    )

    parsed = parse_doc_sources(config)

    assert parsed.missing_paths == [str(missing)]
    assert parsed.scanned_paths == [docs]
    assert [doc.route for doc in parsed.docs] == ["index"]
