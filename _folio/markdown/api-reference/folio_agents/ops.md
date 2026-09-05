# folio_agents.ops 

Board operations as importable functions — the write path every surface shares.

The CLI's subcommands, the serve write API, and any future mount all call
these four operations; each one is a targeted file edit through the
verified surgery in ``kanban_edit``, a board revalidation with rollback,
and optionally one conventional commit whose pathspec is limited to the
touched card file. Refusals raise (``OpError``, or ``ExpectationError``
when the board moved under the caller); nothing here prints.

## Classes

A refused operation: bad input, unknown ids, a failed commit.

The caller's picture of the board is stale; nothing was written.

Block mappings, inline sequences — the format the rest of the CLI reads.

The mapping has to be block style: every other command edits card
frontmatter by line surgery, so a card dumped as
``{title: ..., status: ...}`` could never be moved again — ``move``
looked for a ``status:`` line, found none, and refused the file as
structurally unusual.

The sequences have to stay inline: ``tags: [cli, core]`` is the one-line
hand edit the format documents, and PyYAML's ``default_flow_style`` is
all-or-nothing, so the two rules need a representer rather than a flag.

## Functions

### `_represent_flow_sequence` 

```python
def _represent_flow_sequence(dumper: yaml.SafeDumper, data: list) -> Any
```

**Returns:** `Any` - 

### `resolve_actor` 

```python
def resolve_actor() -> str
```

**Returns:** `str` - 

### `_today` 

```python
def _today() -> str
```

**Returns:** `str` - 

### `_project_dir` 

```python
def _project_dir(board_dir: Path, project_dir: Optional[Path]) -> Path
```

**Returns:** `Path` - 

### `_load_board` 

```python
def _load_board(board_dir: Path, project_dir: Path) -> dict[str, Any]
```

**Returns:** `dict[str, Any]` - 

### `_card_path` 

```python
def _card_path(board_dir: Path, card_id: str) -> Path
```

**Returns:** `Path` - 

### `_find_card` 

```python
def _find_card(board: dict[str, Any], card_id: str) -> tuple[dict, dict]
```

**Returns:** `tuple[dict, dict]` - 

### `revalidate_or_rollback` 

```python
def revalidate_or_rollback(board_dir: Path, project_dir: Path, path: Path, original: str) -> None
```

Board-level validation after an edit; a bad board never survives.

The line-surgery editor verifies each file in isolation, but only a
full reload catches board-topology damage (a dangling parent set via
update, an artifact whose doc target is missing). On failure the card
file gets its original bytes back before the error propagates.

**Returns:** `None` - 

### `commit_paths` 

```python
def commit_paths(project_dir: Path, paths: list[Path], message: str) -> bool
```

Stage and commit exactly ``paths``; True when a commit was made.

False means the working tree already held this state — not an error,
the caller decides whether that is worth a word.

**Returns:** `bool` - 

### `compute_after_rank` 

```python
def compute_after_rank(column: dict[str, Any], after: str)
```

The midpoint rank for an after-anchor, computed from the pre-edit board.

### `_rank` 

```python
def _rank(card: dict[str, Any]) -> float | None
```

**Returns:** `float | None` - 

### `move_card` 

```python
def move_card(board_dir: Path, card_id: str, status: str, *, expect_status: str | None = None, after: str | None = None, actor: str = '', commit: bool = True, project_dir: Optional[Path] = None) -> OpResult
```

Move a card to another column — a one-line ``status:`` edit.

**Returns:** [`OpResult`](/docs/api-reference/folio_agents/ops#opresult) - 

### `update_card` 

```python
def update_card(board_dir: Path, card_id: str, field_name: str, value: str, *, actor: str = '', commit: bool = True, project_dir: Optional[Path] = None) -> OpResult
```

Set one allowlisted frontmatter field (assignee takes a comma list).

**Returns:** [`OpResult`](/docs/api-reference/folio_agents/ops#opresult) - 

### `comment_card` 

```python
def comment_card(board_dir: Path, card_id: str, text: str, *, actor: str = '', commit: bool = True, project_dir: Optional[Path] = None) -> OpResult
```

Append one comment to the card's thread (always at the end).

**Returns:** [`OpResult`](/docs/api-reference/folio_agents/ops#opresult) - 

### `add_card` 

```python
def add_card(board_dir: Path, title: str, *, status: str = '', description: str = '', tags: list[str] | None = None, priority: str = '', track: str = '', milestone: str = '', parent: str = '', assignee: list[str] | None = None, actor: str = '', commit: bool = True, project_dir: Optional[Path] = None) -> OpResult
```

Create a new card file; an empty status lands in the first column.

**Returns:** [`OpResult`](/docs/api-reference/folio_agents/ops#opresult) -
