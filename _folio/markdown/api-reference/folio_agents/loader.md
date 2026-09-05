# folio_agents.loader 

Cardfile board loader for ``board.source: <dir>/``.

One card, one Markdown file. ``board.yaml`` holds the column set (and only
the column set); every card lives in ``cards/<id>.md`` where the filename
stem is the card's immutable id, frontmatter carries machine state (status,
tags, relations, artifacts) and the Markdown body carries human/agent prose
(description, acceptance criteria, trail). Column membership is the
``status:`` field, so moving a card is a one-line diff and two concurrent
sessions editing different cards can never produce a merge conflict.

Validation contract (mirrors the plugin's fail-fast configure dispatch):
board topology errors — unparseable frontmatter, missing title/status,
unknown status, dangling parent/blocked_by, malformed artifacts, escaping
doc/file artifact targets — raise ``ValueError`` and stop the build loudly.
Prose-grammar problems (a trail bullet that doesn't parse, an unknown
priority, a doc/file target that resolves to no file, a card directory
whose card is gone) degrade with a warning: a typo in a note must never
break a build, a typo in board topology must never silently ship a wrong
board.

## Functions

### `is_board_dir` 

```python
def is_board_dir(path: Path) -> bool
```

True when ``board.source`` points at a cardfile board directory.

**Returns:** `bool` - 

### `load_board_dir` 

```python
def load_board_dir(board_dir: Path, *, project_dir: Path) -> dict[str, Any]
```

Load a cardfile board into ``{"title": ..., "columns": [...]}``.

Columns come back in board.yaml order with their cards already grouped
(by ``status:``) and sorted; card dicts are raw-but-validated and carry
the extended fields that ``kanban._normalize_card`` normalizes into the
emitted TS contract.

**Returns:** `dict[str, Any]` - 

### `_load_board_meta` 

```python
def _load_board_meta(board_file: Path) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_load_cards` 

```python
def _load_cards(cards_dir: Path, *, column_ids: list[str]) -> list[dict[str, Any]]
```

**Returns:** `list[dict[str, Any]]` - 

### `_load_card` 

```python
def _load_card(path: Path, *, column_ids: list[str]) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_parse_body` 

```python
def _parse_body(body: str, *, path: Path) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]
```

**Returns:** `tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]` - 

### `_validate_relations` 

```python
def _validate_relations(cards: list[dict[str, Any]]) -> None
```

**Returns:** `None` - 

### `_resolve_artifacts` 

```python
def _resolve_artifacts(cards: list[dict[str, Any]], *, cards_dir: Path, project_dir: Path) -> None
```

Derive each card's artifacts from its directory, then merge the block.

The directory is the record: one artifact per regular file at its top
level, name-sorted — ``doc`` for Markdown and MDX, ``file`` for the rest.
Dotfiles, ``_``-prefixed names, subdirectories, and symlinks stay behind,
the same lines publishing already draws. The frontmatter block survives
for what is not a file — ``pr:``, ``url:``, ``api:`` — and for labelling
a sibling: a ``doc:``/``file:`` entry naming one (bare name, ``./`` form,
or the full project-relative path) lands its label on the derived entry
instead of appearing twice.

Every entry carries ``display``, the target as the author wrote it (the
bare name for a derived sibling nothing labels), and ``target``, always a
project-relative path. A ``doc:``/``file:`` target resolves against the
card's directory first, then the project root — the order a relative
markdown link already implies. One that resolves to no file warns and
stays: a stale path in one card's frontmatter is not board topology.
Only an absolute path or one escaping the project still raises.

**Returns:** `None` - 

### `_derived_sibling_artifacts` 

```python
def _derived_sibling_artifacts(sibling_dir: Path, *, cards_prefix: str, card_id: str) -> list[dict[str, Any]]
```

One artifact per visible regular file at the directory's top level.

**Returns:** `list[dict[str, Any]]` - 

### `_sibling_name` 

```python
def _sibling_name(path_part: str, *, cards_prefix: str | None, card_id: str) -> str | None
```

The top-level sibling a written target names, or ``None``.

Three spellings reach a sibling: the bare name, the ``./`` form a
markdown link would use, and the legacy full project-relative path
existing boards carry.

**Returns:** `str | None` - 

### `_resolve_file_target` 

```python
def _resolve_file_target(path_part: str, *, kind: str, written: str, fragment: str, card_id: str, card_dir: Path | None, project_dir: Path, project_root: Path) -> str
```

A ``doc:``/``file:`` target as a project-relative path, or a warning.

The card's directory is tried first, then the project root. A target the
card resolves is recorded at its project-relative address, so everything
downstream keeps one path grammar; one the project resolves is already
written in it and stays as written.

**Returns:** `str` - 

### `_warn_orphan_directories` 

```python
def _warn_orphan_directories(cards_dir: Path, *, card_ids: set[str]) -> None
```

Name every directory whose card is gone — shape B's one drift risk.

The filename stem names the directory, so a card renamed or deleted
leaves its directory behind and nothing publishes an unclaimed one. Dot
and ``_`` prefixes keep their existing meanings — editor scratch and
"not the board's business" — and stay quiet.

**Returns:** `None` - 

### `parse_artifact` 

```python
def parse_artifact(raw: Any, *, card_id: str) -> tuple[str, str, str]
```

One artifact entry -&gt; ``(kind, target, label)``.

The committed form is a one-line single-key map — ``- doc: research/x.md``
— with an optional ``label:`` sibling key.

**Returns:** `tuple[str, str, str]` - 

### `_sort_key` 

```python
def _sort_key(card: dict[str, Any]) -> tuple
```

Deterministic intra-column order: rank, then priority, created, id.

``order:`` is the rare escape hatch — ranked cards sort first among
themselves; everything else falls back to computed order so reordering
never has to touch another card's file.

**Returns:** `tuple` -
