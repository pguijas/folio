import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs/agents/board"
COMPONENT_DOC = Path(__file__).resolve().parents[1] / "docs/agents/board-component.md"
TSX = Path(__file__).resolve().parents[1] / "folio_agents/assets/kanban-board.tsx"
INIT_COLUMNS = {"backlog", "in-progress", "done"}

# Both forms the pages use: the site-absolute /docs/kanban/<page>#x and
# the sibling-relative ./<page>#x. The lookbehind keeps ../ out of the match,
# and the cards/ exclusion keeps compiled card pages (not siblings) out too.
ANCHOR_LINK = re.compile(
    r"(?:/docs/kanban/(?!cards/)|(?<![.\w])\./)(?:([a-z0-9-]+)/?)?#([^)\s]+)"
)
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def _slug(heading: str) -> str:
    """The heading-id rule the built site uses: backticks are markup, spaces
    become dashes, anything outside [a-z0-9-] is dropped, interior dash runs
    collapse. A leading run is kept whole, so ### `--commit` stays --commit."""
    text = heading.replace("`", "").lower().replace(" ", "-")
    text = re.sub(r"[^a-z0-9-]", "", text)
    lead = len(text) - len(text.lstrip("-"))
    return "-" * lead + re.sub(r"-{2,}", "-", text[lead:])


def _anchors(page: Path) -> set:
    """H2 and below only: the built page renders its H1 without an id, so an
    anchor naming the title would resolve here and 404 in the browser."""
    body = FENCE.sub("", page.read_text())
    return {_slug(h) for h in re.findall(r"^#{2,6} +(.+?)\s*$", body, re.MULTILINE)}


def test_kanban_anchor_links_resolve():
    """Every anchor link between the kanban pages must land on a heading that
    exists. Sections move between these pages; a link into one that moved is a
    404 no build step catches."""
    targets = {page.stem: _anchors(page) for page in DOCS.glob("*.md")}
    broken, checked = [], 0
    for page in sorted(DOCS.glob("*.md")):
        for route, anchor in ANCHOR_LINK.findall(FENCE.sub("", page.read_text())):
            checked += 1
            target = route or "index"
            if anchor not in targets.get(target, set()):
                broken.append(f"{page.name} -> /{target}#{anchor}")
    assert checked >= 8, f"the link collector found only {checked} anchored links"
    assert not broken, f"anchors with no matching heading: {broken}"


def test_doc_examples_use_init_columns():
    """Every status:/move example under docs/agents/board/*.md must
    name a column that folio board init scaffolds, so a reader copying
    examples onto a fresh board never assembles an invalid one."""
    used = set()
    for page in DOCS.glob("*.md"):
        text = page.read_text()
        used |= set(re.findall(r"^status: (\S+)", text, re.MULTILINE))
        used |= set(re.findall(r"folio board move \S+ (\S+)", text))
    # Column ids are lowercase slugs; drop signature placeholders (STATUS),
    # flags (--commit), and ellipses that the capture group also picks up.
    used = {u for u in used if re.fullmatch(r"[a-z][a-z0-9-]*", u)}
    assert used <= INIT_COLUMNS, f"docs use undeclared columns: {used - INIT_COLUMNS}"


def test_component_docs_cover_all_data_slots():
    """Every data-slot value in the tsx must appear in the component
    documentation's slot table, so the theming surface is fully documented."""
    tsx_text = TSX.read_text()
    # Extract constant string data-slot values (not template literals/variables)
    tsx_slots = set(re.findall(r'data-slot="([a-z-]+)"', tsx_text))
    doc_text = COMPONENT_DOC.read_text()
    doc_slots = set(re.findall(r'`data-slot="([a-z-]+)"`', doc_text))
    assert tsx_slots <= doc_slots, f"undocumented slots: {tsx_slots - doc_slots}"


def test_component_docs_do_not_require_an_active_project_board():
    """The repository docs build without activating its operational board."""
    prose = FENCE.sub("", COMPONENT_DOC.read_text())
    assert "<KanbanBoard" not in prose
