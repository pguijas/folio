from pathlib import Path

from folio_docs.config import Config
from folio_docs.sources import parse_doc_sources, parse_python_sources


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


def test_parse_python_sources_treats_src_as_an_import_root(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    package = source_root / "acme"
    namespace = source_root / "extensions" / "payments"
    namespace.mkdir(parents=True)
    package.mkdir()
    (package / "__init__.py").write_text('"""Acme package."""\n', encoding="utf-8")
    (package / "api.py").write_text("def ping(): pass\n", encoding="utf-8")
    (namespace / "client.py").write_text("def charge(): pass\n", encoding="utf-8")
    (source_root / "standalone.py").write_text("def run(): pass\n", encoding="utf-8")

    parsed = parse_python_sources(
        Config(project_name="Demo", python_sources=[str(source_root)])
    )

    assert [module.name for module in parsed.modules] == [
        "standalone",
        "acme",
        "acme.api",
        "extensions.payments.client",
    ]
