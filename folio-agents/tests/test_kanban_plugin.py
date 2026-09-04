from __future__ import annotations

import warnings

from pathlib import Path

import pytest

from folio_docs.config import Config
from folio_agents.integrations import kanban as kanban_plugin
from folio_agents.milestones import resolve_roadmap_phases


class _PageBuilder:
    """AssetBuilder stand-in that also supports reading page content."""

    def __init__(
        self,
        pages: dict[str, str] | None = None,
        *,
        readable: bool = True,
    ) -> None:
        self.pages: dict[str, str] = dict(pages or {})
        self.written_pages: list[str] = []
        self.removed_pages: list[str] = []
        self.routes: set[str] = set()
        if not readable:
            self.read_page = None  # type: ignore[assignment]

    def page_exists(self, route: str) -> bool:
        return route in self.pages

    def read_page(self, route: str) -> str:
        return self.pages[route]

    def write_page(self, route: str, content: str) -> None:
        self.written_pages.append(route)
        self.pages[route] = content

    def remove_page(self, route: str) -> None:
        self.removed_pages.append(route)
        self.pages.pop(route, None)

    def register_route(self, route: str) -> None:
        self.routes.add(route)


def _configure(tmp_path: Path, kanban_section: dict) -> Config:
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    kanban_plugin.configure(config=config, raw_config={"kanban": kanban_section})
    return config


def _cardfile_kanban(tmp_path, cards=()):
    """A minimal real cardfile board; returns the kanban config section."""
    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True, exist_ok=True)
    (board / "board.yaml").write_text(
        'title: "Board"\ncolumns:\n  - id: backlog\n    title: Backlog\n'
        "  - id: in-progress\n    title: In progress\n  - id: done\n    title: Done\n"
    )
    for stem, front in cards:
        (board / "cards" / f"{stem}.md").write_text(f"---\n{front}---\n")
    return {"source": "board"}


def _product_board(root: Path, card_id: str, title: str) -> None:
    (root / "cards").mkdir(parents=True)
    (root / "board.yaml").write_text(
        "columns:\n  - id: backlog\n    title: Backlog\n",
        encoding="utf-8",
    )
    (root / "cards" / f"{card_id}.md").write_text(
        f'---\ntitle: "{title}"\nstatus: backlog\nmilestone: "0.1"\n---\n',
        encoding="utf-8",
    )


def test_kanban_configure_defaults_without_key_stays_inert(tmp_path: Path) -> None:
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    kanban_plugin.configure(config=config, raw_config={})
    assert config.extra == {}

    # ...and the build hooks emit nothing (registry/builder are never used).
    kanban_plugin.register_extensions(registry=None, config=config)
    kanban_plugin.emit_assets(builder=None, config=config)


def test_kanban_configure_preserves_description(tmp_path: Path) -> None:
    # register_extensions() reads the band description back from
    # config.extra["kanban"]; normalization must not drop it.
    kanban_section = _cardfile_kanban(tmp_path)
    kanban_section["description"] = "  Band copy.  "
    config = _configure(tmp_path, kanban_section)
    assert config.extra["kanban"]["description"] == "Band copy."


def test_named_sources_are_independent_canvases_and_match_their_roadmaps(
    tmp_path: Path,
) -> None:
    _product_board(tmp_path / "folio-docs" / "board", "docs-release", "Docs")
    _product_board(tmp_path / "folio-agents" / "board", "agents-release", "Agents")
    config = Config(project_name="Folio", project_dir=str(tmp_path), extra={})
    kanban_plugin.configure(
        config=config,
        raw_config={
            "kanban": {
                "sources": {
                    "docs": "folio-docs/board",
                    "agents": "folio-agents/board",
                }
            },
            "roadmap": {
                "phases": [
                    {"id": "docs-01", "project": "docs", "version": "0.1"},
                    {"id": "agents-01", "project": "agents", "version": "0.1"},
                ]
            },
        },
    )

    cards = {
        card["id"]: card
        for column in config.extra["kanban"]["columns"]
        for card in column["cards"]
    }
    assert cards["docs-release"]["project"] == "docs"
    assert cards["docs-release"]["phase"] == "docs-01"
    assert cards["agents-release"]["project"] == "agents"
    assert cards["agents-release"]["phase"] == "agents-01"
    assert set(config.extra["kanban"]["cardDirs"]) == {"docs", "agents"}


def _board_with_cards(cards: list[dict]) -> dict:
    """The minimal ``{"columns": [{"cards": [...]}]}`` shape the resolver walks."""
    return {"columns": [{"cards": cards}]}


def test_an_unclaimed_milestone_warns_grouped_naming_cards_and_versions() -> None:
    kanban = _board_with_cards(
        [
            {"title": "A", "id": "a", "milestone": "0.9"},
            {"title": "B", "id": "b", "milestone": "0.9"},
            {"title": "C", "id": "c", "milestone": "0.3"},
        ]
    )
    roadmap = {"phases": [{"id": "p3", "title": "Three", "version": "0.3"}]}
    with pytest.warns(
        UserWarning,
        match=r"milestone '0\.9' matches no roadmap phase "
        r"\(cards: a, b; known: 0\.3\)",
    ) as caught:
        resolve_roadmap_phases(kanban, raw_roadmap=roadmap)
    # Exactly one warning for the two 0.9 cards, none for the claimed 0.3.
    assert len(caught) == 1


def test_an_unclaimed_card_without_an_id_is_named_by_its_title() -> None:
    kanban = _board_with_cards([{"title": "Ship it", "milestone": "0.9"}])
    roadmap = {"phases": [{"id": "p3", "title": "Three", "version": "0.3"}]}
    with pytest.warns(UserWarning, match=r"\(cards: Ship it; known: 0\.3\)"):
        resolve_roadmap_phases(kanban, raw_roadmap=roadmap)


def test_claimed_no_roadmap_and_versionless_phases_stay_silent() -> None:
    for raw_roadmap in (
        None,
        {},
        {"phases": []},
        {"phases": [{"id": "p", "title": "T"}]},
    ):
        kanban = _board_with_cards(
            [{"title": "A", "id": "a", "milestone": "0.9"}, {"title": "B", "id": "b"}]
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            resolve_roadmap_phases(kanban, raw_roadmap=raw_roadmap)
    # A claimed milestone is silent too — and so is a card with no milestone
    # key sitting next to a roadmap that could have claimed one.
    kanban = _board_with_cards(
        [{"title": "A", "id": "a", "milestone": "0.3"}, {"title": "B", "id": "b"}]
    )
    roadmap = {"phases": [{"id": "p3", "title": "Three", "version": "v0.3"}]}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        resolve_roadmap_phases(kanban, raw_roadmap=roadmap)
    assert kanban["columns"][0]["cards"][0]["phase"] == "p3"  # v-prefix matches


def test_a_tracked_card_never_claims_another_products_phase() -> None:
    kanban = _board_with_cards(
        [{"title": "Docs", "id": "docs", "project": "docs", "milestone": "0.4"}]
    )
    roadmap = {
        "phases": [
            {"id": "agents-04", "project": "agents", "version": "0.4"}
        ]
    }

    with pytest.warns(UserWarning, match="matches no roadmap phase"):
        resolve_roadmap_phases(kanban, raw_roadmap=roadmap)

    assert "phase" not in kanban["columns"][0]["cards"][0]


def test_retired_inline_columns_are_a_loud_error(tmp_path):
    """A `columns:` key stops the build with the cardfile pointer instead of
    rendering a board nobody can operate."""
    with pytest.raises(ValueError, match=r"inline `columns:` boards were removed"):
        kanban_plugin.normalize_kanban({"columns": []}, project_dir=tmp_path)


def test_retired_single_file_source_is_a_loud_error(tmp_path):
    """A `source:` file is rejected; only the current directory format exists."""
    (tmp_path / "board.yaml").write_text("columns: []\n")
    with pytest.raises(ValueError, match=r"must name a board directory"):
        kanban_plugin.normalize_kanban({"source": "board.yaml"}, project_dir=tmp_path)


def test_kanban_section_without_source_is_a_loud_error(tmp_path):
    """A kanban section without `source:` used to render an empty board
    silently; now it says what is missing."""
    with pytest.raises(
        ValueError, match=r"needs `source:` pointing at a board directory"
    ):
        kanban_plugin.normalize_kanban(
            {"routes": {"public": True}}, project_dir=tmp_path
        )


def test_bare_kanban_section_is_a_loud_error(tmp_path):
    """`board:` with no mapping under it is one typo away from a retired
    format; it gets the same missing-source error, not a silent empty board."""
    with pytest.raises(
        ValueError, match=r"needs `source:` pointing at a board directory"
    ):
        kanban_plugin.normalize_kanban(None, project_dir=tmp_path)


def test_kanban_missing_source_file_is_a_loud_error(tmp_path: Path) -> None:
    resolved = (tmp_path / "missing-board").resolve()

    with pytest.raises(ValueError, match="no cardfile board at") as excinfo:
        _configure(tmp_path, {"source": "missing-board"})

    assert str(resolved) in str(excinfo.value)


def test_kanban_card_without_title_is_dropped_with_warning(tmp_path: Path) -> None:
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    config.extra["kanban"] = {
        "columns": [
            {
                "title": "To Do",
                "cards": [{"description": "no title"}, {"title": "Kept"}],
            }
        ]
    }

    with pytest.warns(UserWarning, match="dropping a card without a title"):
        kanban = kanban_plugin.active_kanban(config)

    cards = kanban["columns"][0]["cards"]
    assert [card["title"] for card in cards] == ["Kept"]


def test_kanban_invalid_wip_limit_is_ignored_with_warning(tmp_path: Path) -> None:
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    config.extra["kanban"] = {"columns": [{"title": "To Do", "limit": "four"}]}

    with pytest.warns(UserWarning, match="invalid WIP limit"):
        kanban = kanban_plugin.active_kanban(config)

    assert kanban["columns"][0]["limit"] is None


def test_kanban_unsafe_card_link_fails_loudly(tmp_path: Path) -> None:
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    config.extra["kanban"] = {
        "columns": [
            {
                "title": "To Do",
                "cards": [{"title": "Bad link", "link": "javascript:alert(1)"}],
            }
        ]
    }

    with pytest.raises(ValueError, match="http\\(s\\) URL or a relative path"):
        kanban_plugin.active_kanban(config)


def test_kanban_emit_assets_writes_docs_page_and_registers_route(
    tmp_path: Path,
) -> None:
    config = _configure(tmp_path, _cardfile_kanban(tmp_path))

    builder = _PageBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert "kanban/index" in builder.routes
    page = builder.pages["kanban/index"]
    assert 'import { KanbanBoard } from "@/components/kanban-board"' in page
    assert "# Board" in page
    assert "<KanbanBoard />" in page


def test_kanban_emit_assets_respects_docs_route_opt_out(tmp_path: Path) -> None:
    kanban_section = _cardfile_kanban(tmp_path)
    kanban_section["routes"] = {"docs": False}
    config = _configure(tmp_path, kanban_section)

    builder = _PageBuilder()
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.routes == set()
    assert builder.pages == {}


def test_kanban_emit_assets_never_overwrites_user_page(tmp_path: Path) -> None:
    config = _configure(tmp_path, _cardfile_kanban(tmp_path))

    builder = _PageBuilder(pages={"kanban": "# My hand-written board\n"})
    kanban_plugin.emit_assets(builder=builder, config=config)

    # The route stays registered for link-checking, the page stays untouched.
    assert "kanban" in builder.routes
    assert builder.written_pages == []
    assert builder.pages["kanban"] == "# My hand-written board\n"


def test_kanban_emit_assets_refreshes_stale_generated_page(tmp_path: Path) -> None:
    kanban_section = _cardfile_kanban(tmp_path)
    kanban_section["title"] = "Project Board"
    config = _configure(tmp_path, kanban_section)
    stale = kanban_plugin.docs_page_mdx({"title": "Old Title"})

    builder = _PageBuilder(pages={"kanban/index": stale})
    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.written_pages == ["kanban/index"]
    assert "# Project Board" in builder.pages["kanban/index"]

    # Without read_page support the existing page is left alone.
    unreadable = _PageBuilder(pages={"kanban/index": stale}, readable=False)
    kanban_plugin.emit_assets(builder=unreadable, config=config)
    assert unreadable.written_pages == []


def test_kanban_emit_assets_refreshes_stale_page_with_real_site_builder(
    tmp_path: Path,
) -> None:
    """Warm-build refresh works against folio's real SiteBuilder.

    Regression test: SiteBuilder previously exposed no ``read_page``, so the
    marker-based write-if-changed branch was dead in real builds and a title
    change kept serving the stale generated page until a --clean build.
    """
    from folio_docs.docs.site_builder import SiteBuilder

    def _builder(config: Config) -> SiteBuilder:
        return SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    kanban_a = _cardfile_kanban(tmp_path)
    kanban_a["title"] = "Board A"
    config = _configure(tmp_path, kanban_a)
    kanban_plugin.emit_assets(builder=_builder(config), config=config)

    page_path = tmp_path / "build" / "content" / "kanban" / "index.mdx"
    assert "# Board A" in page_path.read_text(encoding="utf-8")

    # Second (warm) build with a changed title: the persistent content dir
    # still holds the old page, and the plugin must refresh it in place.
    kanban_b = _cardfile_kanban(tmp_path)
    kanban_b["title"] = "Board B"
    reconfigured = _configure(tmp_path, kanban_b)
    kanban_plugin.emit_assets(builder=_builder(reconfigured), config=reconfigured)

    refreshed = page_path.read_text(encoding="utf-8")
    assert "# Board B" in refreshed
    assert "Board A" not in refreshed


def test_kanban_emit_assets_removes_generated_page_when_docs_route_disabled(
    tmp_path: Path,
) -> None:
    generated = kanban_plugin.docs_page_mdx({"title": "Old Board"})
    kanban_section = _cardfile_kanban(tmp_path)
    kanban_section["routes"] = {"docs": False}
    config = _configure(tmp_path, kanban_section)

    builder = _PageBuilder(pages={"kanban/index": generated})
    kanban_plugin.emit_assets(builder=builder, config=config)

    # The persisted generated page is dropped so warm builds stop
    # publishing it; the route is no longer declared live.
    assert builder.removed_pages == ["kanban/index"]
    assert builder.pages == {}
    assert builder.routes == set()

    # A user-authored page at the same route (no marker) is never removed.
    user_builder = _PageBuilder(pages={"kanban": "# My hand-written board\n"})
    kanban_plugin.emit_assets(builder=user_builder, config=config)
    assert user_builder.removed_pages == []
    assert user_builder.pages["kanban"] == "# My hand-written board\n"

    # A builder that cannot read pages leaves the page alone (content is
    # unknown, so it might be user-authored).
    unreadable = _PageBuilder(pages={"kanban/index": generated}, readable=False)
    kanban_plugin.emit_assets(builder=unreadable, config=config)
    assert unreadable.removed_pages == []


def test_kanban_emit_assets_migrates_its_legacy_sibling_page(tmp_path: Path) -> None:
    generated = kanban_plugin.docs_page_mdx({"title": "Old Board"})
    config = _configure(tmp_path, _cardfile_kanban(tmp_path))
    builder = _PageBuilder(pages={"kanban": generated})

    kanban_plugin.emit_assets(builder=builder, config=config)

    assert builder.removed_pages == ["kanban"]
    assert builder.written_pages == ["kanban/index"]
    assert "kanban" not in builder.pages
    assert "kanban/index" in builder.pages


def test_kanban_docs_page_escapes_markdown_link_syntax_in_title() -> None:
    page = kanban_plugin.docs_page_mdx(
        {"title": "[click me](javascript:alert(document.domain))"}
    )

    # The brackets are backslash-escaped so MDX renders literal text instead
    # of an <a href="javascript:..."> link inside the generated heading.
    assert "# \\[click me\\](javascript:alert(document.domain))" in page
    assert "# [click me](" not in page


def test_active_kanban_renormalizes_plugin_overridden_columns(tmp_path: Path) -> None:
    """Overrides of config.extra['kanban'] are pulled back onto the contract.

    Project plugins may replace the extra entry after configure() with
    partial column/card shapes; active_kanban must not pass those verbatim
    into lib/kanban-data.ts, where kanban-board.tsx dereferences card.tags
    and column.cards unguarded.
    """
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    config.extra["kanban"] = {
        "title": "  Overridden  ",
        "columns": [
            {"id": "todo", "title": "Todo", "cards": [{"title": "x"}, "bare string"]},
            "not a column",
        ],
    }

    with pytest.warns(UserWarning):
        kanban = kanban_plugin.active_kanban(config)

    assert kanban is not None
    assert kanban["title"] == "Overridden"
    # The malformed column is dropped; the partial card gains the full
    # KanbanCard shape and the non-mapping card is dropped.
    assert kanban["columns"] == [
        {
            "id": "todo",
            "title": "Todo",
            "limit": None,
            "cards": [
                {
                    "id": "x",
                    "title": "x",
                    "description": "",
                    "tags": [],
                    "assignee": [],
                    "track": "",
                    "project": "",
                    "type": "",
                    "size": "",
                    "icon": "",
                    "iconTag": "",
                    "source": "",
                    "link": "",
                    "priority": "",
                    "parent": "",
                    "blocked_by": [],
                    "created": "",
                    "milestone": "",
                    "artifacts": [],
                    "criteria": [],
                    "trail": [],
                    "comments": [],
                    "phase": "",
                    "phaseTitle": "",
                    "file": "",
                }
            ],
        }
    ]

    # A non-list columns override degrades to an empty board, not a crash.
    config.extra["kanban"] = {"columns": {"todo": []}}
    kanban = kanban_plugin.active_kanban(config)
    assert kanban is not None
    assert kanban["columns"] == []


def test_kanban_registers_component_with_compact_props(tmp_path: Path) -> None:
    from folio_docs.extensions import ExtensionRegistry

    config = _configure(tmp_path, _cardfile_kanban(tmp_path))
    registry = ExtensionRegistry()
    kanban_plugin.register_extensions(registry=registry, config=config)

    props = registry.components["KanbanBoard"].props
    assert props["compact"] == "boolean | undefined"
    assert props["maxCardsPerColumn"] == "number | undefined"


def test_the_public_view_opts_the_board_into_workspace_mode(tmp_path: Path) -> None:
    """Only the plugin's emitted public view page turns workspace mode on.

    The same `KanbanBoard` renders in three contexts — the standalone
    public page, docs-prose embeds, and compact miniatures — and only the
    first is an app: the plugin passes `workspace: true` on the view block
    it emits, and to the layout, whose vertical frame padding would
    otherwise make the viewport-height section scroll the page by exactly
    that padding. Docs embeds never receive the prop, so they keep the
    in-flow default.
    """
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    kanban_section = _cardfile_kanban(tmp_path)
    kanban_section["routes"] = {"public": True}
    config = _configure(tmp_path, kanban_section)
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)

    view = registry.views["/kanban"]
    board_block = view.slots["main"][0]
    assert board_block.props["workspace"] is True
    assert view.props["workspace"] is True
    # The prop is part of the component's declared surface.
    assert (
        registry.components["KanbanBoard"].props["workspace"] == "boolean | undefined"
    )


def test_card_type_normalizes_to_string(tmp_path: Path) -> None:
    """`type` reaches the emitted payload as a stripped string; a non-scalar
    warns and degrades to empty rather than failing the build."""
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    config.extra["kanban"] = {
        "title": "Board",
        "columns": [
            {
                "id": "todo",
                "title": "Todo",
                "cards": [
                    {"title": "typed", "type": " bug "},
                    {"title": "untyped"},
                    {"title": "weird", "type": {"not": "scalar"}},
                ],
            },
        ],
    }
    with pytest.warns(UserWarning, match="type"):
        kanban = kanban_plugin.active_kanban(config)
    cards = kanban["columns"][0]["cards"]
    assert cards[0]["type"] == "bug"
    assert cards[1]["type"] == ""
    assert cards[2]["type"] == ""


def test_emitted_interface_carries_type(tmp_path: Path) -> None:
    from folio_agents.integrations.kanban import KANBAN_TYPES

    assert "  type: string\n" in KANBAN_TYPES
    assert "  track: string\n" in KANBAN_TYPES
    assert "  assignee: string[]\n" in KANBAN_TYPES
    assert "  size: string\n" in KANBAN_TYPES
    assert "  source: string\n" in KANBAN_TYPES


def _normalize_one(raw_card: dict) -> dict:
    """One card through the real normalization path.

    active_kanban re-runs _normalize_card on whatever sits in
    config.extra["kanban"], so this exercises the same code every board
    format funnels through.
    """
    config = Config(project_name="Demo", extra={})
    config.extra["kanban"] = {
        "title": "Board",
        "columns": [{"id": "todo", "title": "Todo", "cards": [raw_card]}],
    }
    kanban = kanban_plugin.active_kanban(config)
    assert kanban is not None
    return kanban["columns"][0]["cards"][0]


def test_track_is_a_free_vocabulary_workstream() -> None:
    """A card's own `track` is a workstream inside its project, not the project.

    The multi-source projection used to overwrite it with the name of the
    source the card came from; that lands in `project` now and this survives.
    """
    assert _normalize_one({"title": "A", "track": " agents "})["track"] == "agents"
    assert _normalize_one({"title": "A"})["track"] == ""


def test_track_qualified_milestones_resolve_independently() -> None:
    kanban = _board_with_cards(
        [
            {"title": "Docs", "milestone": "docs-0.3"},
            {"title": "Agents", "milestone": "agents-0.1"},
        ]
    )
    roadmap = {
        "phases": [
            {
                "id": "docs",
                "title": "Docs",
                "version": "0.3",
                "milestone": "docs-0.3",
            },
            {
                "id": "agents",
                "title": "Agents",
                "version": "0.1",
                "milestone": "agents-0.1",
            },
        ]
    }

    resolve_roadmap_phases(kanban, raw_roadmap=roadmap)

    cards = kanban["columns"][0]["cards"]
    assert [card["phase"] for card in cards] == ["docs", "agents"]


def test_assignee_normalizes_both_forms_to_a_list() -> None:
    # scalar form
    card = _normalize_one({"title": "A", "assignee": "  ana  "})
    assert card["assignee"] == ["ana"]
    # list form: trimmed, empties out, duplicates dropped, order preserved
    card = _normalize_one({"title": "A", "assignee": ["bo", " ana ", "", "bo", 7]})
    assert card["assignee"] == ["bo", "ana"]
    # absent
    assert _normalize_one({"title": "A"})["assignee"] == []


def test_size_normalizes_to_uppercase_and_warns_off_scale() -> None:
    assert _normalize_one({"title": "A", "size": "m"})["size"] == "M"
    assert _normalize_one({"title": "A"})["size"] == ""
    with pytest.warns(UserWarning, match="size .* is not one of S, M, L, XL"):
        assert _normalize_one({"title": "A", "size": "enormous"})["size"] == ""
    # "" is the normalized unset value, so re-normalization (active_kanban
    # re-runs _normalize_card on already-normalized cards) must stay silent.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _normalize_one({"title": "A", "size": ""})["size"] == ""


def test_source_is_a_free_scalar_like_type() -> None:
    card = _normalize_one({"title": "A", "source": " folio#feat/x "})
    assert card["source"] == "folio#feat/x"
    with pytest.warns(UserWarning, match="source .* is not a scalar"):
        assert _normalize_one({"title": "A", "source": ["a"]})["source"] == ""


def test_routes_public_normalizes_string_paths(tmp_path: Path) -> None:
    """String paths get normalized with leading slash and stripped."""
    # Clean path stays as is
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/board"}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] == "/board"

    # "board" gets leading slash added
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "board"}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] == "/board"

    # Trailing slash stripped
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/board/"}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] == "/board"

    # Both trimmed
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "  board  "}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] == "/board"


def test_routes_public_empty_string_becomes_false(tmp_path: Path) -> None:
    """Empty or whitespace-only strings become False."""
    # Empty string
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": ""}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] is False

    # Whitespace only
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "   "}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] is False


def test_routes_public_bools_stay_intact(tmp_path: Path) -> None:
    """Boolean values are preserved."""
    # True stays True
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] is True

    # False stays False
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": False}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] is False


def test_routes_public_non_bool_non_string_coerced_to_bool(tmp_path: Path) -> None:
    """Non-bool, non-string types get bool() applied."""
    # Number (truthy)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": 1}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] is True

    # None (falsy)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": None}
    config = _configure(tmp_path, kanban)
    assert config.extra["kanban"]["routes"]["public"] is False


def test_routes_public_rejects_docs_base_collision(tmp_path: Path) -> None:
    """ValueError when public path equals or sits under docs route base."""
    # Exact collision with default /docs
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/docs"}
    with pytest.raises(ValueError, match="docs"):
        _configure(tmp_path, kanban)

    # Under docs route base
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/docs/board"}
    with pytest.raises(ValueError, match="docs"):
        _configure(tmp_path, kanban)


def test_routes_public_rejects_landing_root_collision(tmp_path: Path) -> None:
    """ValueError when public is "/" AND config has a landing section."""
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/"}
    # This should fail because landing exists
    config = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    with pytest.raises(ValueError, match="landing"):
        kanban_plugin.configure(
            config=config, raw_config={"kanban": kanban, "landing": {"enabled": True}}
        )


def test_routes_public_root_path_without_landing_succeeds(tmp_path: Path) -> None:
    """Public "/" is allowed when there's no landing section."""
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/"}
    config = _configure(tmp_path, kanban)
    # Simulate landing plugin having disabled landing_enabled (no landing: section)
    config.landing_enabled = False
    assert config.extra["kanban"]["routes"]["public"] == "/"


def test_public_view_registered_at_configured_path(tmp_path: Path) -> None:
    """The view is registered at the configured path; /kanban redirects when moved."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    # Root path: board at /, redirect at /kanban
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/"}
    config = _configure(tmp_path, kanban)
    # Simulate landing plugin having disabled landing_enabled (no landing: section)
    config.landing_enabled = False
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    assert "/" in registry.views
    assert registry.views["/"].slots["main"][0].component == "KanbanBoard"
    # Redirect view at /kanban preserves published links
    assert "/kanban" in registry.views
    assert registry.views["/kanban"].slots["main"][0].component == "RedirectPage"

    # Custom path: board at /board, redirect at /kanban
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/board"}
    config = _configure(tmp_path, kanban)
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    assert "/board" in registry.views
    assert registry.views["/board"].slots["main"][0].component == "KanbanBoard"
    # Redirect view at /kanban preserves published links
    assert "/kanban" in registry.views
    assert registry.views["/kanban"].slots["main"][0].component == "RedirectPage"

    # True still uses /kanban (no redirect needed)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    assert "/kanban" in registry.views
    assert registry.views["/kanban"].slots["main"][0].component == "KanbanBoard"


def test_roadmap_href_adapts_to_view_depth(tmp_path: Path) -> None:
    """roadmapHref is computed from view depth, not hardcoded."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    # Root (/) → "roadmap/" (depth 0)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/"}
    config = _configure(tmp_path, kanban)
    # Simulate landing plugin having disabled landing_enabled (no landing: section)
    config.landing_enabled = False
    config.extra["roadmap"] = {"routes": {"public": True}}
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    board_props = registry.views["/"].slots["main"][0].props
    assert board_props["roadmapHref"] == "roadmap/"

    # /kanban (True) → "../roadmap/" (depth 1)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    config.extra["roadmap"] = {"routes": {"public": True}}
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    board_props = registry.views["/kanban"].slots["main"][0].props
    assert board_props["roadmapHref"] == "../roadmap/"

    # /board → "../roadmap/" (depth 1)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/board"}
    config = _configure(tmp_path, kanban)
    config.extra["roadmap"] = {"routes": {"public": True}}
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    board_props = registry.views["/board"].slots["main"][0].props
    assert board_props["roadmapHref"] == "../roadmap/"

    # /team/board → "../../roadmap/" (depth 2)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/team/board"}
    config = _configure(tmp_path, kanban)
    config.extra["roadmap"] = {"routes": {"public": True}}
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)
    board_props = registry.views["/team/board"].slots["main"][0].props
    assert board_props["roadmapHref"] == "../../roadmap/"


def test_guards_hold_on_override_path_docs_collision(tmp_path: Path) -> None:
    """ValueError when project plugin overrides public to collide with docs route base."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    # Normal configure, then override extra to /docs (bypassing configure guards)
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    # Project plugin overrides after configure
    config.extra["kanban"]["routes"]["public"] = "/docs"
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    # Guard should catch this in register_extensions
    with pytest.raises(ValueError, match="docs"):
        kanban_plugin.register_extensions(registry=registry, config=config)

    # Also test /docs/board
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    config.extra["kanban"]["routes"]["public"] = "/docs/board"
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    with pytest.raises(ValueError, match="docs"):
        kanban_plugin.register_extensions(registry=registry, config=config)


def test_guards_hold_on_override_path_landing_collision(tmp_path: Path) -> None:
    """ValueError when project plugin overrides public to "/" with landing enabled."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    # Normal configure, then override extra to "/" with landing enabled
    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    # Simulate landing plugin having set landing_enabled
    config.landing_enabled = True
    # Project plugin overrides after configure
    config.extra["kanban"]["routes"]["public"] = "/"
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    # Guard should catch this in register_extensions
    with pytest.raises(ValueError, match="landing"):
        kanban_plugin.register_extensions(registry=registry, config=config)


def test_redirect_page_component_exists_and_preserves_query_and_hash() -> None:
    """The RedirectPage component exists and forwards query and hash intact.

    Published instructions (agents.md, board/SKILL.md) teach /kanban/?q= as the
    report link. When the board moves to a different path, the redirect at
    /kanban keeps those instructions true by preserving query and hash.
    """
    component = (
        Path(__file__).parents[1] / "folio_agents" / "assets" / "redirect-page.tsx"
    ).read_text()

    # Client component that redirects on mount
    assert '"use client"' in component
    assert "window.location.replace" in component
    # Query and hash are concatenated to the target
    assert "window.location.search" in component
    assert "window.location.hash" in component
    # Static fallback link works without JS
    assert "<a" in component and "href={to}" in component


def test_public_at_root_registers_redirect_view(tmp_path: Path) -> None:
    """When public: "/" the plugin registers both the board and a redirect view.

    The board renders at "/" and "/kanban" forwards to "../" so every published
    /kanban/?q= link keeps working.
    """
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/"}
    config = _configure(tmp_path, kanban)
    # Simulate landing plugin having disabled landing_enabled (no landing: section)
    config.landing_enabled = False
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)

    # Board view at root
    assert "/" in registry.views
    board_view = registry.views["/"]
    assert board_view.slots["main"][0].component == "KanbanBoard"

    # Redirect view at /kanban pointing to ../
    assert "/kanban" in registry.views
    redirect_view = registry.views["/kanban"]
    assert redirect_view.layout == "folio_docs.public"
    redirect_block = redirect_view.slots["main"][0]
    assert redirect_block.component == "RedirectPage"
    assert redirect_block.props["to"] == "../"

    # RedirectPage component is registered
    assert "RedirectPage" in registry.components


def test_public_at_custom_path_registers_redirect_view(tmp_path: Path) -> None:
    """When public: "/board" the redirect view points to "../board/"."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": "/board"}
    config = _configure(tmp_path, kanban)
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)

    # Board view at /board
    assert "/board" in registry.views

    # Redirect view at /kanban pointing to ../board/
    assert "/kanban" in registry.views
    redirect_view = registry.views["/kanban"]
    redirect_block = redirect_view.slots["main"][0]
    assert redirect_block.component == "RedirectPage"
    assert redirect_block.props["to"] == "../board/"


def test_public_true_gets_no_redirect_view(tmp_path: Path) -> None:
    """When public: true (path IS /kanban), no redirect view is registered."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions

    kanban = _cardfile_kanban(tmp_path)
    kanban["routes"] = {"public": True}
    config = _configure(tmp_path, kanban)
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    kanban_plugin.register_extensions(registry=registry, config=config)

    # Board view at /kanban exists
    assert "/kanban" in registry.views
    board_view = registry.views["/kanban"]
    assert board_view.slots["main"][0].component == "KanbanBoard"

    # Exactly one view - no redirect since the path IS /kanban
    assert len(registry.views) == 1


def test_watch_paths_names_the_board_directory(tmp_path: Path) -> None:
    """The serve watcher asks plugins what to watch; a cardfile board answers
    with its directory, and no board answers with nothing."""
    config = _configure(tmp_path, _cardfile_kanban(tmp_path))
    assert kanban_plugin.watch_paths(config) == [str(tmp_path / "board")]

    silent = Config(project_name="Demo", project_dir=str(tmp_path), extra={})
    assert kanban_plugin.watch_paths(silent) == []


def test_a_card_change_reloads_the_board_while_serving(tmp_path: Path) -> None:
    """The bug this pins: a card added while `folio serve` ran never reached
    the served board. The change handler reloads the board from disk into
    config.extra and re-emits, so the next data write carries the new card."""
    config = _configure(tmp_path, _cardfile_kanban(tmp_path))
    assert all(not column["cards"] for column in config.extra["kanban"]["columns"])

    new_card = tmp_path / "board" / "cards" / "hot-added.md"
    new_card.write_text("---\ntitle: Hot added\nstatus: backlog\n---\n")
    builder = _PageBuilder()
    applied = []
    builder.apply_extensions = applied.append
    handled = kanban_plugin.on_watched_change(builder, config, str(new_card), "added")
    assert handled is True
    titles = [
        card["title"]
        for column in config.extra["kanban"]["columns"]
        for card in column["cards"]
    ]
    assert titles == ["Hot added"]
    # The served board reads lib/kanban-data.ts, which the extension
    # emitter writes from the registry — refreshing extra alone was the
    # bug this test originally missed. The re-applied registry must carry
    # the new card in its data module.
    assert len(applied) == 1
    module = applied[0].data_modules["kanban"]
    assert any(
        card["title"] == "Hot added"
        for column in module.data
        for card in column["cards"]
    )

    outside = tmp_path / "notes.md"
    outside.write_text("x")
    assert (
        kanban_plugin.on_watched_change(builder, config, str(outside), "added") is False
    )


def test_icons_survive_renormalization_and_reach_the_contract() -> None:
    """active_kanban re-normalizes plugin-overridden boards; the icon map
    rides along and re-stamps the cards, and the TS contract carries the
    field the component renders."""
    from folio_agents.integrations.kanban import KANBAN_TYPES, active_kanban

    config = Config(project_name="Demo", project_dir=".", extra={})
    config.extra["kanban"] = {
        "routes": {"docs": True, "public": False},
        "title": "B",
        "columns": [
            {
                "id": "backlog",
                "title": "Backlog",
                "limit": None,
                "cards": [{"title": "A", "tags": ["casa"], "link": ""}],
            }
        ],
        "description": "",
        "cardDir": "",
        "icons": {"casa": "🏠"},
    }
    kanban = active_kanban(config)
    assert kanban["columns"][0]["cards"][0]["icon"] == "🏠"
    assert kanban["columns"][0]["cards"][0]["iconTag"] == "casa"
    assert "  icon: string\n" in KANBAN_TYPES
    assert "  iconTag: string\n" in KANBAN_TYPES
