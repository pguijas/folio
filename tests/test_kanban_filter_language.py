"""The board's filter language, executed rather than grepped.

Every other test of `kanban-board.tsx` asserts that a string appears in the
file. That catches a deletion and nothing else: the defect this file exists
for — `tag:"core",spec` selecting no cards while `tag:spec,"core"` selected
the right ones — was invisible to all of them, because both spellings were
present in the source the whole time.

So this lifts the query language out of the component and runs it. Node 24
strips TypeScript types on its own, so there is no build step and no
transpiler to keep in sync; the functions are read from the real file, and a
rename breaks this loudly rather than silently passing.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

COMPONENT = (
    Path(__file__).parents[1] / "template" / "components" / "kanban-board.tsx"
)

# The language and nothing else: the field table, the types it needs, and the
# six functions between an input string and a yes/no for one card.
BLOCKS = (
    r"\ninterface FilterField \{.*?\n\}\n",
    r"\ntype CompareOp =.*?\n",
    r"\ninterface QueryAlternative \{.*?\n\}\n",
    r"\ninterface QueryTerm \{.*?\n\}\n",
    r"\nconst FULL_ISO_DATE =.*?\n",
    r"\nconst FILTER_FIELDS: FilterField\[\] = \[.*?\n\]\n",
    r"\nfunction tokenizeQuery.*?\n\}\n",
    r"\nfunction firstColonOutsideQuotes.*?\n\}\n",
    r"\nfunction splitAlternatives.*?\n\}\n",
    r"\nfunction readAlternative.*?\n\}\n",
    r"\nfunction parseQuery.*?\n\}\n",
    r"\nfunction matchesAlternative.*?\n\}\n",
    r"\nfunction matchesTerm\(.*?\n\}\n",
)

# The rewrite helpers: extract for round-trip testing.
REWRITE_BLOCKS = (
    r"\ntype ValueState =.*?\n",
    r"\nfunction soleValue\(.*?\n\}\n",
    r"\nfunction withSoleValue\(.*?\n\}\n",
    r"\nfunction withValue\(.*?\n\}\n",
    r"\nfunction termSource\(.*?\n\}\n",
    r"\nfunction quoteValue\(.*?\n\}\n",
)

# `matchesTerm` is written against the component's KanbanCard; this is the
# part of that shape the ten fields actually read.
CARD_TYPE = """
interface KanbanCard {
  title: string
  description: string
  id?: string
  milestone?: string
  tags: string[]
  priority?: string
  assignee?: string[]
  size?: string
  source?: string
  type?: string
  parent?: string
  blocked_by?: string[]
  created?: string
  artifacts?: { kind: string; target: string }[]
}
"""

HARNESS = """
const FIELD_BY_NAME = new Map<string, FilterField>()
for (const field of FILTER_FIELDS) {
  FIELD_BY_NAME.set(field.key, field)
  for (const alias of field.aliases ?? []) {
    FIELD_BY_NAME.set(alias, field)
  }
}

const cards: KanbanCard[] = JSON.parse(process.argv[2])
const queries: string[] = JSON.parse(process.argv[3])
const columnId: string = process.argv[4]
const columnTitle: string = process.argv[5]

const answers: Record<string, string[]> = {}
for (const query of queries) {
  const terms = parseQuery(query)
  answers[query] = cards
    .filter((card) => terms.every((t) => matchesTerm(t, card, columnId, columnTitle)))
    .map((card) => card.title)
}
console.log(JSON.stringify(answers))
"""


def _extract(source: str) -> str:
    parts = [CARD_TYPE]
    for pattern in BLOCKS:
        match = re.search(pattern, source, re.S)
        assert match, f"kanban-board.tsx no longer contains {pattern!r}"
        parts.append(match.group(0))
    parts.append(HARNESS)
    return "".join(parts)


def _extract_rewrite(source: str) -> str:
    parts = [CARD_TYPE]
    for pattern in BLOCKS:
        match = re.search(pattern, source, re.S)
        assert match, f"kanban-board.tsx no longer contains {pattern!r}"
        parts.append(match.group(0))
    for pattern in REWRITE_BLOCKS:
        match = re.search(pattern, source, re.S)
        assert match, f"kanban-board.tsx no longer contains {pattern!r}"
        parts.append(match.group(0))
    # Harness for rewrite testing
    parts.append("""
const FIELD_BY_NAME = new Map<string, FilterField>()
for (const field of FILTER_FIELDS) {
  FIELD_BY_NAME.set(field.key, field)
  for (const alias of field.aliases ?? []) {
    FIELD_BY_NAME.set(alias, field)
  }
}

interface RewriteOperation {
  action: "soleValue" | "withSoleValue" | "roundtrip"
  query: string
  key?: string
  value?: string | null
  cards?: KanbanCard[]
}

const operations: RewriteOperation[] = JSON.parse(process.argv[2])
const results = operations.map((operation) => {
  const terms = parseQuery(operation.query)
  if (operation.action === "soleValue") {
    return soleValue(terms, operation.key ?? "")
  }
  if (operation.action === "withSoleValue") {
    return withSoleValue(
      terms,
      operation.key ?? "",
      operation.value ?? null,
    )
  }

  const cards = operation.cards ?? []
  const rebuilt = terms.map(termSource).join(" ")
  const rebuiltTerms = parseQuery(rebuilt)
  const original = cards.filter((card) =>
    terms.every((t) => matchesTerm(t, card, "backlog", "Backlog"))
  ).map((card) => card.title)
  const after = cards.filter((card) =>
    rebuiltTerms.every((t) => matchesTerm(t, card, "backlog", "Backlog"))
  ).map((card) => card.title)
  return { original, after, rebuilt }
})
console.log(JSON.stringify(results))
""")
    return "".join(parts)


@pytest.fixture
def run_queries(tmp_path: Path):
    """Cards and queries in, `query -> matching titles` out — the same
    extracted language, the same Node invocation as the table test."""
    if shutil.which("node") is None:
        pytest.skip("needs node")

    script = tmp_path / "language.ts"
    script.write_text(_extract(COMPONENT.read_text()), encoding="utf-8")

    def run(cards: list[dict], queries: list[str]) -> dict[str, list[str]]:
        result = subprocess.run(
            [
                "node",
                "--experimental-strip-types",
                "--no-warnings",
                str(script),
                json.dumps(cards),
                json.dumps(queries),
                "backlog",
                "Backlog",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)

    return run


def test_multi_assignee_matches_either_name(run_queries):
    cards = [
        {"title": "Pair", "description": "", "tags": [], "assignee": ["ana", "bo"]},
        {"title": "Solo", "description": "", "tags": [], "assignee": ["cara"]},
    ]
    answers = run_queries(cards, ["assignee:ana", "assignee:bo", "assignee:cara", "-assignee:ana"])
    assert answers["assignee:ana"] == ["Pair"]
    assert answers["assignee:bo"] == ["Pair"]
    assert answers["assignee:cara"] == ["Solo"]
    assert answers["-assignee:ana"] == ["Solo"]


def test_size_and_source_filter_case_insensitively(run_queries):
    cards = [
        {"title": "Small", "description": "", "tags": [], "size": "S", "source": "folio#feat/x"},
        {"title": "Large", "description": "", "tags": [], "size": "XL", "source": "https://github.com/x/y"},
        {"title": "Bare", "description": "", "tags": []},
    ]
    answers = run_queries(
        cards,
        ["size:s", "size:s,xl", "size:none", 'source:"https://github.com/x/y"', "-source:none"],
    )
    assert answers["size:s"] == ["Small"]
    assert answers["size:s,xl"] == ["Small", "Large"]
    assert answers["size:none"] == ["Bare"]
    assert answers['source:"https://github.com/x/y"'] == ["Large"]
    assert answers["-source:none"] == ["Small", "Large"]


CARDS = [
    {
        "title": "Alpha",
        "description": "the first one",
        "id": "alpha-one",
        "tags": ["core", "spec"],
        "milestone": "0.3",
        "priority": "high",
        "type": "bug",
        "created": "2026-08-01",
    },
    {
        "title": "Beta",
        "description": "",
        "id": "beta-two",
        "tags": ["launch"],
        "created": "2026-12-31",
    },
    # A date folio never validated: it reaches the browser as written.
    {"title": "Gamma", "description": "", "id": "gamma", "tags": [], "created": "2026-8-1"},
    {"title": "Delta", "description": "", "id": "delta", "tags": ["core-languages"]},
    {"title": "Epsilon", "description": "", "id": "epsilon", "tags": ["a,b"]},
]

# query -> the titles it must select, in board order.
CASES: dict[str, list[str]] = {
    # The five documented rules.
    "": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    "tag:core priority:high": ["Alpha"],
    "tag:core,launch": ["Alpha", "Beta", "Delta"],
    "-tag:core": ["Beta", "Gamma", "Epsilon"],
    'tag:"core"': ["Alpha"],
    "milestone:none": ["Beta", "Gamma", "Delta", "Epsilon"],
    "milestone:any": ["Alpha"],
    "type:bug": ["Alpha"],
    "-type:bug": ["Beta", "Gamma", "Delta", "Epsilon"],
    "type:none": ["Beta", "Gamma", "Delta", "Epsilon"],
    "type:any": ["Alpha"],
    # The defect this file exists for: both orders, same answer.
    'tag:"core",launch': ["Alpha", "Beta"],
    'tag:launch,"core"': ["Alpha", "Beta"],
    'tag:"core","launch"': ["Alpha", "Beta"],
    # ...without breaking what the shortcut protected.
    'tag:"a,b"': ["Epsilon"],
    'tag:"a,b",launch': ["Beta", "Epsilon"],
    # Unquoted is a substring, quoted is the whole value.
    "tag:core": ["Alpha", "Delta"],
    # Anything that is not a field name is text, over title, description, id.
    "alpha": ["Alpha"],
    "first": ["Alpha"],
    "owner:pedro": [],
    # Ordered comparison, guarded on both sides: Gamma's date is not a date.
    "created:>2026-01-01": ["Alpha", "Beta"],
    "created:<2026-12-31": ["Alpha"],
    "created:>=2026-12-31": ["Beta"],
    # A half-typed date asks nothing rather than asking wrongly.
    "created:>2026-8": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    # Status is the column, by id and by title.
    "status:backlog": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    'status:"backlog"': ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    # Aliases.
    "tags:launch": ["Beta"],
    # A term with no value yet is dropped, so the board never blinks empty.
    "tag:": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    "created:>": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    # Nothing typeable is an error state.
    '"': ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
    ":::": [],
    # A bare `-` is a search for a hyphen, not an empty exclusion: `-`
    # excludes only in front of a real field, because this board's ids are
    # full of hyphens and `-technical-plan` meaning "everything except"
    # would invert what was asked.
    "-": ["Alpha", "Beta"],
    "  ": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
}


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_the_filter_language_answers_what_it_documents(tmp_path: Path) -> None:
    script = tmp_path / "language.ts"
    script.write_text(_extract(COMPONENT.read_text()), encoding="utf-8")

    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            str(script),
            json.dumps(CARDS),
            json.dumps(list(CASES)),
            "backlog",
            "Backlog",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    answers = json.loads(result.stdout)
    wrong = {
        query: {"got": answers[query], "want": want}
        for query, want in CASES.items()
        if answers[query] != want
    }
    assert not wrong, json.dumps(wrong, indent=2)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_rewrite_helpers(tmp_path: Path) -> None:
    """Exercise every rewrite case in one Node process.

    Node spends far more time starting and stripping the extracted TypeScript
    than these pure helpers spend running. Keep each behavioral assertion, but
    pay that fixed boundary cost once.
    """
    script = tmp_path / "rewrite.ts"
    script.write_text(_extract_rewrite(COMPONENT.read_text()), encoding="utf-8")

    # soleValue: no term → "", one single-value positive term → its text,
    # OR list (type:a,b) → null, two positive terms → null, negation only → ""
    sole_cases = [
        ("", "type", ""),
        ("type:bug", "type", "bug"),
        ("type:bug,feature", "type", None),
        ("type:bug type:feature", "type", None),
        ("-type:bug", "type", ""),
        ("tag:spec -type:bug", "type", ""),
        ("type:bug tag:spec", "type", "bug"),
    ]
    # withSoleValue: sets key:value replacing positive terms; value null clears;
    # -type:a survives a set; comparison terms of other fields survive
    sole_set_cases = [
        ("", "type", "bug", "type:bug"),
        ("type:feature", "type", "bug", "type:bug"),
        ("type:feature,plan", "type", "bug", "type:bug"),
        ("-type:feature", "type", "bug", "-type:feature type:bug"),
        ("tag:spec -type:feature", "type", "bug", "tag:spec -type:feature type:bug"),
        ("created:>=2026-01-01", "type", "bug", "created:>=2026-01-01 type:bug"),
        ("type:bug", "type", None, ""),
        ("tag:spec type:bug", "type", None, "tag:spec"),
    ]
    # Round-trip: parseQuery → termSource each → parseQuery again yields matching
    # behavior on the card set
    roundtrip_cases = [
        "tag:spec -priority:high type:bug created:>=2026-01-01",
        "tag:core,launch",
        'tag:"core" priority:high',
        "status:backlog milestone:0.3",
        "created:<2026-12-31 -tag:launch",
    ]

    operations = [
        {"action": "soleValue", "query": query, "key": key}
        for query, key, _ in sole_cases
    ]
    operations.extend(
        {
            "action": "withSoleValue",
            "query": query,
            "key": key,
            "value": value,
        }
        for query, key, value, _ in sole_set_cases
    )
    operations.extend(
        {"action": "roundtrip", "query": query, "cards": CARDS}
        for query in roundtrip_cases
    )
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            str(script),
            json.dumps(operations),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    outputs = json.loads(result.stdout)

    offset = 0
    for (query, key, want), got in zip(
        sole_cases,
        outputs[offset : offset + len(sole_cases)],
        strict=True,
    ):
        assert got == want, f"soleValue({query!r}, {key!r}) = {got}, want {want}"
    offset += len(sole_cases)

    for (query, key, value, want), got in zip(
        sole_set_cases,
        outputs[offset : offset + len(sole_set_cases)],
        strict=True,
    ):
        assert got == want, (
            f"withSoleValue({query!r}, {key!r}, {value!r}) = {got!r}, "
            f"want {want!r}"
        )
    offset += len(sole_set_cases)

    for query, data in zip(roundtrip_cases, outputs[offset:], strict=True):
        assert data["original"] == data["after"], (
            f"roundtrip {query!r}: original={data['original']}, "
            f"after={data['after']}, rebuilt={data['rebuilt']!r}"
        )


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_filter_options_search_is_substring_and_case_blind(tmp_path: Path) -> None:
    """The combobox's search is `filterOptions`, pure and extracted here:
    case-blind substring on the label, and a blank query filters nothing."""
    source = COMPONENT.read_text()
    match = re.search(r"\nfunction filterOptions\(.*?\n\}\n", source, re.S)
    assert match, "kanban-board.tsx no longer contains filterOptions"
    script = tmp_path / "options.ts"
    script.write_text(
        match.group(0)
        + "\nconst values = JSON.parse(process.argv[2])\n"
        + "const queries = JSON.parse(process.argv[3])\n"
        + "console.log(JSON.stringify(queries.map((query: string) => filterOptions(values, query))))\n",
        encoding="utf-8",
    )

    values = [["feat/plugins-v2", "feat/plugins-v2"], ["main", "main"], ["FEAT/x", "FEAT/x"]]
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            str(script),
            json.dumps(values),
            json.dumps(["feat", "  "]),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    filtered, blank = json.loads(result.stdout)
    assert filtered == [["feat/plugins-v2", "feat/plugins-v2"], ["FEAT/x", "FEAT/x"]]
    assert blank == values  # blank query filters nothing


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_the_inline_md_grammar_is_executed(tmp_path: Path) -> None:
    """The dialog renders the markdown the cards are written in, and the
    grammar is pinned by execution: code spans, bold, http(s) links, and —
    just as load-bearing — everything that must stay literal. A stray
    asterisk is prose; a `javascript:` target never becomes a link, because
    the scheme guard is the token pattern itself, not a sanitizer."""
    source = COMPONENT.read_text()
    match = re.search(r"type MdToken.*?function parseInlineMd.*?\n\}", source, re.S)
    assert match, "kanban-board.tsx no longer carries parseInlineMd"
    script = tmp_path / "md.ts"
    script.write_text(
        match.group(0)
        + "\nconst cases: string[] = JSON.parse(process.argv[2])\n"
        + "console.log(JSON.stringify(cases.map((text) => parseInlineMd(text))))\n",
        encoding="utf-8",
    )

    cases = [
        "run `folio kanban check` now",
        "**The header.** presides",
        "see [the docs](https://example.com/x) here",
        "[evil](javascript:alert(1))",
        "a * b and `unclosed",
        "**`code` inside**",
        "",
        "double `` `code` `` span",
        "``x `y` z``",
    ]
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            str(script),
            json.dumps(cases),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    tokens = json.loads(result.stdout)

    assert tokens[0] == [
        {"kind": "text", "text": "run "},
        {"kind": "code", "text": "folio kanban check"},
        {"kind": "text", "text": " now"},
    ]
    assert tokens[1] == [
        {"kind": "bold", "text": "The header."},
        {"kind": "text", "text": " presides"},
    ]
    assert tokens[2] == [
        {"kind": "text", "text": "see "},
        {"kind": "link", "text": "the docs", "href": "https://example.com/x"},
        {"kind": "text", "text": " here"},
    ]
    # Not http(s): the whole thing stays one literal text token.
    assert tokens[3] == [{"kind": "text", "text": "[evil](javascript:alert(1))"}]
    # Unmatched marks are prose, not a parse error.
    assert tokens[4] == [{"kind": "text", "text": "a * b and `unclosed"}]
    # No nesting: bold wins at its position and keeps the backticks inside.
    assert tokens[5] == [{"kind": "bold", "text": "`code` inside"}]
    assert tokens[6] == []
    # CommonMark double-backtick spans: how a card quotes a backtick. The
    # padding space strips, single backticks inside stay literal — this
    # feature's own spec card writes exactly this shape.
    assert tokens[7] == [
        {"kind": "text", "text": "double "},
        {"kind": "code", "text": "`code`"},
        {"kind": "text", "text": " span"},
    ]
    assert tokens[8] == [{"kind": "code", "text": "x `y` z"}]


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_the_block_md_grammar_is_executed(tmp_path: Path) -> None:
    """The dialog's prose is blocks, not one paragraph: blank lines split,
    consecutive dash lines become a list, numbered lines an ordered one, and
    a dash in the middle of a sentence stays prose. Pinned by execution,
    like the inline grammar above it feeds."""
    source = COMPONENT.read_text()
    match = re.search(r"type MdBlock.*?function parseMdBlocks.*?\n\}", source, re.S)
    assert match, "kanban-board.tsx no longer carries parseMdBlocks"
    script = tmp_path / "blocks.ts"
    script.write_text(
        match.group(0)
        + "\nconst cases: string[] = JSON.parse(process.argv[2])\n"
        + "console.log(JSON.stringify(cases.map((text) => parseMdBlocks(text))))\n",
        encoding="utf-8",
    )

    cases = [
        "Piezas:\n\n- Baldas sala\n- Perchero habitación\n- Mesa",
        "Piezas:\n- a\n- b",
        "1. uno\n2. dos",
        "a - b",
        "una línea\notra línea",
        "",
        "- solo",
        "Piezas:\r\n\r\n- a\r\n- b",
        "- a\n1. uno",
    ]
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            str(script),
            json.dumps(cases),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    blocks = json.loads(result.stdout)

    assert blocks[0] == [
        {"kind": "paragraph", "text": "Piezas:"},
        {
            "kind": "list",
            "ordered": False,
            "items": ["Baldas sala", "Perchero habitación", "Mesa"],
        },
    ]
    # A list needs no blank line after its lead-in.
    assert blocks[1] == [
        {"kind": "paragraph", "text": "Piezas:"},
        {"kind": "list", "ordered": False, "items": ["a", "b"]},
    ]
    assert blocks[2] == [{"kind": "list", "ordered": True, "items": ["uno", "dos"]}]
    # A dash inside a sentence is prose, not a bullet.
    assert blocks[3] == [{"kind": "paragraph", "text": "a - b"}]
    # Single newlines stay inside one paragraph.
    assert blocks[4] == [{"kind": "paragraph", "text": "una línea\notra línea"}]
    assert blocks[5] == []
    assert blocks[6] == [{"kind": "list", "ordered": False, "items": ["solo"]}]
    # Windows line endings split and list cleanly, no \r inside items.
    assert blocks[7] == [
        {"kind": "paragraph", "text": "Piezas:"},
        {"kind": "list", "ordered": False, "items": ["a", "b"]},
    ]
    # Adjacent lists of different kinds stay two lists.
    assert blocks[8] == [
        {"kind": "list", "ordered": False, "items": ["a"]},
        {"kind": "list", "ordered": True, "items": ["uno"]},
    ]


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_card_relative_links_resolve_against_the_card(tmp_path: Path) -> None:
    """The epic's spec sentence is "references are relative, and identical
    everywhere": a body link written `./sibling` is the same string that
    opens the file in an editor. The grammar widens by exactly the `./`
    prefix — every other non-http(s) shape stays literal text — and the
    resolver answers in order: the card's own artifact first, matched by
    display or target and borrowing its build-resolved href; the raw bundle
    at /_folio/kanban/<id>/ for anything unmatched; nothing at all for a
    path that climbs out, an artifact the build left unlinked, or a board
    whose cards have no id to publish under."""
    source = COMPONENT.read_text()
    inline = re.search(r"type MdToken.*?function parseInlineMd.*?\n\}", source, re.S)
    assert inline, "kanban-board.tsx no longer carries parseInlineMd"
    resolver = re.search(
        r"type CardLinkResolution.*?function resolveCardLink.*?\n\}", source, re.S
    )
    assert resolver, "kanban-board.tsx no longer carries resolveCardLink"
    script = tmp_path / "cardlink.ts"
    script.write_text(
        "interface KanbanArtifact {\n"
        "  kind: string\n"
        "  target: string\n"
        "  display?: string\n"
        "  label: string\n"
        "  href: string\n"
        "}\n"
        + inline.group(0)
        + "\n"
        + resolver.group(0)
        + "\nconst artifacts: KanbanArtifact[] = JSON.parse(process.argv[2])\n"
        + "const targets: string[] = JSON.parse(process.argv[3])\n"
        + "const texts: string[] = JSON.parse(process.argv[4])\n"
        + "console.log(JSON.stringify({\n"
        + '  resolved: targets.map((t) => resolveCardLink(t, "epic", artifacts)),\n'
        + '  unowned: targets.map((t) => resolveCardLink(t, "", artifacts)),\n'
        + "  tokens: texts.map((text) => parseInlineMd(text)),\n"
        + "}))\n",
        encoding="utf-8",
    )

    artifacts = [
        {"kind": "pr", "target": "61", "display": "61", "label": "", "href": ""},
        {
            # A sibling derived from the card's directory: display is the
            # bare name, target the resolved path, href the compiled page.
            "kind": "doc",
            "target": "board/cards/epic/prototypes-compared.md",
            "display": "prototypes-compared.md",
            "label": "The comparison",
            "href": "/docs/kanban/epic/prototypes-compared/",
        },
        {
            # A label carrier that wrote the full path: display repeats it,
            # so the body's `./` form must match through the target.
            "kind": "file",
            "target": "board/cards/epic/tree-table.html",
            "display": "board/cards/epic/tree-table.html",
            "label": "",
            "href": "/_folio/kanban/epic/tree-table.html",
        },
        {
            # Written `./` but resolved elsewhere and left unlinked.
            "kind": "doc",
            "target": "design/ghost.md",
            "display": "./ghost.md",
            "label": "",
            "href": "",
        },
    ]
    targets = [
        "./prototypes-compared.md",
        "./tree-table.html",
        "./notes/appendix.css",
        "./../secrets.md",
        "./a/../b.md",
        "./ghost.md",
        "https://example.com/x",
    ]
    texts = [
        "read [the comparison](./prototypes-compared.md) first",
        "[evil](javascript:alert(1))",
        "[up](../escape.md)",
        "[abs](/etc/passwd)",
        "[bare](prototypes-compared.md)",
    ]
    result = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            "--no-warnings",
            str(script),
            json.dumps(artifacts),
            json.dumps(targets),
            json.dumps(texts),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)

    assert out["resolved"] == [
        {"kind": "artifact", "index": 1},
        {"kind": "artifact", "index": 2},
        {"kind": "raw", "href": "/_folio/kanban/epic/notes/appendix.css"},
        None,
        None,
        None,
        None,
    ]
    # A board whose cards publish nowhere has no raw bundle to fall back
    # to; matching an artifact still answers.
    assert out["unowned"][0] == {"kind": "artifact", "index": 1}
    assert out["unowned"][2] is None

    # `./` tokenizes as a link; the scheme guard gives nothing else away.
    assert out["tokens"][0] == [
        {"kind": "text", "text": "read "},
        {
            "kind": "link",
            "text": "the comparison",
            "href": "./prototypes-compared.md",
        },
        {"kind": "text", "text": " first"},
    ]
    for tokens in out["tokens"][1:]:
        assert len(tokens) == 1 and tokens[0]["kind"] == "text"


def test_a_card_with_holes_matches_nothing_instead_of_crashing(run_queries):
    """A card handed in through the `columns` prop, or written by an older
    build's overlay, can lack tags entirely or carry a null where a string
    belongs. The filter answers no for the hole — it never throws."""
    cards = [
        {"title": "Holey", "description": "", "link": ""},
        {"title": "Nully", "description": "", "link": "", "tags": [None, "casa"]},
    ]
    answers = run_queries(cards, ["tag:casa", "tag:none", "-tag:casa"])
    assert answers["tag:casa"] == ["Nully"]
    assert answers["tag:none"] == ["Holey"]
    assert answers["-tag:casa"] == ["Holey"]
