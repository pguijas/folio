from __future__ import annotations

import hashlib
import io
import json
import shutil
from pathlib import Path

from folio import __version__
import folio.build as build_module
from folio.build import run_build
from folio.generator.site_builder import SiteBuilder
from folio.parser.markdown_parser import MarkdownResult
from rich.console import Console


def test_run_build_recreates_missing_page_even_when_manifest_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    index_doc = docs_dir / "index.md"
    index_doc.write_text("# Overview\n\nWelcome.")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n'
    )

    build_dir = tmp_path / ".build"
    build_dir.mkdir()
    file_hash = hashlib.sha256(index_doc.read_bytes()).hexdigest()
    (build_dir / ".folio-manifest.json").write_text(
        json.dumps({"sources": {str(index_doc): {"hash": file_hash, "route": "index"}}})
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    generated = build_dir / "content" / "index.mdx"
    assert generated.exists()
    assert "# Overview" in generated.read_text()


def test_run_build_keeps_llm_files_after_static_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "llm:\n"
        "  generate_llms_txt: true\n"
        "  generate_llms_full_txt: true\n"
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)

    def fake_static_export(builder: SiteBuilder, **kwargs) -> None:
        if builder.output_dir.exists():
            shutil.rmtree(builder.output_dir)
        builder.output_dir.mkdir(parents=True)
        (builder.output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(SiteBuilder, "build", fake_static_export)

    run_build(tmp_path)

    assert (tmp_path / "_site" / "llms.txt").exists()
    assert (tmp_path / "_site" / "llms-full.txt").exists()


def test_run_build_respects_individual_llm_flags(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "llm:\n"
        "  generate_llms_txt: true\n"
        "  generate_llms_full_txt: false\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)

    def fake_static_export(builder: SiteBuilder, **kwargs) -> None:
        if builder.output_dir.exists():
            shutil.rmtree(builder.output_dir)
        builder.output_dir.mkdir(parents=True)
        (builder.output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(SiteBuilder, "build", fake_static_export)

    run_build(tmp_path)

    assert (tmp_path / "_site" / "llms.txt").exists()
    assert not (tmp_path / "_site" / "llms-full.txt").exists()


def test_check_generated_links_does_not_treat_disabled_docs_as_valid(
    tmp_path: Path,
) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "# Overview\n\n[Plugins](./plugins)\n",
        encoding="utf-8",
    )

    docs = [
        MarkdownResult(content="# Overview", frontmatter={}, route="index"),
        MarkdownResult(content="# Plugins", frontmatter={}, route="plugins"),
    ]

    class FakeBuilder:
        pass

    builder = FakeBuilder()
    builder.content_dir = content_dir

    broken = build_module._check_generated_links(builder, [], docs)

    assert len(broken) == 1
    assert broken[0].source_page == "index"
    assert broken[0].target == "./plugins"


def test_run_build_banner_uses_folio_version(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "9.9.9"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = capsys.readouterr().out
    assert f"v{__version__}" in output
    assert "v9.9.9" not in output


def test_run_build_serve_banner_omits_news_line(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = capsys.readouterr().out
    assert "⚡" not in output


def test_print_banner_without_news_leaves_trailing_spacer(monkeypatch) -> None:
    buffer = io.StringIO()
    test_console = Console(file=buffer, width=80, color_system=None)
    monkeypatch.setattr(build_module, "console", test_console)

    build_module._print_banner(None, include_news=False)

    assert buffer.getvalue().endswith("\n\n")


def test_print_banner_with_news_leaves_trailing_spacer(monkeypatch) -> None:
    buffer = io.StringIO()
    test_console = Console(file=buffer, width=80, color_system=None)
    monkeypatch.setattr(build_module, "console", test_console)

    build_module._print_banner(None, include_news=True)

    assert "⚡" in buffer.getvalue()
    assert buffer.getvalue().endswith("\n\n")


def test_run_build_serve_banner_keeps_spacing_after_logo(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = capsys.readouterr().out
    lines = output.splitlines()
    logo_version_line = next(
        index for index, line in enumerate(lines) if f"v{__version__}" in line
    )

    assert lines[logo_version_line + 1 : logo_version_line + 3] == ["", ""]


def test_run_build_banner_omits_news_line_and_keeps_spacing_after_logo(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    output = capsys.readouterr().out
    lines = output.splitlines()
    logo_version_line = next(
        index for index, line in enumerate(lines) if f"v{__version__}" in line
    )

    assert "⚡" not in output
    assert lines[logo_version_line + 1 : logo_version_line + 3] == ["", ""]


def test_run_build_serve_prints_structured_done_step(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=80, color_system=None)

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = test_console.export_text()

    assert "✓ Done" in output
    assert "Export" not in output
    assert "06  Done" not in output
    assert "07  Done" not in output
    assert "Build complete" not in output


def test_step_description_omits_number_and_left_margin() -> None:
    description = build_module._step_description("Export", "building static site")

    assert "06" not in description
    assert description.startswith("[bold cyan]Export")
    assert "›" in description
    assert "building static site" in description


def test_export_step_detail_omits_full_log_toggle() -> None:
    assert build_module._export_step_detail() == "building static site"


def test_build_output_stream_records_lines_without_live_repaint(monkeypatch) -> None:
    class FakeLive:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("build output should not use a live repainting panel")

    monkeypatch.setattr(build_module, "Live", FakeLive, raising=False)

    stream = build_module._BuildOutputStream()
    with stream:
        stream.record("Creating an optimized production build ...\n")
        stream.record("Compiled successfully\n")

    assert stream.lines == [
        "Creating an optimized production build ...\n",
        "Compiled successfully\n",
    ]


def test_pages_progress_starts_before_meta_pages(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    state = {"pages_active": False, "meta_called": False}

    class TrackingProgress:
        console = Console(file=io.StringIO(), color_system=None)

        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self) -> "TrackingProgress":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            state["pages_active"] = False

        def add_task(self, description: str, total=None) -> int:
            if "Pages" in description:
                state["pages_active"] = True
            return 1

        def advance(self, task_id: int) -> None:
            pass

        def update(self, task_id: int, **kwargs) -> None:
            pass

    def fake_write_meta_pages(*args, **kwargs) -> None:
        state["meta_called"] = True
        assert state["pages_active"]

    monkeypatch.setattr(build_module, "Progress", TrackingProgress)
    monkeypatch.setattr(build_module, "_write_meta_pages", fake_write_meta_pages)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    assert state["meta_called"]


def test_run_build_shows_progress_for_post_page_work(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "examples").mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=100, color_system=None)

    state = {
        "active": "",
        "preview_called": False,
        "links_called": False,
    }
    descriptions: list[str] = []

    class TrackingProgress:
        console = Console(file=io.StringIO(), color_system=None)

        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self) -> "TrackingProgress":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            state["active"] = ""

        def add_task(self, description: str, total=None) -> int:
            state["active"] = description
            descriptions.append(description)
            return 1

        def advance(self, task_id: int) -> None:
            pass

        def update(self, task_id: int, **kwargs) -> None:
            pass

    def fake_write_preview_examples(self: SiteBuilder, examples_dir: Path) -> None:
        state["preview_called"] = True
        assert "Previews" in state["active"]

    def fake_check_generated_links(*args, **kwargs) -> list:
        state["links_called"] = True
        assert "Links" in state["active"]
        return []

    monkeypatch.setattr(build_module, "Progress", TrackingProgress)
    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(
        SiteBuilder, "write_preview_examples", fake_write_preview_examples
    )
    monkeypatch.setattr(
        build_module, "_check_generated_links", fake_check_generated_links
    )
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    output = test_console.export_text()

    assert state["preview_called"]
    assert state["links_called"]
    assert any("Finalize" in description for description in descriptions)
    assert any("Previews" in description for description in descriptions)
    assert any("Links" in description for description in descriptions)
    assert "✓ Previews" in output


def test_run_build_prints_structured_steps(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=100, color_system=None)

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)

    def fake_build(self: SiteBuilder, **kwargs) -> None:
        assert kwargs["log_path"].name == ".folio-build.log"
        assert callable(kwargs["output_callback"])
        kwargs["output_callback"]("Creating an optimized production build ...\n")
        kwargs["output_callback"]("Compiled successfully\n")

    monkeypatch.setattr(SiteBuilder, "build", fake_build)

    run_build(tmp_path)

    output = test_console.export_text()
    expected_steps = [
        "✓ Sources",
        "✓ Template",
        "✓ Pages",
        "✓ Links",
        "✓ Dependencies",
        "✓ Export",
        "Build output",
        "✓ Done",
        "✨ Site ready",
    ]
    positions = [output.index(step) for step in expected_steps]

    assert positions == sorted(positions)
    assert "  ✓ Sources" not in output
    assert "01  Sources" not in output
    assert "06  Export" not in output
    assert "Build complete" not in output
    assert "Static site ready at" not in output
    assert "Build output" in output
    assert output.count("Build output") == 1
    assert "Creating an optimized production build ..." in output
    assert "Compiled successfully" in output
    assert "Ctrl+O" not in output
    assert "Site export completed" in output
    assert "Next.js build completed" not in output
    assert "ready in" not in output
    assert "page in" in output
    assert "_site/" in output


def test_run_build_prints_rst_warning_as_structured_step(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (docs_dir / "legacy.rst").write_text("Legacy docs\n===========\n", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=100, color_system=None)

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    captured = capsys.readouterr()
    output = test_console.export_text()

    assert "✓ Sources" in output
    assert "01  Sources" not in output
    assert "source.docs supports Markdown build inputs only" in output
    assert "UserWarning" not in captured.err


def test_run_build_preview_examples_do_not_print_nested_banners(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    example_docs = tmp_path / "docs" / "examples" / "sample" / "docs"
    example_docs.mkdir(parents=True)
    (example_docs / "index.md").write_text("# Example\n\nPreview.", encoding="utf-8")
    (example_docs.parent / "docs.yaml").write_text(
        'project:\n  name: "Sample"\nsource:\n  docs:\n    - "docs/"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    buffer = io.StringIO()
    test_console = Console(
        file=buffer,
        force_terminal=True,
        width=100,
        color_system=None,
    )

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    output = buffer.getvalue()

    assert output.count(f"v{__version__}") == 1
    assert (tmp_path / ".build" / "public" / "_folio" / "examples" / "sample").exists()


def test_run_build_quiet_suppresses_tty_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    buffer = io.StringIO()
    test_console = Console(
        file=buffer,
        force_terminal=True,
        width=100,
        color_system=None,
    )

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, quiet=True)

    assert buffer.getvalue() == ""
    assert (tmp_path / ".build" / "content" / "index.mdx").exists()


def test_run_build_regenerates_source_pages_when_config_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "core.py").write_text(
        'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    config_path = tmp_path / "docs.yaml"
    config_path.write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/old"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    generated = tmp_path / ".build" / "content" / "api-reference" / "demo" / "core.mdx"
    assert "https://github.com/acme/old/blob/main/demo/core.py" in generated.read_text()

    config_path.write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/new"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    run_build(tmp_path)

    content = generated.read_text()
    assert "https://github.com/acme/new/blob/main/demo/core.py" in content
    assert "https://github.com/acme/old/blob/main/demo/core.py" not in content


def test_run_build_uses_configured_source_ref_for_source_links(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "core.py").write_text(
        'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/demo"\n'
        '  repo_ref: "release/2.x"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    generated = tmp_path / ".build" / "content" / "api-reference" / "demo" / "core.mdx"
    content = generated.read_text()
    assert "https://github.com/acme/demo/blob/release/2.x/demo/core.py" in content
    assert "/blob/main/" not in content


def test_run_build_source_ref_override_wins_for_source_links(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "core.py").write_text(
        'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/demo"\n'
        '  repo_ref: "main"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, source_ref_override="v0.1.0")

    generated = tmp_path / ".build" / "content" / "api-reference" / "demo" / "core.mdx"
    content = generated.read_text()
    assert "https://github.com/acme/demo/blob/v0.1.0/demo/core.py" in content
    assert "/blob/main/" not in content


def test_run_build_omits_version_metadata_by_default(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1"\n'
        '    path: "v0.1"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    run_build(tmp_path)

    output = capsys.readouterr().out
    assert "Current version only" not in output

    selector = tmp_path / ".build" / "components" / "version-selector.tsx"
    content = selector.read_text(encoding="utf-8")
    assert "const versions: Version[] = []" in content
    assert 'const configuredCurrentPath: string = ""' in content
    assert "latest" not in content
    assert "v0.1" not in content


def test_run_build_serve_writes_doc_preview_examples(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    example_dir = tmp_path / "docs" / "examples" / "sample"
    example_dir.mkdir(parents=True)
    (example_dir / "docs.yaml").write_text(
        'project:\n  name: "Sample"\nsource:\n  docs:\n    - "docs/"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    preview_calls: list[Path] = []
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(
        SiteBuilder,
        "write_preview_examples",
        lambda self, examples_dir: preview_calls.append(Path(examples_dir)),
    )
    monkeypatch.setattr(
        build_module,
        "_start_dev_server",
        lambda **kwargs: None,
    )

    run_build(tmp_path, serve=True)

    assert preview_calls == [tmp_path / "docs" / "examples"]
