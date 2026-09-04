"""Cardfile board format (board.source pointing at a directory)."""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path

import pytest

from folio_docs.config import Config
from folio_agents.integrations import kanban as kanban_plugin
from folio_agents.loader import load_board_dir

BOARD_YAML = """\
title: "Demo Board"
columns:
  - id: ideas
    title: "Ideas"
  - id: doing
    title: "In progress"
    limit: 2
  - id: done
    title: "Done"
"""


def _write_card(board: Path, card_id: str, content: str) -> Path:
    path = board / "cards" / f"{card_id}.md"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _make_board(tmp_path: Path) -> Path:
    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True)
    (board / "board.yaml").write_text(BOARD_YAML, encoding="utf-8")
    return board


class _StaticAssetBuilder:
    """AssetBuilder stand-in that records what a plugin publishes."""

    def __init__(self) -> None:
        self.copied: list[str] = []
        self.removed: list[str] = []
        self.pages: dict[str, str] = {}
        self.meta: dict[str, str] = {}
        self.routes: set[str] = set()

    def copy_static_asset(self, relative: str, source: Path) -> None:
        assert source.is_file()
        self.copied.append(relative)

    def remove_static_tree(self, relative: str) -> None:
        self.removed.append(relative)

    def page_exists(self, route: str) -> bool:
        return route in self.pages

    def read_page(self, route: str) -> str:
        return self.pages[route]

    def write_page(self, route: str, content: str) -> None:
        self.pages[route] = content

    def remove_page(self, route: str) -> None:
        self.pages.pop(route, None)

    def list_pages(self, prefix: str) -> list[str]:
        return sorted(route for route in self.pages if route.startswith(f"{prefix}/"))

    def write_meta(self, directory: str, meta_json: str) -> None:
        self.meta[directory] = meta_json

    def register_route(self, route: str) -> None:
        self.routes.add(route)


def _configure(tmp_path: Path, kanban_section: dict) -> Config:
    config = Config(
        project_name="Demo",
        project_dir=str(tmp_path),
        project_repo="https://github.com/acme/demo",
        extra={},
    )
    kanban_plugin.configure(config=config, raw_config={"kanban": kanban_section})
    return config


def test_cardfile_board_loads_groups_and_sorts(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "notes.md").write_text("# n", encoding="utf-8")

    _write_card(
        board,
        "epic-artifacts",
        """\
        ---
        title: Artifact manager epic
        status: ideas
        priority: high
        created: 2026-07-01
        ---

        The umbrella card.
        """,
    )
    _write_card(
        board,
        "write-cli",
        """\
        ---
        title: Write CLI
        status: doing
        parent: epic-artifacts
        blocked_by: [store-lib]
        tags: [cli]
        assignee: claude
        artifacts:
          - doc: research/notes.md
            label: Research
          - pr: 42
          - url: https://example.com/spec
        created: 2026-07-10
        ---

        Deterministic mutation commands.

        ## Acceptance criteria
        - [x] move command
        - [ ] trail command

        ## Trail
        - 2026-07-11 @claude (abc1234): spiked line surgery
        - 2026-07-12 @pguijas: reviewed approach
        """,
    )
    _write_card(
        board,
        "store-lib",
        """\
        ---
        title: Store lib
        status: doing
        order: 100
        created: 2026-07-09
        ---
        """,
    )

    loaded = load_board_dir(board, project_dir=tmp_path)
    assert loaded["title"] == "Demo Board"
    by_id = {column["id"]: column for column in loaded["columns"]}
    assert list(by_id) == ["ideas", "doing", "done"]

    doing = by_id["doing"]["cards"]
    # store-lib carries an explicit rank so it sorts before the unranked card.
    assert [card["id"] for card in doing] == ["store-lib", "write-cli"]

    card = doing[1]
    assert card["parent"] == "epic-artifacts"
    assert card["blocked_by"] == ["store-lib"]
    assert card["description"] == "Deterministic mutation commands."
    assert card["criteria"] == [
        {"text": "move command", "done": True},
        {"text": "trail command", "done": False},
    ]
    assert card["trail"][0] == {
        "date": "2026-07-11",
        "actor": "claude",
        "ref": "abc1234",
        "note": "spiked line surgery",
    }
    assert card["trail"][1]["ref"] == ""


def test_an_artifact_away_from_its_card_carries_no_href(tmp_path: Path) -> None:
    """A path or a PR number renders as what it is, never as a repo URL.

    The board used to rewrite doc/file targets to ``{repo}/blob/HEAD/...``
    and a PR number to ``{repo}/pull/n``. That made every artifact a link
    out to whoever hosts the repository, and produced a 404 for anything
    not committed there.

    What is a link: ``url:``, which the author wrote as one, and anything
    inside the card's own directory, which the build publishes. Everywhere
    else in the project is a path, printed — attaching a file does not
    publish an arbitrary part of the repository.
    """
    board = _make_board(tmp_path)
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "notes.md").write_text("# n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: research/notes.md
          - file: folio/x.py#L12
          - pr: 7
          - url: https://example.com/a
        ---
        """,
    )
    (tmp_path / "folio").mkdir()
    (tmp_path / "folio" / "x.py").write_text("x = 1\n", encoding="utf-8")

    # The unlinked doc: is also the one whose file exists but whose page
    # nothing publishes, so configure's one pass says so.
    with pytest.warns(UserWarning, match="no published page"):
        config = _configure(tmp_path, {"source": "board"})
    kanban = config.extra["kanban"]
    assert kanban["title"] == "Demo Board"
    hrefs = {
        artifact["kind"]: artifact["href"]
        for artifact in kanban["columns"][0]["cards"][0]["artifacts"]
    }
    assert hrefs == {
        "doc": "",
        "file": "",
        "pr": "",
        "url": "https://example.com/a",
    }
    # The targets themselves are untouched: only the derived link is gone.
    targets = {
        artifact["kind"]: artifact["target"]
        for artifact in kanban["columns"][0]["cards"][0]["artifacts"]
    }
    assert targets["doc"] == "research/notes.md"
    assert targets["file"] == "folio/x.py#L12"
    assert targets["pr"] == "7"

    # The extended fields survive active_kanban's re-normalization pass.
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    card = active["columns"][0]["cards"][0]
    assert card["id"] == "one-card"
    assert len(card["artifacts"]) == 4
    assert card["artifacts"][0]["href"] == ""
    assert card["artifacts"][0]["target"] == "research/notes.md"


def test_an_artifact_beside_its_card_opens(tmp_path: Path) -> None:
    """A card's own directory is published, so its artifacts are links.

    Markdown resolves to the page it was built into — it goes through the
    same parser and MDX writer as any documentation page, so there is a real
    page to open. Everything else resolves to the file as published under
    ``/_folio/kanban/<id>/``. A file one directory up resolves to neither,
    because nothing publishes it. The siblings are derived (name-sorted,
    first), so the legacy full-path frontmatter entries ride along as their
    ``display`` instead of duplicating them.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "prototype.html").write_text("<p>x</p>", encoding="utf-8")
    (assets / "compared.md").write_text("# c", encoding="utf-8")
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "loose.md").write_text("# l", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - file: board/cards/one-card/prototype.html
          - doc: board/cards/one-card/compared.md
          - doc: research/loose.md
        ---
        """,
    )

    # The loose doc: exists but nothing publishes it, and the build says so.
    with pytest.warns(UserWarning, match="no published page"):
        config = _configure(tmp_path, {"source": "board"})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    artifacts = active["columns"][0]["cards"][0]["artifacts"]
    assert [artifact["href"] for artifact in artifacts] == [
        "/docs/kanban/cards/one-card/compared/",
        "/_folio/kanban/one-card/prototype.html",
        "",
    ]
    # A published artifact is still described by the path it was written as.
    assert artifacts[1]["target"] == "board/cards/one-card/prototype.html"
    assert artifacts[1]["display"] == "board/cards/one-card/prototype.html"


def test_compiled_artifact_href_uses_the_configured_docs_route(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "report.mdx").write_text("# Report\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: board/cards/one-card/report.mdx
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    config.docs_route_base = "/reference"
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    artifact = active["columns"][0]["cards"][0]["artifacts"][0]
    assert artifact["href"] == "/reference/kanban/cards/one-card/report/"


def test_artifacts_derive_from_the_card_directory(tmp_path: Path) -> None:
    """What sits in the directory is the card's artifacts, derived not declared.

    One artifact per regular file at the directory's top level, name-sorted:
    markdown kinds become ``doc``, everything else ``file``. Dotfiles,
    ``_``-prefixed names, subdirectories, and symlinks stay behind — the same
    lines publishing already draws. ``display`` carries the one string a
    reader needs: the bare name, because a card's own directory is the one
    place a target never has to say where it is.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    (assets / "nested").mkdir(parents=True)
    (assets / "compare.md").write_text("# c", encoding="utf-8")
    (assets / "proto.html").write_text("<p>x</p>", encoding="utf-8")
    (assets / "brief.mdx").write_text("# b", encoding="utf-8")
    (assets / ".scratch").write_text("s", encoding="utf-8")
    (assets / "_draft.md").write_text("# d", encoding="utf-8")
    (assets / "nested" / "inner.txt").write_text("i", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("o", encoding="utf-8")
    (assets / "linked.txt").symlink_to(outside)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    assert active["columns"][0]["cards"][0]["artifacts"] == [
        {
            "kind": "doc",
            "target": "board/cards/one-card/brief.mdx",
            "label": "",
            "display": "brief.mdx",
            "href": "/docs/kanban/cards/one-card/brief/",
        },
        {
            "kind": "doc",
            "target": "board/cards/one-card/compare.md",
            "label": "",
            "display": "compare.md",
            "href": "/docs/kanban/cards/one-card/compare/",
        },
        {
            "kind": "file",
            "target": "board/cards/one-card/proto.html",
            "label": "",
            "display": "proto.html",
            "href": "/_folio/kanban/one-card/proto.html",
        },
    ]


def test_frontmatter_labels_siblings_without_duplicating_them(tmp_path: Path) -> None:
    """A ``doc:``/``file:`` entry naming a sibling is a label, not a second row.

    All three spellings reach the same derived entry: the bare name, the
    ``./`` form a markdown link would use, and the legacy project-relative
    path existing boards carry. The label lands on the derived artifact,
    ``display`` keeps what the author wrote, and nothing is listed twice.
    Frontmatter entries that are not siblings follow the derived block in
    frontmatter order.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "plan.md").write_text("# p", encoding="utf-8")
    (assets / "compare.md").write_text("# c", encoding="utf-8")
    (assets / "proto.html").write_text("<p>x</p>", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: plan.md
            label: The plan
          - doc: ./compare.md
            label: Compared
          - file: board/cards/one-card/proto.html
            label: The prototype
          - pr: 7
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    artifacts = active["columns"][0]["cards"][0]["artifacts"]
    assert [
        (artifact["kind"], artifact["display"], artifact["label"])
        for artifact in artifacts
    ] == [
        ("doc", "./compare.md", "Compared"),
        ("doc", "plan.md", "The plan"),
        ("file", "board/cards/one-card/proto.html", "The prototype"),
        ("pr", "7", ""),
    ]
    assert [artifact["target"] for artifact in artifacts[:3]] == [
        "board/cards/one-card/compare.md",
        "board/cards/one-card/plan.md",
        "board/cards/one-card/proto.html",
    ]


def test_targets_resolve_beside_the_card_before_the_project(tmp_path: Path) -> None:
    """A relative target means what a relative link in the body means.

    Resolution tries the card's directory first, then the project root — the
    same order a reader applies. A nested card-relative path resolves and is
    recorded at its project-relative address, so the published href still
    works; a project-relative path stays exactly as written.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    (assets / "sub").mkdir(parents=True)
    (assets / "shared.txt").write_text("card copy", encoding="utf-8")
    (assets / "sub" / "deep.txt").write_text("d", encoding="utf-8")
    (tmp_path / "shared.txt").write_text("project copy", encoding="utf-8")
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "notes.txt").write_text("n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - file: shared.txt
          - file: sub/deep.txt
          - file: research/notes.txt
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    artifacts = active["columns"][0]["cards"][0]["artifacts"]
    assert [
        (artifact["target"], artifact["display"], artifact["href"])
        for artifact in artifacts
    ] == [
        # The bare name reached the sibling, not the project-root file.
        (
            "board/cards/one-card/shared.txt",
            "shared.txt",
            "/_folio/kanban/one-card/shared.txt",
        ),
        (
            "board/cards/one-card/sub/deep.txt",
            "sub/deep.txt",
            "/_folio/kanban/one-card/sub/deep.txt",
        ),
        ("research/notes.txt", "research/notes.txt", ""),
    ]


def test_a_doc_naming_a_published_docs_page_links_to_it(tmp_path: Path) -> None:
    """A ``doc:`` under a docs source opens the page the site already builds.

    The site publishes exactly that page, so printing the path instead of
    linking it was the last unkept half of "a doc: artifact renders as a
    site page". The route rule is the one ``parse_markdown_directory``
    applies: relative to the source, ``.md`` off, ``README`` is the folder.
    """
    board = _make_board(tmp_path)
    guide = tmp_path / "docs" / "guide"
    (guide / "kanban").mkdir(parents=True)
    (guide / "kanban" / "index.md").write_text("# K", encoding="utf-8")
    (guide / "start.md").write_text("# S", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: docs/guide/kanban/index.md
          - doc: docs/guide/start.md#setup
        ---
        """,
    )

    config = Config(
        project_name="Demo",
        project_dir=str(tmp_path),
        doc_sources=["docs/guide"],
        extra={},
    )
    kanban_plugin.configure(config=config, raw_config={"kanban": {"source": "board"}})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    artifacts = active["columns"][0]["cards"][0]["artifacts"]
    assert [artifact["href"] for artifact in artifacts] == [
        "/docs/kanban/",
        "/docs/start/#setup",
    ]


def test_an_unreachable_target_warns_and_still_renders(tmp_path: Path) -> None:
    """A target that resolves to no file warns, naming the card and the path.

    It used to fail the build; a stale path in one card's frontmatter is not
    board topology, and the artifact still says something true — this card
    claims that output. The tile renders unlinked, the way every unpublished
    target already does.
    """
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: gone.md
          - file: also/gone.txt
        ---
        """,
    )

    with pytest.warns(UserWarning) as caught:
        loaded = load_board_dir(board, project_dir=tmp_path)
    messages = " | ".join(str(warning.message) for warning in caught)
    assert "card 'one-card'" in messages
    assert "'gone.md'" in messages
    assert "'also/gone.txt'" in messages

    card = loaded["columns"][0]["cards"][0]
    assert [artifact["target"] for artifact in card["artifacts"]] == [
        "gone.md",
        "also/gone.txt",
    ]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        config = _configure(tmp_path, {"source": "board"})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    assert [
        artifact["href"] for artifact in active["columns"][0]["cards"][0]["artifacts"]
    ] == ["", ""]


def test_a_doc_without_a_published_page_warns_at_build(tmp_path: Path) -> None:
    """A ``doc:`` promises a page; when no page exists, the build says so.

    The file is real but nothing publishes it — not the card's directory,
    not a docs source. A ``file:`` target in the same place stays silent:
    it promised a file in the repository, and that promise holds.
    """
    board = _make_board(tmp_path)
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "notes.md").write_text("# n", encoding="utf-8")
    (tmp_path / "folio").mkdir()
    (tmp_path / "folio" / "x.py").write_text("x = 1\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: research/notes.md
          - file: folio/x.py
        ---
        """,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = _configure(tmp_path, {"source": "board"})
    unpublished = [
        str(warning.message)
        for warning in caught
        if "no published page" in str(warning.message)
    ]
    assert len(unpublished) == 1
    assert "card 'one-card'" in unpublished[0]
    assert "'research/notes.md'" in unpublished[0]

    # The artifact still renders, unlinked — the warning is the whole cost.
    artifacts = config.extra["kanban"]["columns"][0]["cards"][0]["artifacts"]
    assert [artifact["href"] for artifact in artifacts] == ["", ""]


def test_an_orphan_card_directory_is_reported(tmp_path: Path) -> None:
    """A directory whose card is missing is named, not silently skipped.

    The filename stem names the directory, so a card renamed or deleted
    leaves its directory orphaned and unpublished — the drift shape B pays
    for. Dot and ``_`` prefixes keep their existing meanings and stay quiet.
    """
    board = _make_board(tmp_path)
    ghost = board / "cards" / "ghost"
    ghost.mkdir()
    (ghost / "output.md").write_text("# o", encoding="utf-8")
    (board / "cards" / "_stash").mkdir()
    (board / "cards" / ".verify").mkdir()
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    with pytest.warns(UserWarning) as caught:
        load_board_dir(board, project_dir=tmp_path)
    messages = [str(warning.message) for warning in caught]
    orphaned = [message for message in messages if "ghost" in message]
    assert len(orphaned) == 1
    assert "no card" in orphaned[0]
    assert "ghost.md" in orphaned[0]
    assert not any("_stash" in message or ".verify" in message for message in messages)


def test_a_board_without_card_directories_is_unchanged(tmp_path: Path) -> None:
    """No directory, no derivation: frontmatter order and targets hold.

    The only addition is ``display``, carrying the target as written.
    """
    board = _make_board(tmp_path)
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "notes.md").write_text("# n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: research/notes.md
            label: Research
          - pr: 7
          - url: https://example.com/a
        ---
        """,
    )

    loaded = load_board_dir(board, project_dir=tmp_path)
    assert loaded["columns"][0]["cards"][0]["artifacts"] == [
        {
            "kind": "doc",
            "target": "research/notes.md",
            "label": "Research",
            "display": "research/notes.md",
        },
        {"kind": "pr", "target": "7", "label": "", "display": "7"},
        {
            "kind": "url",
            "target": "https://example.com/a",
            "label": "",
            "display": "https://example.com/a",
        },
    ]


def test_a_card_directory_is_published_whole(tmp_path: Path) -> None:
    """The whole directory travels, not only what `artifacts:` names.

    A prototype page loads its own stylesheet and script, and neither is
    attached — publishing only the named files would put up a page that
    renders as nothing. Two things stay behind: dotfiles, which are session
    scratch by convention, and symlinks, which could otherwise publish a
    file the project does not contain.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    (assets / "nested").mkdir(parents=True)
    (assets / "prototype.html").write_text("<p>x</p>", encoding="utf-8")
    (assets / "prototype.css").write_text("p{color:red}", encoding="utf-8")
    (assets / "nested" / "data.js").write_text("const a = 1", encoding="utf-8")
    (assets / ".hidden").write_text("scratch", encoding="utf-8")
    (assets / ".verify").mkdir()
    (assets / ".verify" / "shot.png").write_bytes(b"\x89PNG")
    outside = tmp_path / "secret.txt"
    outside.write_text("not in the card", encoding="utf-8")
    (assets / "link.txt").symlink_to(outside)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - file: board/cards/one-card/prototype.html
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    builder = _StaticAssetBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert sorted(builder.copied) == [
        "_folio/kanban/one-card/nested/data.js",
        "_folio/kanban/one-card/prototype.css",
        "_folio/kanban/one-card/prototype.html",
    ]
    # Cleared before republishing, so a file deleted from the project stops
    # being served by the next warm build. Compiled pages are owned by the
    # core source manifest, which removes stale routes independently.
    assert builder.removed == ["_folio/kanban"]


def test_disabling_kanban_removes_its_warm_static_artifacts(tmp_path: Path) -> None:
    builder = _StaticAssetBuilder()
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})

    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.removed == ["_folio/kanban"]
    assert builder.copied == []


def test_a_card_markdown_is_built_as_a_page(tmp_path: Path) -> None:
    """A markdown sibling is compiled by folio, not served as source.

    The kanban plugin contributes it to Folio's document-source hook. It is
    compiled later by the core build, so search, mirrors, llms output,
    incremental cleanup, link validation, and local images all use the same
    machinery as ordinary docs. An underscore opts out, matching
    `_TEMPLATE.md`.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "compared.md").write_text(
        "# A very long heading nobody wants in a sidebar\n\nBody.\n", encoding="utf-8"
    )
    (assets / "loose-note.md").write_text("# Loose\n", encoding="utf-8")
    (assets / "_scratch.md").write_text("# Scratch\n", encoding="utf-8")
    (assets / "_drafts").mkdir()
    (assets / "_drafts" / "inner.md").write_text("# Draft\n", encoding="utf-8")
    (assets / "prototype.html").write_text("<p>x</p>", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: board/cards/one-card/compared.md
            label: Five layouts compared
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board", "routes": {"docs": False}})
    documents = kanban_plugin.collect_docs(config=config)

    assert [(document.source.name, document.route) for document in documents] == [
        ("compared.md", "kanban/cards/one-card/compared"),
        ("loose-note.md", "kanban/cards/one-card/loose-note"),
    ]
    # Board output, not documentation: every contributed page stays out of
    # the docs sidebar while keeping route, search, mirrors, and llms output.
    assert all(document.unlisted for document in documents)

    builder = _StaticAssetBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)
    # `routes.docs: false` suppresses the board page; the folder indexes over
    # the contributed documents are still generated (covered in their own
    # tests below).
    assert sorted(builder.pages) == [
        "kanban/cards/index",
        "kanban/cards/one-card/index",
        "kanban/index",
    ]
    assert builder.meta == {}
    assert sorted(builder.copied) == [
        "_folio/kanban/one-card/_drafts/inner.md",
        "_folio/kanban/one-card/_scratch.md",
        "_folio/kanban/one-card/compared.md",
        "_folio/kanban/one-card/loose-note.md",
        "_folio/kanban/one-card/prototype.html",
    ]


def test_card_pages_are_delisted_from_the_built_sidebar(tmp_path: Path) -> None:
    """The generated _meta.ts hides card pages and every folder above them.

    Nextra lists content pages by default, so leaving card routes out of the
    meta would not delist them — and the generated card indexes are not docs
    at all. The `cards/` folder, the card folder, and each page must carry
    `{"display": "hidden"}` in the exact TS the build writes, while an
    authored doc stays listed: the kanban folder itself hides only while
    nothing authored sits in it. Same result with the board's docs page on:
    `collect_docs` ignores `routes.docs` by design.
    """
    import re

    from folio_docs.build import _collect_plugin_docs
    from folio_docs.docs.sidebar import generate_meta_files
    from folio_docs.parser.markdown_parser import MarkdownResult
    from folio_docs.plugin import PluginManager

    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "compared.md").write_text("# Compared\n\nBody.\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    def hidden(ts_content: str, slug: str) -> bool:
        return bool(
            re.search(
                rf'"{re.escape(slug)}":\s*\{{\s*"display":\s*"hidden",?\s*\}}',
                ts_content,
                re.DOTALL,
            )
        )

    for docs_route in (False, True):
        config = _configure(
            tmp_path, {"source": "board", "routes": {"docs": docs_route}}
        )
        manager = PluginManager()
        manager.register(kanban_plugin, name="folio_agents.integrations.kanban")
        plugin_docs = _collect_plugin_docs(manager, config)
        authored = MarkdownResult(
            route="guide", content="# Guide", frontmatter={"title": "Guide"}
        )
        files = generate_meta_files([], [], [authored, *plugin_docs])

        root_meta = files["_meta.ts"]
        assert '"guide": "Guide"' in root_meta
        # With no authored page under kanban/ the whole folder is unlisted
        # and the root hides it; the cards subtree is hidden at every level.
        assert hidden(root_meta, "kanban")
        assert hidden(files["kanban/_meta.ts"], "cards")
        assert hidden(files["kanban/cards/_meta.ts"], "one-card")
        assert hidden(files["kanban/cards/one-card/_meta.ts"], "compared")

        # Folio's own shape: the kanban guide is authored at `kanban/index`,
        # so the folder holds listed pages and stays visible — the mixed rule
        # — while the fully-unlisted `cards/` subtree below it still hides.
        guide_index = MarkdownResult(
            route="kanban/index",
            content="# Kanban",
            frontmatter={"title": "Kanban"},
        )
        files = generate_meta_files([], [], [authored, guide_index, *plugin_docs])
        root_meta = files["_meta.ts"]
        assert not hidden(root_meta, "kanban")
        assert '"kanban"' in root_meta
        assert hidden(files["kanban/_meta.ts"], "cards")
        assert hidden(files["kanban/cards/_meta.ts"], "one-card")


def test_a_readme_artifact_links_to_its_canonical_directory_url(
    tmp_path: Path,
) -> None:
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    readme = assets / "README.md"
    readme.write_text("# Card report\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: board/cards/one-card/README.md
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    documents = kanban_plugin.collect_docs(config=config)

    assert [(document.source, document.route) for document in documents] == [
        (readme, "kanban/cards/one-card/index")
    ]
    board_data = config.extra["kanban"]
    artifact = board_data["columns"][0]["cards"][0]["artifacts"][0]
    assert artifact["href"] == "/docs/kanban/cards/one-card/"


def test_a_card_with_documents_gets_a_generated_folder_index(
    tmp_path: Path,
) -> None:
    """`/docs/kanban/cards/<id>/` resolves when a card publishes pages below it.

    The compiled documents sit at `kanban/cards/<id>/<stem>`, so the folder
    route is a URL readers reach — trimmed by hand or from a breadcrumb — and
    under `output: export` a missing folder index is a build-time error page,
    not even a clean 404. The plugin fills the hole with a marker-tagged index
    listing the card's documents, titled from each document's first heading.
    The `cards/` folder itself is the same kind of URL, and it resolves to a
    directory of the publishing cards.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "compared.md").write_text(
        "---\ntitle: front\n---\n# A very long internal heading\n\nBody.\n",
        encoding="utf-8",
    )
    (assets / "notes.md").write_text("Plain body, no heading.\n", encoding="utf-8")
    (assets / "prototype.html").write_text("<p>x</p>", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - doc: board/cards/one-card/compared.md
            label: Five layouts compared
          - file: board/cards/one-card/prototype.html
            label: The prototype
          - pr: 7
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    builder = _StaticAssetBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert "kanban/cards/one-card/index" in builder.routes
    index = builder.pages["kanban/cards/one-card/index"]
    assert "generated by the official" in index
    assert "# One card" in index
    # The curated artifact label beats the document's own heading.
    assert 'title="Five layouts compared"' in index
    assert 'title="A very long internal heading"' not in index
    assert 'href="/docs/kanban/cards/one-card/compared/"' in index
    assert 'title="notes"' in index
    assert 'href="/docs/kanban/cards/one-card/notes/"' in index
    # A published prototype opens; a bare PR is a tile without a door.
    assert 'title="The prototype"' in index
    assert 'href="/_folio/kanban/one-card/prototype.html"' in index
    assert '<FeatureCard title="#7" description="#7" icon="git" />' in index
    assert "(/docs/kanban/)" in index

    assert "kanban/cards/index" in builder.routes
    cards_directory = builder.pages["kanban/cards/index"]
    assert "generated by the official" in cards_directory
    assert 'title="One card"' in cards_directory
    assert 'href="/docs/kanban/cards/one-card/"' in cards_directory


def test_a_card_that_writes_its_own_index_is_left_alone(tmp_path: Path) -> None:
    """A card's `README.md` owns the folder route; nothing is generated."""
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "README.md").write_text("# Card report\n", encoding="utf-8")
    (assets / "compared.md").write_text("# Compared\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    # The core pipeline compiled the README at the folder route already; the
    # compiled page carries no marker and must survive emit_assets untouched.
    builder = _StaticAssetBuilder()
    builder.pages["kanban/cards/one-card/index"] = "# Card report\n"
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.pages["kanban/cards/one-card/index"] == "# Card report\n"


def test_a_stale_generated_card_index_is_dropped(tmp_path: Path) -> None:
    """A generated index whose card stopped publishing documents goes away.

    Warm builds keep the workspace, so without the sweep a card renamed or
    emptied on one build would keep serving last build's index forever. The
    sweep also takes marker pages at the pre-`cards/` route shape
    (`kanban/<id>/index`), so a warm workspace crosses the route move without
    serving both generations. Only marker-tagged pages are swept; a user page
    at either shape of route is never touched, and the board's own
    `kanban/index` never matches.
    """
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    builder = _StaticAssetBuilder()
    builder.pages["kanban/cards/gone-card/index"] = kanban_plugin.card_index_mdx(
        {"id": "gone-card", "title": "Gone card"}, [], route_base="/docs"
    )
    builder.pages["kanban/legacy-card/index"] = kanban_plugin.card_index_mdx(
        {"id": "legacy-card", "title": "Legacy card"}, [], route_base="/docs"
    )
    builder.pages["kanban/cards/user-card/index"] = "# Mine\n"
    builder.pages["kanban/legacy-user/index"] = "# Also mine\n"
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert "kanban/cards/gone-card/index" not in builder.pages
    assert "kanban/legacy-card/index" not in builder.pages
    assert builder.pages["kanban/cards/user-card/index"] == "# Mine\n"
    assert builder.pages["kanban/legacy-user/index"] == "# Also mine\n"
    assert "kanban/index" in builder.pages


def test_docs_route_off_still_indexes_publishing_cards(tmp_path: Path) -> None:
    """`routes.docs: false` turns off the board page, not the folder chain.

    Card documents compile under the docs route either way (`collect_docs`
    ignores `routes.docs` by design), so the card keeps its folder index and
    the parent `kanban/` folder resolves to a directory of publishing cards
    rather than to the board the configuration said no to. A stale generated
    index still comes down, and a user page is still untouchable.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "compared.md").write_text("# Compared\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board", "routes": {"docs": False}})
    builder = _StaticAssetBuilder()
    builder.pages["kanban/cards/gone-card/index"] = kanban_plugin.card_index_mdx(
        {"id": "gone-card", "title": "Gone card"}, [], route_base="/docs"
    )
    builder.pages["kanban/cards/user-card/index"] = "# Mine\n"
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert (
        'href="/docs/kanban/cards/one-card/compared/"'
        in (builder.pages["kanban/cards/one-card/index"])
    )
    directory = builder.pages["kanban/index"]
    assert "generated by the official" in directory
    assert 'title="One card"' in directory
    assert 'href="/docs/kanban/cards/one-card/"' in directory
    assert "KanbanBoard" not in directory
    assert "kanban/cards/gone-card/index" not in builder.pages
    assert builder.pages["kanban/cards/user-card/index"] == "# Mine\n"


def test_docs_off_directory_page_defers_to_user_legacy_page(
    tmp_path: Path,
) -> None:
    """A user-authored `kanban.mdx` owns the public route /docs/kanban/.

    The generated directory page compiles at `kanban/index`, which the router
    serves at the same URL, so writing it beside the user page would shadow
    it — the collision `_reject_duplicate_doc_routes` fails loudly for
    collect_docs pages must not arrive silently through emit_assets. A
    directory page persisted from a build before the user wrote theirs comes
    down in the same pass.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "compared.md").write_text("# Compared\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board", "routes": {"docs": False}})
    builder = _StaticAssetBuilder()
    builder.pages["kanban"] = "# My own board writeup\n"
    builder.pages["kanban/index"] = kanban_plugin.kanban_directory_mdx(
        {"title": "Old"},
        {"one-card": {"card": {"id": "one-card", "title": "One card"}}},
        route_base="/docs",
    )
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.pages["kanban"] == "# My own board writeup\n"
    assert "kanban/index" not in builder.pages
    assert "kanban" in builder.routes
    assert "kanban/cards/one-card/index" in builder.pages


def test_a_user_docs_page_at_the_card_route_suppresses_the_index(
    tmp_path: Path,
) -> None:
    """A user page at `kanban/cards/<id>` owns the folder's public URL.

    `_canonical_doc_route` maps `kanban/cards/<id>/index` and
    `kanban/cards/<id>` to the same public route, so the generated index
    would contend with the user's page for one URL. The user wins, and a
    marker index persisted from an earlier build is swept.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "compared.md").write_text("# Compared\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    builder = _StaticAssetBuilder()
    builder.pages["kanban/cards/one-card"] = "# My page about this card\n"
    builder.pages["kanban/cards/one-card/index"] = kanban_plugin.card_index_mdx(
        {"id": "one-card", "title": "One card"}, [], route_base="/docs"
    )
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.pages["kanban/cards/one-card"] == "# My page about this card\n"
    assert "kanban/cards/one-card/index" not in builder.pages


def test_documents_in_subdirectories_get_folder_indexes(tmp_path: Path) -> None:
    """Every folder between a document and the card root resolves.

    A card publishing `sub/deep.md` leaves `kanban/cards/<id>/sub/` reachable
    by trimming, so it gets an index scoped to its subtree; a subdirectory
    that writes its own `README.md` keeps it, exactly as the card root does.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    (assets / "sub" / "nested").mkdir(parents=True)
    (assets / "owned").mkdir()
    (assets / "top.md").write_text("# Top\n", encoding="utf-8")
    (assets / "sub" / "deep.md").write_text("# Deep\n", encoding="utf-8")
    (assets / "sub" / "nested" / "deeper.md").write_text("# Deeper\n", encoding="utf-8")
    (assets / "owned" / "README.md").write_text("# Owned\n", encoding="utf-8")
    (assets / "owned" / "note.md").write_text("# Note\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board"})
    builder = _StaticAssetBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert "kanban/cards/one-card/index" in builder.pages
    assert "kanban/cards/one-card/sub/index" in builder.pages
    assert "kanban/cards/one-card/sub/nested/index" in builder.pages
    # `owned/README.md` compiled at that route already; nothing is generated.
    assert "kanban/cards/one-card/owned/index" not in builder.pages

    sub_index = builder.pages["kanban/cards/one-card/sub/index"]
    assert 'href="/docs/kanban/cards/one-card/sub/deep/"' in sub_index
    assert 'href="/docs/kanban/cards/one-card/sub/nested/deeper/"' in sub_index
    assert "top" not in sub_index


def test_removing_the_kanban_section_sweeps_generated_pages(
    tmp_path: Path,
) -> None:
    builder = _StaticAssetBuilder()
    builder.pages["kanban/index"] = kanban_plugin.docs_page_mdx({"title": "Old"})
    builder.pages["kanban/cards/one-card/index"] = kanban_plugin.card_index_mdx(
        {"id": "one-card", "title": "One card"}, [], route_base="/docs"
    )
    builder.pages["kanban/cards/user-card/index"] = "# Mine\n"
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})

    kanban_plugin.emit_assets(builder=builder, config=config)

    assert sorted(builder.pages) == ["kanban/cards/user-card/index"]


def test_docs_route_off_without_documents_stays_silent(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board", "routes": {"docs": False}})
    builder = _StaticAssetBuilder()
    builder.pages["kanban/index"] = kanban_plugin.kanban_directory_mdx(
        {"title": "Old"},
        {"one-card": {"card": {"id": "one-card", "title": "One card"}}},
        route_base="/docs",
    )
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.pages == {}
    assert builder.routes == set()


def test_a_symlinked_card_directory_is_never_followed(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("# Secret\n", encoding="utf-8")
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    (board / "cards" / "one-card").symlink_to(outside, target_is_directory=True)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "board", "routes": {"docs": False}})
    assert kanban_plugin.collect_docs(config=config) == []

    builder = _StaticAssetBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)
    assert builder.copied == []


def test_an_artifact_cannot_claim_another_cards_directory(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    one = board / "cards" / "one-card"
    two = board / "cards" / "other-card"
    one.mkdir()
    two.mkdir()
    (two / "secret.html").write_text("secret", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        artifacts:
          - file: board/cards/one-card/../other-card/secret.html
        ---
        """,
    )
    _write_card(
        board,
        "other-card",
        """\
        ---
        title: Other card
        status: ideas
        ---
        """,
    )

    config = _configure(tmp_path, {"source": "./board"})
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    assert active["cardDir"] == "board"
    artifact = active["columns"][0]["cards"][0]["artifacts"][0]
    assert artifact["href"] == ""


def test_a_trail_ref_stays_the_ref_it_was_written_as(tmp_path: Path) -> None:
    """A ref renders as the identifier it is, not as a hosting-provider URL.

    A sha used to resolve to ``{repo}/commit/<sha>`` and ``PR #23`` to
    ``{repo}/pull/23``. A sha is already an address and ``git show`` takes
    it, so the board keeps the ref and builds no link. Refs are hand-written
    prose and are never rewritten.
    """
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---

        ## Trail
        - 2026-08-04 @claude (f5fc1b818): a commit sha.
        - 2026-08-05 @claude (PR #23): a pull request.
        - 2026-08-06 @claude (#24): the bare form.
        - 2026-08-07 @claude (see the notes): prose, not an identifier.
        - 2026-08-08 @claude: no ref at all.
        """,
    )
    config = _configure(tmp_path, {"source": "board"})
    trail = config.extra["kanban"]["columns"][0]["cards"][0]["trail"]
    assert [entry["href"] for entry in trail] == ["", "", "", "", ""]
    # Every ref survives verbatim, including the two that used to be links.
    assert [entry["ref"] for entry in trail] == [
        "f5fc1b818",
        "PR #23",
        "#24",
        "see the notes",
        "",
    ]
    # The note is never touched, and the ref stays exactly as authored: the
    # resolved URL is derived data and must not reach board/cards/*.md.
    assert trail[3]["ref"] == "see the notes"
    assert trail[0]["note"] == "a commit sha."

    # And it survives active_kanban's re-normalization pass: no stage of the
    # pipeline puts a link back.
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    replayed = active["columns"][0]["cards"][0]["trail"][0]
    assert replayed["ref"] == "f5fc1b818"
    assert replayed["href"] == ""


def test_milestone_resolves_to_its_roadmap_step(tmp_path: Path) -> None:
    """A card's milestone names the roadmap phase it belongs to.

    The roadmap already deep-links into the board with ``?milestone=``; this
    is the return path, and both halves are declared in the same docs.yaml.
    A bare "0.4" on a card tells a reader nothing.
    """
    board = _make_board(tmp_path)
    for card_id, milestone in (("one", "0.4"), ("two", "9.9"), ("three", "")):
        _write_card(
            board,
            card_id,
            f"""\
            ---
            title: Card {card_id}
            status: ideas
            milestone: "{milestone}"
            ---
            """,
        )
    config = Config(
        project_name="Demo",
        project_dir=str(tmp_path),
        project_repo="https://github.com/acme/demo",
        extra={},
    )
    # The unclaimed 9.9 milestone below now warns against the roadmap's
    # known versions — that is the registry behavior, asserted here so the
    # fixture's warning is expected rather than stray.
    with pytest.warns(
        UserWarning,
        match=r"milestone '9\.9' matches no roadmap phase "
        r"\(cards: two; known: 0\.4, 0\.7\)",
    ):
        kanban_plugin.configure(
            config=config,
            raw_config={
                "kanban": {"source": "board"},
                "roadmap": {
                    "phases": [
                        {
                            "id": "agent-project-os",
                            "version": "0.4",
                            "title": "Project OS",
                        },
                        {"id": "launch", "version": "v0.7", "title": "Launch"},
                    ]
                },
            },
        )
    cards = {
        card["id"]: card
        for column in config.extra["kanban"]["columns"]
        for card in column["cards"]
    }
    # Claimed by a phase: anchor and human name both resolve.
    assert cards["one"]["phase"] == "agent-project-os"
    assert cards["one"]["phaseTitle"] == "Project OS"
    # A milestone no phase claims keeps its milestone and gains no step, so
    # the card renders exactly as it did before.
    assert cards["two"]["milestone"] == "9.9"
    assert cards["two"]["phase"] == ""
    assert cards["three"]["phase"] == ""

    # And it survives active_kanban's re-normalization, which has no view of
    # the roadmap section and so must carry the resolved values through.
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    resolved = {
        card["id"]: card["phase"]
        for column in active["columns"]
        for card in column["cards"]
    }
    assert resolved["one"] == "agent-project-os"


def test_milestone_needs_no_roadmap_section(tmp_path: Path) -> None:
    """No roadmap configured means no step — never a crash, never a guess."""
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one",
        """\
        ---
        title: One
        status: ideas
        milestone: "0.4"
        ---
        """,
    )
    config = _configure(tmp_path, {"source": "board"})
    card = config.extra["kanban"]["columns"][0]["cards"][0]
    assert card["milestone"] == "0.4"
    assert card["phase"] == ""
    assert card["phaseTitle"] == ""


def test_trail_refs_stay_plain_without_a_project_repo(tmp_path: Path) -> None:
    """No repo configured means no link — the ref renders as text."""
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---

        ## Trail
        - 2026-08-04 @claude (f5fc1b818): a commit sha.
        """,
    )
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    kanban_plugin.configure(config=config, raw_config={"kanban": {"source": "board"}})
    trail = config.extra["kanban"]["columns"][0]["cards"][0]["trail"]
    assert trail[0]["ref"] == "f5fc1b818"
    assert trail[0]["href"] == ""


def test_docs_yaml_title_wins_over_board_yaml(tmp_path: Path) -> None:
    _make_board(tmp_path)
    config = _configure(tmp_path, {"source": "board", "title": "Override"})
    assert config.extra["kanban"]["title"] == "Override"


def test_template_files_are_not_cards(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    (board / "cards" / "_TEMPLATE.md").write_text("not a card", encoding="utf-8")
    loaded = load_board_dir(board, project_dir=tmp_path)
    assert all(not column["cards"] for column in loaded["columns"])


@pytest.mark.parametrize(
    ("card_id", "content", "message"),
    [
        (
            "no-status",
            "---\ntitle: X\n---\n",
            "needs a `status:`",
        ),
        (
            "bad-status",
            "---\ntitle: X\nstatus: nope\n---\n",
            "has status 'nope'",
        ),
        (
            "no-title",
            "---\nstatus: ideas\n---\n",
            "needs a `title:`",
        ),
        (
            "no-frontmatter",
            "just prose\n",
            "no frontmatter",
        ),
        (
            "dangling-parent",
            "---\ntitle: X\nstatus: ideas\nparent: ghost\n---\n",
            "parent 'ghost'",
        ),
        (
            "dangling-blocker",
            "---\ntitle: X\nstatus: ideas\nblocked_by: [ghost]\n---\n",
            "blocked_by 'ghost'",
        ),
        (
            "self-blocked",
            "---\ntitle: X\nstatus: ideas\nblocked_by: [self-blocked]\n---\n",
            "cannot block itself",
        ),
        (
            "bad-artifact",
            "---\ntitle: X\nstatus: ideas\nartifacts:\n  - nope: y\n---\n",
            "exactly one kind key",
        ),
        (
            "escaping-artifact",
            "---\ntitle: X\nstatus: ideas\nartifacts:\n  - file: ../outside.md\n---\n",
            "escapes the project",
        ),
    ],
)
def test_board_topology_errors_fail_fast(
    tmp_path: Path, card_id: str, content: str, message: str
) -> None:
    board = _make_board(tmp_path)
    _write_card(board, card_id, content)
    with pytest.raises(ValueError, match=message.replace("[", "\\[")):
        load_board_dir(board, project_dir=tmp_path)


def test_non_slug_filename_fails_fast(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    (board / "cards" / "Not A Slug.md").write_text(
        "---\ntitle: X\nstatus: ideas\n---\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="is not a slug"):
        load_board_dir(board, project_dir=tmp_path)


def test_missing_board_yaml_fails_fast(tmp_path: Path) -> None:
    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True)
    with pytest.raises(ValueError, match="board.yaml"):
        load_board_dir(board, project_dir=tmp_path)


def test_prose_problems_degrade_with_warnings(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    _write_card(
        board,
        "sloppy",
        """\
        ---
        title: Sloppy
        status: doing
        priority: urgent
        ---

        ## Trail
        - someone did something at some point
        """,
    )
    _write_card(
        board,
        "second",
        "---\ntitle: Second\nstatus: doing\n---\n",
    )
    _write_card(
        board,
        "third",
        "---\ntitle: Third\nstatus: doing\n---\n",
    )

    with pytest.warns(UserWarning) as caught:
        loaded = load_board_dir(board, project_dir=tmp_path)

    messages = " | ".join(str(warning.message) for warning in caught)
    assert "trail line does not match" in messages
    assert "unknown priority" in messages
    assert "over its WIP limit" in messages  # 3 cards in doing, limit 2

    doing = next(c for c in loaded["columns"] if c["id"] == "doing")
    sloppy = next(card for card in doing["cards"] if card["id"] == "sloppy")
    assert sloppy["trail"] == [
        {
            "date": "",
            "actor": "",
            "ref": "",
            "note": "- someone did something at some point",
        }
    ]


def test_card_milestone_passes_through(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    _write_card(
        board,
        "vered",
        """\
        ---
        title: Vered
        status: ideas
        milestone: "0.6"
        ---
        """,
    )
    loaded = load_board_dir(board, project_dir=tmp_path)
    cards = {c["id"]: c for col in loaded["columns"] for c in col["cards"]}
    assert cards["vered"]["milestone"] == "0.6"


def test_each_card_links_to_its_own_file(tmp_path: Path) -> None:
    """A card is a file, so the card says where that file is.

    On a published board the browser writes nothing, so "where do I change
    this" has to be answerable from the card itself — and the answer is the
    forge's own editor, authenticated by the session the reader already has.
    """
    board = _make_board(tmp_path)
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )
    config = Config(
        project_name="Demo",
        project_dir=str(tmp_path),
        project_repo="https://github.com/acme/demo",
        project_repo_ref="board",
        extra={},
    )
    kanban_plugin.configure(config=config, raw_config={"kanban": {"source": "board"}})
    card = config.extra["kanban"]["columns"][0]["cards"][0]
    # A path, not a URL, and unaffected by project_repo being set at all.
    assert card["file"] == "board/cards/one-card.md"

    # Survives active_kanban's re-normalization, which rebuilds it.
    active = kanban_plugin.active_kanban(config)
    assert active is not None
    assert active["columns"][0]["cards"][0]["file"] == "board/cards/one-card.md"


def test_a_cards_path_needs_no_repo(tmp_path: Path) -> None:
    """The path is there without a project.repo, because it is not a link.

    This is the case the old behaviour got wrong in both directions: with a
    repo it invented a URL, and without one it offered nothing at all, even
    though the file was sitting right there.
    """
    board = _make_board(tmp_path)
    _write_card(board, "one", "---\ntitle: One\nstatus: ideas\n---\n")
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    kanban_plugin.configure(config=config, raw_config={"kanban": {"source": "board"}})
    card = config.extra["kanban"]["columns"][0]["cards"][0]
    assert card["file"] == "board/cards/one.md"


def test_created_that_is_not_a_date_warns_with_the_file_name(tmp_path: Path) -> None:
    """`created: 2026-8-1` is a string, not a YAML date, and orders as text.

    Text says "2026-8-1" comes after "2026-08-01" and before nothing at all,
    so both the intra-column sort and the board's `created:<...` filter answer
    wrongly about that card. Nothing else validates the field, so this warning
    is the only place the author is told — and it names the file.
    """
    board = _make_board(tmp_path)
    _write_card(
        board,
        "late",
        """\
        ---
        title: Late
        status: doing
        created: 2026-8-1
        ---
        """,
    )

    with pytest.warns(UserWarning, match=r"created '2026-8-1' is not a YYYY-MM-DD"):
        loaded = load_board_dir(board, project_dir=tmp_path)

    # Tolerant reader: the card still loads, it just cannot be ordered by date.
    titles = [card["title"] for column in loaded["columns"] for card in column["cards"]]
    assert "Late" in titles


def test_a_real_iso_created_date_is_silent(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    _write_card(
        board,
        "ontime",
        """\
        ---
        title: On time
        status: doing
        created: 2026-08-01
        ---
        """,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        load_board_dir(board, project_dir=tmp_path)

    assert not [w for w in caught if "created" in str(w.message)]


def test_card_type_passes_through(tmp_path: Path) -> None:
    """`type:` is machine state like milestone — free vocabulary, no validation."""
    board = _make_board(tmp_path)
    _write_card(
        board,
        "typed",
        """\
        ---
        title: Typed
        status: ideas
        type: bug
        ---
        """,
    )
    loaded = load_board_dir(board, project_dir=tmp_path)
    cards = {c["id"]: c for col in loaded["columns"] for c in col["cards"]}
    assert cards["typed"]["type"] == "bug"


def test_size_and_source_are_carried_from_cardfile_frontmatter(tmp_path: Path) -> None:
    board = _make_board(tmp_path)
    _write_card(
        board,
        "sized",
        """\
        ---
        title: Sized
        status: ideas
        size: m
        source: example/project#feat/cardfile-board
        assignee: [ana, bo]
        ---
        """,
    )
    loaded = load_board_dir(board, project_dir=tmp_path)
    cards = {c["id"]: c for col in loaded["columns"] for c in col["cards"]}
    card = cards["sized"]
    assert card["size"] == "m"  # carried raw; normalization uppercases later
    assert card["source"] == "example/project#feat/cardfile-board"
    assert card["assignee"] == ["ana", "bo"]


@pytest.mark.parametrize("size_line", ["size: enormous", "size: 5"])
def test_a_size_outside_the_scale_is_a_hard_error_naming_the_file(
    tmp_path: Path, size_line: str
) -> None:
    board = _make_board(tmp_path)
    _write_card(
        board,
        "bad-size",
        f"---\ntitle: Bad\nstatus: ideas\n{size_line}\n---\n",
    )
    with pytest.raises(ValueError, match=r"bad-size.*use S, M, L, or XL"):
        load_board_dir(board, project_dir=tmp_path)


def test_comments_parse_and_a_malformed_line_warns(tmp_path: Path) -> None:
    """`## Comments` is the trail's grammar minus the ref — and the same
    tolerance: a bullet that misses the grammar warns and still joins the
    thread as prose."""
    board = _make_board(tmp_path)
    _write_card(
        board,
        "threaded",
        """\
        ---
        title: Threaded
        status: ideas
        ---

        A card people argue about.

        ## Comments
        - 2026-08-18 @peter: should the cadence bind to the milestone?
        - 2026-08-18 @claude: yes — see criterion 4
        - just a stray thought
        """,
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        loaded = load_board_dir(board, project_dir=tmp_path)

    card = loaded["columns"][0]["cards"][0]
    assert card["comments"] == [
        {
            "date": "2026-08-18",
            "actor": "peter",
            "text": "should the cadence bind to the milestone?",
        },
        {"date": "2026-08-18", "actor": "claude", "text": "yes — see criterion 4"},
        # The tolerant fallback keeps the whole line, bullet included —
        # exactly what the trail does with a malformed entry.
        {"date": "", "actor": "", "text": "- just a stray thought"},
    ]
    messages = [str(warning.message) for warning in caught]
    assert any("comment line does not match" in message for message in messages)
    # A card without the section carries the empty thread, silently — on
    # its own board, so the malformed card above cannot lend its warning.
    quiet = _make_board(tmp_path / "second")
    _write_card(
        quiet,
        "silent",
        """\
        ---
        title: Silent
        status: ideas
        ---
        """,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        loaded = load_board_dir(quiet, project_dir=tmp_path / "second")
    assert loaded["columns"][0]["cards"][0]["comments"] == []


def test_docs_kanban_forwards_to_the_public_board(tmp_path: Path) -> None:
    """With a public board, `/docs/kanban/` redirects instead of listing.

    Card pages are read from the board itself, so the folder above them stops
    indexing them — but the route must still resolve (a hole above a published
    document fails the export). The generated page forwards to the configured
    public route, query and hash intact, written relative so a site base path
    survives. The marker stays, so warm builds refresh and sweeps still work.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "note.md").write_text("# Note\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    for public, to in (
        ("/", "../../"),
        ("/board", "../../board/"),
        (True, "../../kanban/"),
    ):
        config = _configure(
            tmp_path, {"source": "board", "routes": {"docs": False, "public": public}}
        )
        builder = _StaticAssetBuilder()
        kanban_plugin.emit_assets(builder=builder, config=config)
        page = builder.pages["kanban/index"]
        assert "generated by the official" in page
        assert 'from "@/components/redirect-page"' in page
        assert f'<RedirectPage to="{to}" />' in page
        assert "KanbanBoard" not in page
        assert "FeatureCard" not in page
        assert "kanban/index" in builder.routes


def test_an_authored_page_at_docs_kanban_wins_over_the_redirect(
    tmp_path: Path,
) -> None:
    """The kanban guide's own index owns `/docs/kanban/`; the redirect yields.

    Folio's docs author a page at `kanban/index`, the route the forwarding
    page compiles at. The authored page carries no marker, so the plugin must
    leave it exactly as written — no overwrite, no stale redirect beside it —
    while the card pages keep publishing below it.
    """
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "note.md").write_text("# Note\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(
        tmp_path, {"source": "board", "routes": {"docs": False, "public": True}}
    )
    builder = _StaticAssetBuilder()
    builder.pages["kanban/index"] = "# The kanban guide\n"
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.pages["kanban/index"] == "# The kanban guide\n"
    assert "kanban/cards/index" in builder.pages
    assert "kanban/cards/one-card/index" in builder.pages


def test_the_kanban_redirect_climbs_the_configured_docs_route(
    tmp_path: Path,
) -> None:
    """The redirect's relative path is counted from the docs route base."""
    board = _make_board(tmp_path)
    assets = board / "cards" / "one-card"
    assets.mkdir()
    (assets / "note.md").write_text("# Note\n", encoding="utf-8")
    _write_card(
        board,
        "one-card",
        """\
        ---
        title: One card
        status: ideas
        ---
        """,
    )

    config = _configure(
        tmp_path, {"source": "board", "routes": {"docs": False, "public": True}}
    )
    config.docs_route_base = "/handbook/reference"
    builder = _StaticAssetBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)
    assert '<RedirectPage to="../../../kanban/" />' in builder.pages["kanban/index"]


def test_board_yaml_icons_map_resolves_onto_cards(tmp_path: Path) -> None:
    """An `icons:` tag map in board.yaml puts the icon on every card wearing
    the tag; unmapped cards carry an empty icon and a malformed map warns
    without breaking the board."""
    from folio_agents.integrations.kanban import normalize_kanban

    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True)
    (board / "board.yaml").write_text(
        'title: "B"\nicons:\n  casa: "🏠"\n  folio: "📁"\n'
        "columns:\n  - id: backlog\n    title: Backlog\n",
        encoding="utf-8",
    )
    (board / "cards" / "a.md").write_text(
        "---\ntitle: A\nstatus: backlog\ntags: [casa]\n---\n", encoding="utf-8"
    )
    (board / "cards" / "b.md").write_text(
        "---\ntitle: B\nstatus: backlog\ntags: [otros]\n---\n", encoding="utf-8"
    )
    kanban = normalize_kanban({"source": "board"}, project_dir=tmp_path)
    icons = {
        card["title"]: card["icon"]
        for column in kanban["columns"]
        for card in column["cards"]
    }
    assert icons == {"A": "🏠", "B": ""}
    tags = {
        card["title"]: card["iconTag"]
        for column in kanban["columns"]
        for card in column["cards"]
    }
    assert tags == {"A": "casa", "B": ""}
    assert kanban["icons"] == {"casa": "🏠", "folio": "📁"}


def test_a_malformed_icons_map_warns_and_renders_nothing(tmp_path: Path) -> None:
    from folio_agents.integrations.kanban import normalize_kanban

    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True)
    (board / "board.yaml").write_text(
        'title: "B"\nicons: nope\ncolumns:\n  - id: backlog\n    title: Backlog\n',
        encoding="utf-8",
    )
    (board / "cards" / "a.md").write_text(
        "---\ntitle: A\nstatus: backlog\ntags: [casa]\n---\n", encoding="utf-8"
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        kanban = normalize_kanban({"source": "board"}, project_dir=tmp_path)
    assert any("`icons:` must be a mapping" in str(w.message) for w in caught)
    assert kanban["columns"][0]["cards"][0]["icon"] == ""
