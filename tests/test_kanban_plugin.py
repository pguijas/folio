from __future__ import annotations

import warnings

from pathlib import Path

import pytest

from folio.config import Config
from folio.plugins import kanban as kanban_plugin


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
        kanban_plugin._resolve_roadmap_phases(kanban, raw_roadmap=roadmap)
    # Exactly one warning for the two 0.9 cards, none for the claimed 0.3.
    assert len(caught) == 1


def test_an_unclaimed_card_without_an_id_is_named_by_its_title() -> None:
    kanban = _board_with_cards([{"title": "Ship it", "milestone": "0.9"}])
    roadmap = {"phases": [{"id": "p3", "title": "Three", "version": "0.3"}]}
    with pytest.warns(UserWarning, match=r"\(cards: Ship it; known: 0\.3\)"):
        kanban_plugin._resolve_roadmap_phases(kanban, raw_roadmap=roadmap)


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
            kanban_plugin._resolve_roadmap_phases(kanban, raw_roadmap=raw_roadmap)
    # A claimed milestone is silent too — and so is a card with no milestone
    # key sitting next to a roadmap that could have claimed one.
    kanban = _board_with_cards(
        [{"title": "A", "id": "a", "milestone": "0.3"}, {"title": "B", "id": "b"}]
    )
    roadmap = {"phases": [{"id": "p3", "title": "Three", "version": "v0.3"}]}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        kanban_plugin._resolve_roadmap_phases(kanban, raw_roadmap=roadmap)
    assert kanban["columns"][0]["cards"][0]["phase"] == "p3"  # v-prefix matches


def test_retired_inline_columns_are_a_loud_error(tmp_path):
    """A `columns:` key stops the build with the cardfile pointer instead of
    rendering a board nobody can operate."""
    with pytest.raises(ValueError, match=r"inline `columns:` boards were removed"):
        kanban_plugin.normalize_kanban({"columns": []}, project_dir=tmp_path)


def test_retired_single_file_source_is_a_loud_error(tmp_path):
    """A `source:` that resolves to a file names the resolved path and points
    at the cardfile migration."""
    (tmp_path / "board.yaml").write_text("columns: []\n")
    with pytest.raises(ValueError, match=r"single-file boards were removed"):
        kanban_plugin.normalize_kanban({"source": "board.yaml"}, project_dir=tmp_path)


def test_kanban_section_without_source_is_a_loud_error(tmp_path):
    """A kanban section without `source:` used to render an empty board
    silently; now it says what is missing."""
    with pytest.raises(ValueError, match=r"needs `source:` pointing at a board directory"):
        kanban_plugin.normalize_kanban({"routes": {"public": True}}, project_dir=tmp_path)


def test_bare_kanban_section_is_a_loud_error(tmp_path):
    """`kanban:` with no mapping under it is one typo away from a retired
    format; it gets the same missing-source error, not a silent empty board."""
    with pytest.raises(ValueError, match=r"needs `source:` pointing at a board directory"):
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
    from folio.generator.site_builder import SiteBuilder

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


def test_kanban_component_supports_compact_miniatures() -> None:
    """Compact embeds (landing miniatures) hide the export/reset toolbar and
    excerpt each column, while hydration stays SSG-clean (the toolbar gate is
    render-only; the interactive effect still runs)."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # Toolbar controls only render for interactive boards (miniatures pass
    # interactive=false), and filtering suspends drag/toolbar interactivity.
    # The gate carries the compact guard itself now that the staging card is
    # one JSX value with two render slots (workspace vs in-flow).
    assert "!compact && interactive && dirty ? (" in component
    # Excerpting: slice each column, then a muted "+N more" line.
    # Matched on the parts, not the one-line form: the extra @container
    # wrapper pushed this expression a level deeper and prettier reflowed it
    # across four lines.
    assert "column.cards.slice(" in component
    assert "Math.max(maxCardsPerColumn, 0)" in component
    assert "+{column.cards.length - maxCardsPerColumn} more" in component
    # Compact grid tops out at three columns; only the full board goes wider.
    # The full board keeps viewport breakpoints — it owns its page, so
    # container and viewport agree. The compact one is embedded at widths
    # nobody can predict, so it lays out against its container instead:
    # viewport breakpoints made a 600px embed on a 1440px screen still ask
    # for three tracks, wrapping a four-column board onto two rows.
    assert component.count("lg:grid-cols-3 xl:grid-cols-4") == 1
    assert "@lg:grid-cols-2 @2xl:grid-cols-3 @3xl:grid-cols-4" in component
    # The canvas wrapper is a container query root only for compact embeds
    # (the workspace branch shares the same element; `|| undefined` keeps
    # the docs embed's attribute-less markup byte-identical).
    assert 'compact && "@container",' in component


def test_kanban_component_is_one_board_with_filters_and_card_dialog() -> None:
    """The public board is a single instance: filters narrow it in place
    (milestone, tag, and text, all URL-addressable) and a board card carries
    its title only — the complete card opens as a dialog on click."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # Fields are declared once, in one table, and that table is the
    # language: the parser, the syntax reference and the URL all read it.
    assert "const FILTER_FIELDS: FilterField[] = [" in component
    assert 'key: "milestone"' in component
    assert 'key: "tag"' in component
    assert "params.getAll(name)" in component
    assert 'params.get("q")' in component
    assert "window.history.replaceState" in component
    # Cards open the complete view as an accessible modal dialog, and focus
    # is trapped so Tab cannot reach the filter field behind it (typing
    # there would change which cards exist while the dialog is open).
    assert 'aria-haspopup="dialog"' in component
    assert 'role="dialog"' in component
    assert 'aria-modal="true"' in component
    assert '"Escape"' in component
    assert '"Tab"' in component


def test_kanban_component_addresses_cards_by_id_not_position() -> None:
    """Cards carry a stable uid, so a filtered board stays operable.

    Position is a property of the filtered render: an index-addressed move
    moves whichever card sits at that index, which is why filtering used to
    switch drag off. Every mutation now takes a uid, and the dialog resolves
    its card the same way.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "type IdentifiedCard = KanbanCard & { uid: string }" in component
    assert "function identify(columns: KanbanColumn[]): BoardColumn[]" in component
    assert "(uid: string, targetColumn: number) => {" in component
    assert "card.uid" in component
    # The filter gate on interactivity is gone: filtered views are operable.
    assert "interactive={interactive}" in component
    assert "Filtered view, drag is off" not in component
    # Drop feedback names the slot the card will land in.
    assert "border-dashed border-primary/50" in component
    # Moves are announced. Undo is gone with its button: revert and export
    # are the only two things you can do about a staged move, and the third
    # control was a weaker version of revert that kept twenty copies of the
    # board alive to serve it.
    assert 'role="status"' in component
    assert 'aria-live="polite"' in component
    assert "Undo move" not in component
    assert "historyRef" not in component
    # A move announces the card, where it landed and how full that column
    # now is — not a fixed string.
    assert 'Moved "${card.title}" to ${next[targetColumn].title}.' in component
    # Theme packages restyle the board through data attributes rather than
    # by forking the component.
    assert 'data-slot="kanban-card"' in component
    assert 'data-slot="kanban-column"' in component
    assert 'data-slot="kanban-filters"' in component


def test_kanban_filter_field_and_shortcuts_survive_review() -> None:
    """Defects an adversarial review confirmed, each pinned by a line.

    A typed facet token must not commit on the first character after the
    colon (`milestone:0.3` became a `milestone:0` chip), the drag payload
    must stay empty (a card released over the filter field typed its own
    id into the query), the filter field needs a visible focus indicator,
    the live region must re-announce identical messages, and the "/"
    shortcut must not swallow the key for the whole page.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The token-commit machinery is gone with the dual store: there is no
    # moment a term "commits", because the expression is the state. The
    # defect it existed to fix — `milestone:0.3` becoming `milestone:0` on
    # the first digit — cannot happen when nothing is ever extracted from
    # the input. A field with no value is simply dropped until it has one.
    assert "commitTrailingToken" not in component
    assert "if (!rawValue) {" in component
    # An inert drag payload: the filter input is a live text drop target.
    assert 'event.dataTransfer.setData("text/plain", "")' in component
    # The borderless input shows focus through its wrapper.
    assert "focus-within:outline-2 focus-within:outline-offset-2" in component
    # Two identical announcements in a row must both be spoken.
    assert "key={announcement.seq}" in component
    # The shortcut is bound only while the board holds focus.
    assert "sectionRef.current?.contains(active)" in component
    # No card control is pinned by pointer type any more. The move buttons
    # follow hover and focus, they answer no pointer while they are hidden
    # (an opacity-0 button still takes a tap, which turned a card's corner
    # into a silent move on a phone), and the milestone label steps aside
    # on exactly the condition that paints them over it — rather than on a
    # second condition that could drift out of step, which is how a
    # keyboard user ended up with buttons painted over a visible label.
    # A trail ref renders as the identifier it is, in mono. It used to
    # resolve to {repo}/commit/<sha>; the board builds no hosting-provider
    # URLs, and a sha is already an address that `git show` takes.
    assert "{entry.ref ? (" in component
    assert "entry.href" not in component
    assert "font-mono text-muted-foreground" in component

    assert "[@media(pointer:coarse)]" not in component
    # The card has no move affordance in its corner any more. A column is a
    # card's status, and status is set in the dialog as a field, not stepped
    # through one column at a time from a hover-gated chevron — which also
    # unmounted itself on every press, since the moved card reparents into
    # another column and takes the focused button with it.
    assert "function MoveButtons(" not in component
    assert "pointer-events-none absolute -top-px -right-px" not in component
    assert "peer-focus-within/move" not in component
    assert "function CardKey(" in component


def test_the_export_has_one_meaning():
    """Cardfile is the only board format, so the export is always the list
    of move commands; the YAML writer is gone."""
    tsx = (Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx").read_text()
    assert "boardToYaml" not in tsx
    assert "Export YAML" not in tsx
    assert "Export moves" in tsx


def test_kanban_registers_component_with_compact_props(tmp_path: Path) -> None:
    from folio.extensions import ExtensionRegistry

    config = _configure(tmp_path, _cardfile_kanban(tmp_path))
    registry = ExtensionRegistry()
    kanban_plugin.register_extensions(registry=registry, config=config)

    props = registry.components["KanbanBoard"].props
    assert props["compact"] == "boolean | undefined"
    assert props["maxCardsPerColumn"] == "number | undefined"


def test_board_shows_its_sync_status() -> None:
    """A board that mirrors the repo and one holding unsaved edits must differ.

    This board cannot save: moves stage in localStorage and leave as CLI
    commands. So "in sync" versus "3 moves staged here" is the single most
    important thing the surface has to say, and it says the count because
    "some moves are pending" is the state people lose track of.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert 'data-slot="kanban-staging"' in component
    # Nothing is said when nothing is staged. "In sync" was a permanent
    # label for the default state — jargon that announced "you have not done
    # anything yet" in the corner of every board on every load.
    assert "In sync" not in component
    assert 'data-slot="kanban-sync"' not in component
    assert "moves staged in this browser" in component
    # The actions act directly; there is no menu between you and them.
    assert "onClick={reset}" in component
    assert "onClick={exportBoard}" in component
    # The count is real state, tracked wherever the overlay changes: restored
    # from storage, after a move, and cleared on reset.
    assert component.count("setStagedCount(") == 3
    # It is a card, built like the cards under it: eyebrow, then the line
    # that matters, then one line of detail. It used to be loose prose
    # between the navbar and the toolbar, with nothing to belong to.
    assert "rounded-lg border border-border bg-card px-5 py-4" in component
    assert "moves staged in this browser" in component
    # The mode is named, and so is the way out of it. The first draft spent
    # forty words explaining static hosting to someone who had just dragged
    # a card and wanted to know what happened to it.
    assert "Local only" in component
    assert "Nothing you change here is applied" in component
    assert "then apply it in a clone" in component
    # And it sits above the toolbar. A notice about the whole surface
    # belongs at the top of it; between the toolbar and the columns it read
    # as a divider between two working parts.
    staging = component.index('data-slot="kanban-staging"')
    toolbar = component.index('data-slot="kanban-filters"')
    assert staging < toolbar


def test_card_column_is_a_field_you_set() -> None:
    """A card's column is its status, so the dialog sets it as a field.

    The board used to offer only "previous column" / "next column" — two
    chevrons in the card's corner and two buttons in the dialog footer. That
    is a direction, and a move is a destination: sending a card from backlog
    to released meant clicking "next" three times and watching it stop in
    two columns it was never in.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function StatusField(" in component
    assert "<StatusField" in component
    assert "Previous column" not in component
    assert "Next column" not in component

    # The board's last native menu joined the combobox family: the drawn
    # 40px value is a real button, the panel is a listbox whose rows carry
    # the column counts (over-limit in warning ink), and no select remains
    # in the field. The composer's Created comparison keeps the one
    # surviving <select>.
    field_start = component.index("function StatusField(")
    field_end = component.index("function CardDetail(", field_start)
    field = component[field_start:field_end]
    assert "<select" not in field
    assert 'role="combobox"' in field
    assert 'role="listbox"' in field
    assert "aria-activedescendant" in field
    assert "${column.cards.length}/${column.limit}" in field
    assert "<select" in component  # the Created comparison, composer-side
    # Escape belongs to the open panel before it belongs to the dialog:
    # the same three-belt cage the composer combobox wears, and the
    # dialog's document listener early-returns on the flag preventDefault
    # sets — stopPropagation alone never suppressed a same-target listener.
    # The full trio, in order: preventDefault ARMS the flag the document
    # listeners early-return on — pinning the other two belts without it
    # let the load-bearing line vanish unnoticed.
    assert (
        "event.preventDefault()\n"
        "      event.stopPropagation()\n"
        "      event.nativeEvent.stopImmediatePropagation()"
    ) in field
    assert component.count("if (event.defaultPrevented) {") >= 2
    # The cage only sees keys aimed inside its root, and a mouse open never
    # moves focus by itself (mousedown is prevented for Safari's sake) —
    # both dropdown families focus their trigger by hand on open, or the
    # first Escape lands on the dialog's close button and kills everything.
    # Two per family: openPanel and close(refocus).
    assert component.count("triggerRef.current?.focus()") >= 4
    assert field.count("triggerRef.current?.focus()") >= 2


def test_card_dialog_prints_the_command_it_will_export() -> None:
    """The board's claim is that the browser never writes a card file.

    The footer used to assert "Moves export as folio kanban commands." Now a
    staged card prints the exact line `Export moves` will write for it, from
    the same baseline and the same column id, so the two cannot drift.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "moveCommand" in component
    assert (
        "`folio kanban move ${selectedCard.id} ${board[selectedColumn].id}`"
        in component
    )
    assert "committedColumns(baseline).get(selectedCard.uid) !==" in component
    # The footer exists only when there is a consequence to print: an
    # unstaged card gets no placeholder strip. It has one condition because
    # there is one thing to print — the pen that used to force a second
    # condition is gone, and with it the edit link out to a repo host.
    assert "{canMove && moveCommand ? (" in component
    assert "Moves export as folio kanban commands." not in component
    assert "card.editHref" not in component


def test_the_card_dialog_attaches_artifacts_like_a_mail() -> None:
    """Artifacts are the card's output, so they close the card the way
    attachments close a mail: a full-width band at the dialog's foot, one
    kind-tinted tile per artifact, and the CLI gesture taught in place of
    a write the browser will never do. The rail chips are gone.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The tile replaces the chip, and the kind reads as a tinted mark plus
    # assistive text rather than a tooltip.
    assert "function ArtifactTile(" in component
    assert "ArtifactChip" not in component
    assert "const ARTIFACT_KIND_TINT" in component
    assert "const ARTIFACT_GLYPH_D" in component
    assert "{`${artifact.kind}: `}" in component
    # The mono line prints the target as the author wrote it — the bare
    # sibling name on a derived entry, a fuller path only where one was
    # written. Data built before `display` existed keeps the resolved
    # target, which is why the local interface marks the field optional.
    assert "  display?: string" in component
    assert ": artifact.display || artifact.target" in component

    # The band teaches the attach gesture. `canMove` is broader — any
    # hydrated board can stage a drag.
    assert "folio kanban attach ${card.id} --doc <path>" in component
    assert "{canAttach && card.id ? (" in component
    assert "{artifacts.length > 0 || (canAttach && card.id) ? (" in component
    assert "canAttach={interactive}" in component
    # The band caps its own height: it sits outside the body's scroll, and
    # under the dialog's overflow-hidden an uncapped band clips silently.
    assert "max-h-44 shrink-0 overflow-y-auto" in component

    # A tile with an href opens it, and a card-local href is site-absolute
    # (`/_folio/kanban/<id>/…`) because the same data feeds the standalone
    # board and any docs page embedding it. A project site can sit under a
    # base path, so the prefix is applied here rather than baked into the
    # data — and a `url:` artifact, authored as a URL, is passed through.
    assert "function artifactHref(" in component
    assert "href={artifactHref(artifact.href)}" in component
    assert (
        'if (!href.startsWith("/") || href.startsWith("//")) return href' in component
    )
    assert "process.env.NEXT_PUBLIC_FOLIO_BASE_PATH" in component
    # Backend links never include the deploy prefix. Even when the prefix is
    # `/docs` and the configured docs route also begins `/docs`, it must be
    # added instead of mistaken for an already-prefixed href.
    assert "href === FOLIO_BASE_PATH" not in component
    assert "href.startsWith(`${FOLIO_BASE_PATH}/`)" not in component
    assert "return `${FOLIO_BASE_PATH}${href}`" in component
    assert "\0" not in component


def test_the_dialog_renders_the_cards_markdown() -> None:
    """Cards are markdown files, and the dialog prints their prose rendered:
    inline code, bold, and http(s) links; blank lines split description
    paragraphs. Tokens become React nodes — a card's prose never passes
    through innerHTML, by construction (the drawer injects only the site's
    own compiled pages), and the executed grammar test in
    test_kanban_filter_language.py pins what tokenizes and what stays
    literal.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function parseInlineMd(" in component
    assert "function MdInline(" in component
    assert "dangerouslySetInnerHTML" not in component
    # The three places a card talks: description paragraphs, criteria, trail.
    # Only the description carries the card context `./` links resolve
    # against; a criterion or trail note keeps the literal text.
    assert "parseMdBlocks(card.description)" in component
    assert "<MdInline text={block.text} links={bodyLinks} />" in component
    assert "<MdInline text={item} links={bodyLinks} />" in component
    assert "<MdInline text={criterion.text} />" in component
    assert "<MdInline text={entry.note} />" in component
    # The scheme guard is the grammar itself: only http(s) and the
    # card-relative `./` form ever tokenize as a link, so there is no
    # sanitizer to forget. What `./` may become is pinned by execution in
    # test_kanban_filter_language.py.
    assert "((?:https?:\\/\\/|\\.\\/)[^)\\s]+)" in component
    assert "function resolveCardLink(" in component
    # Raw stays raw outside the dialog: the filter's text haystack reads
    # the description as authored, asterisks and all.
    assert '`${card.title} ${card.description} ${card.id ?? ""}`' in component


def test_filter_is_one_expression() -> None:
    """The filter is a language, and the input's value is the whole state.

    The old filter kept two stores: a `Filters` record of committed facets
    and a free-text query, with dropdowns writing the first and the input
    writing the second. Two stores of one thing is two answers to "what is
    filtered", and they could disagree — a menu click could produce
    `-tag:spec tag:spec`, or render a value unchecked while it excluded.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function parseQuery(" in component
    assert "function matchesQuery(" in component
    assert "const FILTER_FIELDS" in component
    # The old dual store and everything that reconciled it.
    assert "const FACETS" not in component
    assert "matchesFilters" not in component
    assert "function FacetMenu(" not in component
    assert "function FiltersMenu(" not in component
    assert "function FilterToken(" not in component
    assert "commitTrailingToken" not in component


def test_filter_vocabulary_is_the_card_frontmatter() -> None:
    """Nothing invented: every field name is a key a card already carries.

    That is what keeps the language teachable in three lines, to a person or
    to an agent, and what stops the board, the URL and the CLI drifting into
    three vocabularies for one thing. `status` is the exception that proves
    it — the column is not on the card at render time, but the cardfile does
    carry `status:` and `folio kanban move <id> in-review` spells it exactly
    that way.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    for field in (
        "status",
        "milestone",
        "tag",
        "priority",
        "assignee",
        "id",
        "parent",
        "blocked_by",
        "created",
        "artifact",
    ):
        assert f'key: "{field}"' in component


def test_filter_parser_has_no_failure_mode() -> None:
    """Every keystroke re-parses, so no keystroke may empty the board.

    Each of these is a real defect found by attacking the grammar before it
    shipped, and each is pinned here because the failure is silent: the board
    answers a question nobody asked instead of throwing.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # A quote binds whitespace only when it has a partner. Otherwise
    # `tag:"spec milestone:0.7` — every quoted value, while it is typed —
    # swallows the terms after it into one nonsense value.
    assert "input.indexOf('\"', index + 1) === -1" in component
    # `-` excludes only in front of a real field. A bare `-word` is text:
    # this board's ids are full of hyphens, and `-technical-plan` inverting
    # the search would also change what every shared ?q= link means.
    assert "FIELD_BY_NAME.has(rest.slice(0, colon).toLowerCase())" in component
    # An ordered comparison against a half-typed date compares as a string
    # and answers about the wrong days, silently.
    assert "FULL_ISO_DATE.test(text)" in component
    # A field with no value yet is a keystroke, not a query.
    assert "if (!rawValue) {" in component
    # A full-width colon is indistinguishable on screen.
    assert 'replace(/：/g, ":")' in component


def test_filter_url_keeps_roadmap_deep_links_and_everything_else() -> None:
    """?milestone=0.3 must keep working: the roadmap links into the board.

    Only the four parameters that ever shipped are folded in. Reading every
    field name as a parameter would let an unrelated `?id=42` from a
    newsletter silently filter the board to nothing.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert (
        'const LEGACY_PARAMS = ["milestone", "tag", "priority", "assignee"]'
        in component
    )
    # The next URL is built from the current one, so a link carrying a
    # fragment or someone else's parameters keeps them.
    assert "const url = new URL(window.location.href)" in component
    assert "${url.pathname}${url.search}${url.hash}" in component


def test_ordered_comparison_guards_both_sides_of_the_date() -> None:
    """`created:<2026-12-31` must not answer about a card dated `2026-8-1`.

    `readAlternative` already refuses a half-typed date on the query side. The
    card side is validated nowhere — folio carries `created:` through as
    written — so without a guard here the comparison is a string comparison
    wearing a date's clothes: "2026-8-1" sorts after "2026-08-01" and before
    nothing, and the card is silently dropped from a range it belongs to.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The query side: no comparison until the typed date is complete.
    assert "if (op && !FULL_ISO_DATE.test(text)) {" in component
    # The card side: the same test, before any operator is applied.
    assert "if (!FULL_ISO_DATE.test(candidate)) {" in component


def test_comma_splitting_is_quote_aware() -> None:
    """`tag:"core",spec` and `tag:spec,"core"` must select the same cards.

    The value was split on commas only when it did not open with a quote —
    a shortcut meant to keep `tag:"a,b"` intact. It also meant a leading
    quote disabled the comma for the whole value, so `tag:"core",spec` asked
    for a tag literally called `core","spec` and answered an empty board.
    Two documented rules that compose in one order and not the other are not
    a rule; both orders go through the same quote-aware scan now.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function splitAlternatives(raw: string): string[] {" in component
    assert "splitAlternatives(rawValue)" in component
    # The shortcut that caused it is gone.
    assert "rawValue.startsWith('\"') ? [rawValue]" not in component


def test_the_syntax_reference_is_in_the_dom_before_it_is_opened() -> None:
    """The filter's description must exist on a freshly loaded page.

    `aria-describedby` pointed at an id rendered only inside the dropdown
    panel, which does not exist until the panel is opened — so a reader who
    tabbed into the filter was described nothing, and the only written copy
    of the language sat behind a button they had no reason to press.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # One source of rules, two renderings: always-on for the description,
    # visible inside the panel.
    assert (
        "const SYNTAX_RULES: { example: string; mark: string; meaning: string }[] = ["
        in component
    )
    assert "function SyntaxRules({ id }: { id: string }) {" in component
    assert "<SyntaxRules id={`${instanceId}-syntax`} />" in component


def test_no_panel_can_exceed_the_viewport() -> None:
    """The composer rail positions itself relative to the viewport and navbar.

    On narrow screens it is a fixed drawer pinned to the viewport edge. On
    wide screens, in the docs embed, the rail is split in two: an outer
    shell that stretches to the board column's full height (so its surface
    runs to the board's foot — no self-start, no overflow, which would also
    break sticky), and an inner block that follows the scroll — sticky
    below the docs navbar (using the nextra CSS variable), bounded to the
    viewport, scrolling its own overflow. The standalone page skips the
    machinery entirely (`test_the_public_board_is_an_app_workspace`).
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The shell is a full-height surface (drawer below lg); the inner block
    # carries the padding, the navbar-aware sticky top, the viewport bound
    # and the internal scroll on the docs-embed path.
    assert "max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-40" in component
    assert (
        "lg:sticky lg:top-[calc(var(--nextra-navbar-height,0px)+1rem)] lg:max-h-[calc(100vh-var(--nextra-navbar-height,0px)-2rem)] lg:overflow-y-auto"
        in component
    )
    assert "lg:self-start" not in component
    assert "function Dropdown(" not in component
    assert "function MenuAction(" not in component


def test_the_public_view_declares_the_navbar_height_the_rail_computes_with() -> None:
    """The rail's viewport math consumes `--nextra-navbar-height` — the
    public view must define it.

    Inside the docs shell nextra sets the variable, so the rail's sticky
    top and max-height calc against the real navbar. The public board page
    renders through PublicLayout instead, whose own navbar is `fixed top-0`
    and 4rem tall, compensated by `pt-16` on the view container — but the
    variable was never declared there, so the rail fell back to 0px: on
    scroll its controls pinned 16px from the viewport top and slid under
    the 64px navbar, and its max-height ran 64px too tall (the owner's
    "some overflow"). The layout now states the same fact twice in the same
    place: `pt-16` for its own spacing, the variable for every consumer.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "folio-view-layouts.tsx"
    ).read_text()

    # The declaration sits on the container whose `pt-16` encodes the same
    # 4rem navbar — one element, one fact, two spellings kept in step.
    assert 'style={{ "--nextra-navbar-height": "4rem" } as CSSProperties}' in component
    assert 'className="min-h-screen bg-background pt-16 text-foreground"' in component


def test_the_field_has_one_mark_and_it_is_the_control() -> None:
    """The field carried two identical filter icons, one of them inert.

    A decorative mark at the head and the composer's trigger at the tail.
    The head is the control now. The `?` went with them: the composer
    teaches the language by writing it into the field, so a second surface
    listing the same five rules was a third place to keep them in step.

    The rules survive as the field's description, because a reader typing by
    hand still needs them and an sr-only span costs nothing.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert component.count("<FilterGlyph") == 1
    assert 'aria-label="Filter by field"' in component
    # The sheet and its trigger are gone; the description is not.
    assert "SyntaxSheet" not in component
    assert 'aria-label="Filter syntax"' not in component
    assert "function SyntaxRules({ id }: { id: string }) {" in component
    assert "<SyntaxRules id={`${instanceId}-syntax`} />" in component


def test_the_card_dialog_names_its_column_once() -> None:
    """The header printed the column and the rail carried the control.

    Two answers to "what column is this in", two inches apart, and the one
    you could act on looked exactly like the five facts you cannot. The
    header's reading is the control now, and the rail is facts only.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    header_start = component.index('<div className="flex shrink-0 items-start')
    header_end = component.index("The card body scrolls", header_start)
    header = component[header_start:header_end]
    # The header identifies the card and nothing else — the title presides,
    # with the close beside Esc. It does not change the card, and it does
    # not name the file: the path is the Card field in the rail.
    assert "<StatusField" not in header
    assert "{columnTitle}" not in header
    assert "id={titleId}" in header
    assert "{card.title}" in header
    assert "board/cards/${card.id}.md" not in header
    # No pen. It opened the repository host's web editor, which is not
    # where anyone edits and is the wrong place for a board hosted
    # elsewhere. A control that cannot do what it draws is worse than none.
    assert "PenGlyph" not in component
    assert 'aria-label="Edit this card"' not in component
    # The Card field carries the resolved path, as text. No anchor: the
    # board builds no link to a repository host, so a mutation that adds
    # one back must fail here.
    assert "{card.file || `board/cards/${card.id}.md`}" in component
    assert "card.fileHref" not in component
    assert "card.editHref" not in component

    # The dialog's rail, not the artifact drawer: the drawer is an aside of
    # its own and sits earlier in the file.
    aside_start = component.index("<aside", component.index("function CardDetail("))
    aside_end = component.index("</aside>", aside_start)
    aside = component[aside_start:aside_end]
    # One box against five bare rows: the control is the only thing in the
    # rail with a surface, a border and a 40px height, and its label says
    # what pressing it does rather than naming a field.
    assert "<StatusField" in aside
    assert "Move to" in component
    assert "h-10 w-full cursor-pointer items-center justify-between" in component

    # The drawn value is the control itself now — a combobox trigger, no
    # transparent select stretched over it. The 40px surface and the
    # chevron-against-the-word reading survive the select's death.
    assert 'className="absolute inset-0 h-full w-full cursor-pointer' not in component


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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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


def test_the_public_board_is_an_app_workspace() -> None:
    """In workspace mode the board is a viewport-height app surface.

    Under the fixed navbar the section takes exactly the viewport
    (`100dvh` minus the navbar variable) at lg+, the composer rail becomes
    a plain full-height flex panel with its own scroll and a right border
    (no rounding, no sticky machinery), and the canvas — the one child
    left to grow — scrolls the columns on both axes, with a per-column
    min-width so a narrow canvas x-scrolls instead of crushing columns.
    The docs embed keeps the in-flow grid and the stretched-shell/sticky
    rail, pinned by `test_no_panel_can_exceed_the_viewport`.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The seam: an optional prop, off by default, so docs embeds and
    # miniatures render exactly as before.
    assert "workspace = false," in component
    # The section is the workspace: exactly the viewport below the navbar.
    assert "lg:h-[calc(100dvh-var(--nextra-navbar-height,0px))]" in component
    # The rail is a full-height panel in the flex row — its own scroll, a
    # right border, no rounded corners, never sticky.
    assert (
        "lg:w-[17rem] lg:shrink-0 lg:overflow-y-auto lg:rounded-none lg:border-y-0 lg:border-l-0"
        in component
    )
    # The canvas is the flex child that grows and scrolls both axes.
    assert "lg:min-h-0 lg:flex-1 lg:overflow-auto" in component
    # Each track declares its own 13rem floor (minmax in the tracks
    # variable), so the canvas x-scrolls rather than crushing the columns;
    # the grid-level floor survives only as the lg baseline.
    assert "lg:min-w-[48rem]" in component
    # The rail's right border is the divider — no flex gap beside it —
    # and the board column carries its own 24px of air on both sides, so
    # the canvas sits symmetric: 24px off the rail's border, 24px off the
    # viewport's right edge.
    assert "lg:flex lg:h-full lg:min-h-0 lg:gap-0" in component
    assert '"lg:flex lg:min-h-0 lg:flex-1 lg:flex-col lg:px-6 lg:pt-5"' in component

    layout = (
        Path(__file__).parents[1] / "template" / "components" / "folio-view-layouts.tsx"
    ).read_text()
    # The frame goes full-bleed at lg+ for a workspace view: vertical
    # padding kept, the viewport-height section scrolls the page by
    # exactly that padding; the measure or side padding kept, the rail's
    # flush-left squared edge floats 24px into whitespace instead of
    # touching the viewport.
    assert 'workspace && "lg:max-w-none lg:px-0 lg:pt-0 lg:pb-0"' in layout


def test_staged_state_has_one_name() -> None:
    """`dirty` was a second useState set beside every setStagedCount.

    Two names for one fact, plus a standing obligation to keep them in step.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "const dirty = stagedCount > 0" in component
    assert "setDirty" not in component


def test_the_toolbar_is_the_field_and_the_count_is_gone() -> None:
    """The row is the filter field. The card count that shared it is gone.

    It sat above four column headers already printing 22, 0/3, 4/3 and 0,
    and when a filter narrowed the board those four narrowed with it — a
    total answering a question the page had already answered four times.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The field takes the row.
    assert "min-h-8 min-w-0 flex-1 flex-wrap items-center" in component

    # The count, and the three values that existed only to feed it.
    assert "totalCount" not in component
    assert "visibleCount" not in component
    assert "clearFilters" not in component

    # Clearing works at every width now. The old "Clear" button was `hidden`
    # below `sm`, so a phone could not unfilter a filtered board.
    assert 'aria-label="Clear the filter"' in component


def test_the_filter_opens_with_a_filter_mark_not_a_magnifying_glass() -> None:
    """Search promises "type a word, get matches". This is a language."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function FilterGlyph(" in component
    # The magnifying glass the field used to open with is gone.
    assert '<circle cx="7" cy="7" r="4.5" />' not in component


def test_an_empty_filter_says_which_term_emptied_it() -> None:
    """Three different mistakes used to produce the same four lines.

    A field name typed wrong (`tagg:spec`, which falls back to a text search
    and finds nothing), a real field with a value no card has
    (`priority:nope`), and an ordinary text miss all rendered "No cards match
    the filters." once per column and named none of them — so the only way
    forward was to delete characters until cards came back.

    Each term is re-run alone; the ones that match nothing by themselves are
    the ones that emptied the board, and they are named in the spelling they
    were typed.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function FilterDiagnosis({" in component
    assert "countMatches(board, [term]) === 0" in component
    assert "function termSource(term: QueryTerm) {" in component
    assert "Nothing matches this filter." in component
    # A near-miss field is the one mistake the language cannot warn about
    # while typing, because `owner:pedro` is a legitimate text search.
    assert "unknownField?: string" in component
    assert "is not\n                  a field, so it was searched as text" in component
    # When every term matches on its own, saying "some combination of these"
    # would help no one, so it says exactly that instead of listing them.
    assert (
        "Each term matches something on its own; together they match nothing."
        in component
    )
    # Said once, above the grid — not once per column.
    assert ") : nothingMatches ? null : (" in component


def test_the_composer_is_a_rail_beside_the_board() -> None:
    """The composer is a fixed-width rail positioned beside the board.

    On narrow screens it is a full-height drawer; on wide screens it is a
    static shell in a two-column grid, stretched to the board column's full
    height, with a sticky scroller inside that follows the reader. No
    runtime measurement needed: the rail's width is declared in both the
    drawer and grid classes, so it stays inside by construction.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The composer is now a full-height rail with a fixed width.
    assert "max-lg:w-[17rem] max-lg:max-w-[85vw]" in component
    assert "lg:grid lg:grid-cols-[17rem_minmax(0,1fr)]" in component
    # The dropdown primitive and its panel-nudging went with the sheet.
    assert "function Dropdown(" not in component
    assert "function MenuAction(" not in component
    assert "panel.getBoundingClientRect()" not in component

    # Each rule still marks the character it is about, in the description.
    assert "const SYNTAX_RULES" in component
    assert 'mark: ","' in component


def test_the_card_dialog_shows_state_as_state() -> None:
    """The rail read as one grey column, whatever the entry meant.

    Priority is a judgement, "blocked by" means the card cannot proceed, and
    a milestone names a place you can go — all rendered in the same muted
    text as the created date beside them.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # Progress is drawn, not divided in the reader's head.
    assert "style={{ width: `${(done / criteria.length) * 100}%` }}" in component
    assert "done === criteria.length" in component
    assert 'done === criteria.length\n                ? "text-primary"' in component

    # Only the ends of the scale take a colour: a board where every card is
    # tinted says nothing.
    assert 'card.priority === "high"' in component
    assert "border-destructive/45 bg-destructive/10" in component

    # Each blocker is its own chip because each is a card id you go and look
    # at, and it is warning-coloured because it is why nothing is moving.
    assert "border-warning/50 bg-warning/10" in component

    # The milestone is the same link the card carries.
    assert "roadmapHref && card.phase ? (" in component
    assert "roadmapHref={roadmapHref}" in component


def test_the_filter_shortcut_works_on_a_freshly_loaded_page() -> None:
    """`/` did nothing until something inside the board had been clicked.

    A fresh page leaves focus on <body>, which is exactly when the badge in
    the field is read and the key is pressed. `body` still means "no other
    control has claimed this key", so the WCAG 2.1.4 protection the guard
    exists for is intact: compact boards never bind it, and a press while
    typing is still ignored.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "active === document.body ||" in component
    assert "sectionRef.current?.contains(active)" in component
    # Still off for embedded miniatures, and still off while typing.
    assert "if (compact) {\n      return\n    }" in component
    assert 'active.tagName === "INPUT"' in component


def test_a_card_has_no_link_out_of_the_board() -> None:
    """The milestone used to navigate to the roadmap from the card's top line.

    That put a link directly above the title, so the top of a card left the
    page and the rest of it opened the card — two destinations in one
    object, and the one you hit by aiming slightly high took you away. The
    roadmap link lives in the dialog's rail now, one press further in.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function CardKey({ card }: { card: KanbanCard }) {" in component
    # No href anywhere in the milestone reading, and the prop that fed it is
    # gone from the card entirely.
    key = component[
        component.index("function CardKey(") : component.index("function CardTitle(")
    ]
    assert "href" not in key
    assert "roadmapHref" not in key
    # It still resolves from the dialog.
    assert "href={`${roadmapHref}#${card.phase}`}" in component


def test_the_filter_panel_composes_without_a_second_store() -> None:
    """A panel that clicks filters, over the one expression that holds them.

    The board deliberately deleted its two-store filter: a record of facet
    values written by menus plus the text, which could disagree. So the panel
    holds nothing. Every row derives from the parsed expression on the way to
    the screen, and every click rewrites that expression with `termSource`,
    the same speller the board uses.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "function FilterPanel({" in component
    assert 'data-slot="kanban-filter-panel"' in component
    # No panel state: it takes the parsed terms and hands back text.
    assert "terms: QueryTerm[]" in component
    assert "onChange: (next: string) => void" in component
    assert "function valueState(" in component
    assert "terms: QueryTerm[]" in component

    # Three states per value, so exclusion is reachable by clicking.
    assert 'type ValueState = "off" | "in" | "out"' in component
    assert 'state === "off"\n                              ? "in"' in component
    assert 'state === "in"\n                                ? "out"' in component

    # The count is of the query you would get, not of the value alone. A
    # faceted panel that counts a value in isolation lies whenever the field
    # already has one, because a click ORs into it rather than replacing it.
    assert "function countWith(" in component
    assert (
        'countMatches(board, parseQuery(withValue(terms, key, value, "in")))'
        in component
    )

    # Anything the panel cannot draw is listed as written and never
    # rewritten. Dropping it silently is the failure this exists to avoid.
    assert "const undrawn = terms.filter(" in component
    assert "Also" in component


def test_the_card_face_shows_every_assignee_and_a_size_chip() -> None:
    """A card can carry several people and a size now, and the face keeps up.

    The interface catches up with the build (`assignee` is a list; `size`
    and `source` exist), the face renders every assignee instead of one,
    and the size sits as a chip at the line's end. The `high priority ·
    @name` middot separator dies with the single-assignee form; flex gap
    spaces the line instead.
    """
    text = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text(encoding="utf-8")

    assert "assignee: string[]" in text
    assert "size?: string" in text
    assert "source?: string" in text
    assert "{card.assignee.map((name) => (" in text  # face renders the list
    assert "card.size" in text


def test_the_size_checkboxes_list_the_scale_in_order() -> None:
    """The panel's size checkboxes follow the scale S→XL, not the order the
    board's cards happen to mention sizes — that ordering is panel-only and
    unreachable from the extracted filter language, so it is pinned here."""
    text = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text(encoding="utf-8")

    assert 'const SIZE_ORDER = ["S", "M", "L", "XL"]' in text
    assert 'const CHECK_FIELDS = ["status", "priority", "size"]' in text
    assert 'const SELECT_FIELDS = ["type", "milestone", "assignee", "source"]' in text
    assert "SIZE_ORDER.indexOf(a[0]) - SIZE_ORDER.indexOf(b[0])" in text


def test_the_composer_selects_are_searchable_comboboxes() -> None:
    """The four sole-value fields draw one custom combobox, not a native
    select: a proper listbox with option roles, a search box once the value
    list is long, and an Escape that closes the open panel instead of
    tearing the whole rail down."""
    text = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text(encoding="utf-8")

    assert "function PanelCombobox(" in text
    assert "PanelSelect" not in text
    assert "const SEARCH_THRESHOLD = 8" in text
    # APG select-only combobox: aria-activedescendant is unsupported on a
    # plain button, so the trigger carries the combobox role.
    assert 'role="combobox"' in text
    assert 'aria-haspopup="listbox"' in text
    assert 'role="listbox"' in text
    assert 'role="option"' in text
    # Escape closes the panel, not the rail. Both handlers sit ON `document`
    # (Next hydrates React's delegated listeners there), and stopPropagation
    # never suppresses same-target listeners — so the combobox stops
    # immediate propagation and the rail defers to `defaultPrevented`.
    assert "Escape belongs to the open panel first." in text
    assert "event.nativeEvent.stopImmediatePropagation()" in text
    assert "if (event.defaultPrevented) {" in text
    assert (
        text.count("event.stopPropagation()") >= 3
    )  # Move-to + filter input + combobox
    # Focus walking out (Tab, the "/" shortcut) closes the panel without
    # refocus, so no stray click can land on a still-painted option.
    assert "rootRef.current?.contains(event.relatedTarget" in text
    # In-combobox mousedowns keep focus put, so that close only fires for
    # genuine departures: Safari and macOS Firefox never focus a button on
    # mousedown (trigger), and scrollbar/padding presses must not blur the
    # search input (panel) — the input itself keeps its caret default.
    assert (
        text.count("onMouseDown={(event) => event.preventDefault()}") >= 2
    )  # trigger + option rows
    assert "if (event.target !== searchRef.current) {" in text  # panel container
    # Opening seeds the active row to the field's current value — Enter on a
    # just-opened list must not clear the filter to "any".
    assert "const seeded = options.findIndex(" in text
    # The search box keeps its caret keys: Home/End fall through to it.
    assert "event.target === searchRef.current" in text


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
    from folio.plugins.kanban import KANBAN_TYPES

    assert "  type: string\n" in KANBAN_TYPES
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


def test_the_dialog_threads_comments_like_a_mail() -> None:
    """Comments are the card's conversation — the trail is its record — so
    they draw as their own separated band above the artifacts, the thread
    before the attachments. No comments, no band: a mail without replies
    shows no empty thread.
    """
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    assert "interface KanbanComment" in component
    assert "comments?: KanbanComment[]" in component
    assert "{comments.length > 0 ? (" in component
    assert "Comments · ${comments.length}" in component
    # The text speaks the same markdown as the rest of the prose.
    assert "<MdInline text={comment.text} />" in component
    # Thread above attachments, and both are capped keyboard-reachable
    # scroll containers — the SAME cap, as the spec promises.
    assert component.index('aria-label="Comments"') < component.index(
        'aria-label="Artifacts"'
    )
    assert component.count("max-h-44 shrink-0 overflow-y-auto") >= 2

    # The emitted stub interface carries the type for generated data.
    from folio.plugins.kanban import KANBAN_TYPES

    assert "export interface KanbanComment {" in KANBAN_TYPES
    assert "  comments: KanbanComment[]\n" in KANBAN_TYPES


# --- Task 1: routes.public learns to be a path ---


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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
        Path(__file__).parents[1] / "template" / "components" / "redirect-page.tsx"
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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
    assert redirect_view.layout == "folio.public"
    redirect_block = redirect_view.slots["main"][0]
    assert redirect_block.component == "RedirectPage"
    assert redirect_block.props["to"] == "../"

    # RedirectPage component is registered
    assert "RedirectPage" in registry.components


def test_public_at_custom_path_registers_redirect_view(tmp_path: Path) -> None:
    """When public: "/board" the redirect view points to "../board/"."""
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
    from folio.extensions import ExtensionRegistry, register_builtin_extensions

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
    assert all(
        not column["cards"] for column in config.extra["kanban"]["columns"]
    )

    new_card = tmp_path / "board" / "cards" / "hot-added.md"
    new_card.write_text("---\ntitle: Hot added\nstatus: backlog\n---\n")
    builder = _PageBuilder()
    applied = []
    builder.apply_extensions = applied.append
    handled = kanban_plugin.on_watched_change(
        builder, config, str(new_card), "added"
    )
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
        kanban_plugin.on_watched_change(builder, config, str(outside), "added")
        is False
    )


def test_icons_survive_renormalization_and_reach_the_contract() -> None:
    """active_kanban re-normalizes plugin-overridden boards; the icon map
    rides along and re-stamps the cards, and the TS contract carries the
    field the component renders."""
    from folio.plugins.kanban import KANBAN_TYPES, active_kanban

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

    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()
    # One render site: a small chip in the face's meta row, beside the
    # priority chip — not a second title mark, not a dialog header prefix.
    assert component.count("{card.icon ? (") == 1
    assert "card.icon || card.priority" in component
    # The face renders a pill: icon plus the tag that brought it.
    assert "{card.icon}</span> {card.iconTag}" in component


def test_the_tag_filter_has_a_real_dropdown() -> None:
    """The composer's tag field once leaned on a native datalist, and whether
    its suggestions ever appeared was the browser's mood. It is the same
    custom listbox the field selects use now: filtered by the draft through
    filterOptions, keyboard-walkable, one commit per pick."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()
    assert "datalist" not in component
    assert 'const listId = "kanban-filter-tag-listbox"' in component
    assert "const options = filterOptions(suggestions, draft)" in component
    assert 'aria-label="Tag suggestions"' in component
    assert component.count('role="combobox"') >= 1


def test_published_artifacts_read_in_a_drawer() -> None:
    """A published `doc:` or `file:` artifact reads on the board itself: the
    band tile opens a drawer from the left edge instead of leaving for a new
    tab. The compiled page is fetched and unwrapped, never rebuilt; a raw
    file stays in a sandboxed frame; the reading position is a URL
    (?card= and ?artifact=) that restores on load and follows heading
    anchors on hashchange. `pr:` and `url:` artifacts keep the band's link
    out, and an unpublished target stays the plain path it always was."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # The drawer is a landmark of its own, beside the dialog frame.
    assert 'data-slot="kanban-artifact-drawer"' in component

    # Published doc/file tiles open the reader — the button branch sits
    # ahead of the <a target="_blank"> the band keeps for everything
    # readerMode rejects.
    assert "function readerMode(" in component
    assert "onOpen(event.currentTarget)" in component
    assert component.index("if (onOpen) {") < component.index(
        "if (artifact.href) {"
    )

    # A `./` link in the card's prose that names a readable artifact opens
    # the same drawer, through the same openReader a tile click takes.
    assert "onOpen: openReader" in component
    assert "links.onOpen(resolved.index, event.currentTarget)" in component

    # The compiled page is consumed, not duplicated; raw files stay caged.
    assert 'parsed.querySelector("main[data-pagefind-body]")' in component
    assert 'sandbox="allow-scripts"' in component

    # The reading position is a URL that restores on load and stays live on
    # hash change.
    assert 'url.searchParams.set("card", card.uid)' in component
    assert 'url.searchParams.set("artifact", target)' in component
    assert 'window.addEventListener("hashchange", applyHash)' in component


def test_workspace_columns_lay_left_to_right_and_resize() -> None:
    """A five-column workspace board never wraps a second row: one weighted
    grid track per column, with a divider that trades width between
    neighbors (pointer and keyboard) and a double click restoring the even
    split."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
    ).read_text()

    # One track per column at lg and up, carried by a CSS variable so the
    # sm wrap below lg survives.
    assert "lg:[grid-template-columns:var(--kanban-tracks)]" in component
    assert '"--kanban-tracks": columnTracks' in component
    assert "minmax(13rem," in component

    # The divider: a real separator, keyboard reachable, reset on double
    # click, and absent after the last column.
    assert 'role="separator"' in component
    assert 'aria-orientation="vertical"' in component
    assert "cursor-col-resize" in component
    assert "onDoubleClick={() => setColumnWeights(null)}" in component
    assert "columnIndex < visibleBoard.length - 1" in component

    # Weights are session view state, never persisted anywhere.
    assert "columnWeights" in component
    assert "localStorage" not in component.split("columnWeights")[1].split(
        "beginColumnResize"
    )[0]
