import io
import threading
from pathlib import Path

from rich.console import Console
from watchfiles import Change

from folio_docs.config import Config
from folio_docs.watcher import (
    _PythonModuleCache,
    _handle_doc_change,
    _handle_preview_example_change,
    _handle_python_change,
    _is_under,
    _module_name_from_path,
    _preview_examples_dir,
    _route_from_doc_path,
    _watcher_loop,
    _watch_dirs_with_preview_examples,
)


def test_is_under_match() -> None:
    dirs = [Path("/src/mylib"), Path("/docs")]
    assert _is_under(Path("/src/mylib/core.py"), dirs)
    assert _is_under(Path("/docs/guide.md"), dirs)


def test_is_under_no_match() -> None:
    dirs = [Path("/src/mylib")]
    assert not _is_under(Path("/other/file.py"), dirs)


def test_module_name_from_path() -> None:
    src_dir = Path("/project/mylib")
    assert (
        _module_name_from_path(Path("/project/mylib/core.py"), src_dir) == "mylib.core"
    )
    assert (
        _module_name_from_path(Path("/project/mylib/__init__.py"), src_dir) == "mylib"
    )
    assert (
        _module_name_from_path(Path("/project/mylib/sub/deep.py"), src_dir)
        == "mylib.sub.deep"
    )
    assert (
        _module_name_from_path(Path("/project/mylib/sub/__init__.py"), src_dir)
        == "mylib.sub"
    )


def test_module_name_from_conventional_src_import_root() -> None:
    src_dir = Path("/project/src")

    assert _module_name_from_path(Path("/project/src/tool.py"), src_dir) == "tool"
    assert (
        _module_name_from_path(Path("/project/src/acme/__init__.py"), src_dir)
        == "acme"
    )
    assert (
        _module_name_from_path(Path("/project/src/acme/core.py"), src_dir)
        == "acme.core"
    )


def test_route_from_doc_path() -> None:
    doc_dir = Path("/project/docs/guide")
    assert (
        _route_from_doc_path(Path("/project/docs/guide/index.md"), doc_dir) == "index"
    )
    assert (
        _route_from_doc_path(Path("/project/docs/guide/install.md"), doc_dir)
        == "install"
    )
    assert (
        _route_from_doc_path(Path("/project/docs/guide/advanced/config.md"), doc_dir)
        == "advanced/config"
    )


def test_doc_watcher_removes_disabled_feature_docs(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    gated = docs_dir / "i18n.md"
    gated.write_text(
        "# Internationalization\n\nThis experimental guide should not be exposed.",
        encoding="utf-8",
    )

    class FakeBuilder:
        def __init__(self) -> None:
            self.pages: dict[str, str] = {"i18n": "stale"}
            self.search_written = False

        def write_page(self, route: str, content: str) -> None:
            self.pages[route] = content

        def remove_page(self, route: str) -> None:
            self.pages.pop(route, None)

        def write_search_index(self) -> None:
            self.search_written = True

    builder = FakeBuilder()
    config = Config(project_name="Demo")
    resolved = Config(project_name="Demo")

    _handle_doc_change(
        Change.modified,
        gated,
        [docs_dir],
        config,
        resolved,
        builder,  # type: ignore[arg-type]
        [],
        Console(file=io.StringIO()),
        verbose=False,
    )

    assert "i18n" not in builder.pages
    assert builder.search_written is True


def test_preview_examples_are_added_to_watch_dirs(tmp_path: Path) -> None:
    doc_dir = tmp_path / "docs" / "guide"
    examples_dir = tmp_path / "docs" / "examples"
    doc_dir.mkdir(parents=True)
    examples_dir.mkdir()

    watch_dirs = _watch_dirs_with_preview_examples([doc_dir], tmp_path)

    assert watch_dirs == [doc_dir, examples_dir]


def test_preview_examples_are_not_duplicated_in_watch_dirs(tmp_path: Path) -> None:
    examples_dir = tmp_path / "docs" / "examples"
    examples_dir.mkdir(parents=True)

    watch_dirs = _watch_dirs_with_preview_examples([examples_dir], tmp_path)

    assert watch_dirs == [examples_dir]


def test_preview_example_change_recompiles_static_assets(tmp_path: Path) -> None:
    examples_dir = _preview_examples_dir(tmp_path)
    changed_file = examples_dir / "landing-page" / "docs.yaml"

    class FakeBuilder:
        def __init__(self) -> None:
            self.examples: list[Path] = []

        def write_preview_examples(self, examples_dir: Path) -> None:
            self.examples.append(examples_dir)

    builder = FakeBuilder()

    _handle_preview_example_change(
        Change.modified,
        changed_file,
        examples_dir,
        builder,  # type: ignore[arg-type]
        Console(file=io.StringIO()),
        verbose=False,
    )

    assert builder.examples == [examples_dir]


def test_python_watcher_uses_full_symbol_index_for_changed_page(tmp_path: Path) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "models.py").write_text(
        'class Settings:\n    """Runtime settings."""\n    pass\n',
        encoding="utf-8",
    )
    consumer_path = package_dir / "consumer.py"
    consumer_path.write_text(
        "from .models import Settings\n"
        "\n"
        "def configure(settings: Settings) -> Settings:\n"
        '    """Configure the app.\n'
        "\n"
        "    Args:\n"
        "        settings: Runtime settings.\n"
        '    """\n'
        "    return settings\n",
        encoding="utf-8",
    )

    class FakeBuilder:
        def __init__(self) -> None:
            self.pages: dict[str, str] = {}

        def write_page(self, route: str, content: str) -> None:
            self.pages[route] = content

        def remove_page(self, route: str) -> None:
            self.pages.pop(route, None)

        def write_search_index(self) -> None:
            pass

    config = Config(project_name="Demo", project_repo="https://github.com/acme/demo")
    resolved = Config(
        project_name="Demo",
        project_repo="https://github.com/acme/demo",
        python_sources=[str(package_dir)],
    )
    builder = FakeBuilder()

    _handle_python_change(
        Change.modified,
        consumer_path,
        [package_dir],
        config,
        resolved,
        builder,  # type: ignore[arg-type]
        tmp_path,
        Console(file=io.StringIO()),
        verbose=False,
    )

    content = builder.pages["api-reference/demo/consumer"]
    assert 'href": "/docs/api-reference/demo/models#settings"' in content


def test_python_watcher_removes_disabled_api_modules(
    tmp_path: Path, monkeypatch
) -> None:
    from folio_docs import features

    monkeypatch.setattr(
        features,
        "MVP_DISABLED_API_MODULES",
        {"folio_docs.extensions": "roadmap", "folio_docs.docs.integrations": "roadmap"},
    )
    package_dir = tmp_path / "folio_docs"
    integrations_dir = package_dir / "docs" / "integrations"
    integrations_dir.mkdir(parents=True)
    roadmap_path = integrations_dir / "roadmap.py"
    roadmap_path.write_text(
        '"""Roadmap plugin internals."""\n',
        encoding="utf-8",
    )

    class FakeBuilder:
        def __init__(self) -> None:
            self.pages: dict[str, str] = {
                "api-reference/folio_docs/docs/integrations/roadmap": "stale",
                "api-reference/index": "stale",
            }
            self.meta: dict[str, str] = {}
            self.search_written = False

        def write_page(self, route: str, content: str) -> None:
            self.pages[route] = content

        def remove_page(self, route: str) -> None:
            self.pages.pop(route, None)

        def write_meta(self, directory: str, content: str) -> None:
            self.meta[directory] = content

        def write_search_index(self) -> None:
            self.search_written = True

    config = Config(project_name="Demo")
    resolved = Config(project_name="Demo", python_sources=[str(package_dir)])

    for module_cache in (None, _PythonModuleCache.from_config(resolved)):
        builder = FakeBuilder()

        _handle_python_change(
            Change.modified,
            roadmap_path,
            [package_dir],
            config,
            resolved,
            builder,  # type: ignore[arg-type]
            tmp_path,
            Console(file=io.StringIO()),
            verbose=False,
            module_cache=module_cache,
        )

        assert "api-reference/folio_docs/docs/integrations/roadmap" not in builder.pages
        assert "api-reference/index" not in builder.pages
        assert "api-reference" not in builder.meta.get("", "")
        assert builder.search_written is True


def test_python_watcher_reparses_only_changed_module_on_file_change(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    changed_path = package_dir / "changed.py"
    changed_path.write_text(
        '"""Changed module."""\n\n'
        "def updated() -> str:\n"
        '    """Return updated value."""\n'
        '    return "updated"\n',
        encoding="utf-8",
    )
    other_path = package_dir / "other.py"
    other_path.write_text(
        '"""Other module."""\n\n'
        "def untouched() -> str:\n"
        '    """Return untouched value."""\n'
        '    return "untouched"\n',
        encoding="utf-8",
    )

    parsed_files: list[Path] = []

    from folio_docs.parser import python_parser

    original_parse_python_file = python_parser.parse_python_file

    def recording_parse_python_file(path: Path, module_name: str, *args, **kwargs):
        parsed_files.append(Path(path))
        return original_parse_python_file(path, module_name, *args, **kwargs)

    monkeypatch.setattr(python_parser, "parse_python_file", recording_parse_python_file)

    def fake_watch(*_args, **_kwargs):
        parsed_files.clear()
        yield {(Change.modified, str(changed_path))}

    monkeypatch.setattr("folio_docs.watcher.watch", fake_watch)

    class FakeBuilder:
        def __init__(self) -> None:
            self.pages: list[str] = []

        def write_page(self, route: str, content: str) -> None:
            self.pages.append(route)

        def remove_page(self, route: str) -> None:
            pass

        def write_search_index(self) -> None:
            pass

    config = Config(project_name="Demo", project_repo="https://github.com/acme/demo")
    resolved = Config(
        project_name="Demo",
        project_repo="https://github.com/acme/demo",
        python_sources=[str(package_dir)],
    )
    builder = FakeBuilder()

    _watcher_loop(
        threading.Event(),
        [package_dir],
        [package_dir],
        [],
        tmp_path / "docs" / "examples",
        config,
        resolved,
        builder,  # type: ignore[arg-type]
        tmp_path,
        Console(file=io.StringIO()),
        verbose=False,
    )

    assert parsed_files == [changed_path]
    assert "api-reference/demo/changed" in builder.pages
    assert "api-reference/demo/other" not in builder.pages


class _FakePluginManager:
    """Records hook dispatches the way the real manager's call_isolated does."""

    def __init__(self, watch_paths=(), handled=True):
        self._watch_paths = list(watch_paths)
        self._handled = handled
        self.changes: list[tuple[str, str]] = []

    def call_isolated(self, hook, policy="warn_skip", **kwargs):
        if hook == "watch_paths":
            return [self._watch_paths]
        if hook == "on_watched_change":
            self.changes.append((kwargs["path"], kwargs["change"]))
            return [self._handled]
        raise AssertionError(hook)


def test_plugin_watch_dirs_come_from_the_hook(tmp_path: Path) -> None:
    """Plugins name the extra directories the watcher must care about; only
    the ones that exist make the list."""
    from folio_docs.watcher import _plugin_watch_dirs

    board = tmp_path / "board"
    board.mkdir()
    pm = _FakePluginManager(watch_paths=[str(board), str(tmp_path / "missing")])
    resolved = Config(project_name="Demo")
    assert _plugin_watch_dirs(pm, resolved) == [board]
    assert _plugin_watch_dirs(None, resolved) == []


def test_plugin_change_dispatches_to_the_hook(tmp_path: Path) -> None:
    """A change under a plugin-watched directory goes to the plugin, whatever
    the file's suffix — board.yaml is .yaml and cards are .md, and the
    handler, not the watcher, knows what they mean."""
    from folio_docs.watcher import _dispatch_plugin_change

    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True)
    card = board / "cards" / "x.md"
    card.write_text("---\ntitle: X\nstatus: backlog\n---\n", encoding="utf-8")

    pm = _FakePluginManager()
    resolved = Config(project_name="Demo")
    handled = _dispatch_plugin_change(
        pm, [board], object(), resolved, Change.modified, card
    )
    assert handled is True
    assert pm.changes == [(str(card), "modified")]

    outside = tmp_path / "elsewhere.md"
    outside.write_text("x", encoding="utf-8")
    assert (
        _dispatch_plugin_change(
            pm, [board], object(), resolved, Change.modified, outside
        )
        is False
    )
    assert len(pm.changes) == 1
