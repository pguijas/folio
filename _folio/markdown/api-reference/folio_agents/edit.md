# folio_agents.edit 

Line-surgery editor for cardfile board cards.

Card files are hand-authored Markdown; a writer that round-trips them
through ``yaml.safe_dump`` would destroy comments, key order, and quoting.
Every mutation here is therefore a targeted line edit — replace one scalar
line, insert one artifact line, append one trail line — followed by a
re-parse verification. When a file is structurally exotic (block scalars,
anchors, a key the surgery cannot find as a plain ``key: value`` line) the
edit refuses loudly and tells the actor to edit the file by hand; a wrong
write never survives, because verification failure restores the original
bytes before raising.

## Classes

A surgical edit could not be applied safely.

## Functions

### `format_trail_entry` 

```python
def format_trail_entry(*, date: str, actor: str, note: str, ref: str = '') -> str
```

The canonical trail line: strict writer, tolerant reader.

**Returns:** `str` - 

### `format_comment_entry` 

```python
def format_comment_entry(*, date: str, actor: str, text: str) -> str
```

The canonical comment line — the trail's grammar minus the ref.

A comment argues; it does not point at a commit. Same strict-writer
contract: the tolerant reader upstream renders anything, so the only
place to keep the section parseable is here.

**Returns:** `str` - 

### `set_scalar` 

```python
def set_scalar(path: Path, key: str, value: Any) -> None
```

Replace (or add) one plain ``key: value`` frontmatter line.

**Returns:** `None` - 

### `set_list` 

```python
def set_list(path: Path, key: str, values: list[str]) -> None
```

Replace (or add) one inline ``key: [a, b]`` frontmatter line.

**Returns:** `None` - 

### `_append_section_line` 

```python
def _append_section_line(path: Path, entry: str, *, heading_re: re.Pattern[str], heading: str, what: str, before_re: re.Pattern[str] | None = None) -> None
```

Append one bullet at the END of a ``## <heading>`` section.

Appending at the tail keeps concurrent-session conflicts predictable:
two appends collide at the same place and the resolution is
mechanically "keep both lines". A missing section is created where
``before_re`` points (comments read before the trail, so they are
created before it), or at the file's end.

**Returns:** `None` - 

### `append_trail` 

```python
def append_trail(path: Path, entry: str) -> None
```

Append one trail line at the END of the ``## Trail`` section.

**Returns:** `None` - 

### `append_comment` 

```python
def append_comment(path: Path, entry: str) -> None
```

Append one comment line at the END of the ``## Comments`` section.

**Returns:** `None` - 

### `insert_artifact` 

```python
def insert_artifact(path: Path, kind: str, target: Any, label: str = '') -> None
```

Insert one artifact item at the end of the ``artifacts:`` block.

**Returns:** `None` - 

### `_artifact_count` 

```python
def _artifact_count(front: str) -> int
```

**Returns:** `int` - 

### `_split` 

```python
def _split(text: str, path: Path) -> tuple[str, str, tuple[int, int]]
```

**Returns:** `tuple[str, str, tuple[int, int]]` - 

### `_assemble` 

```python
def _assemble(original: str, new_front: str, span: tuple[int, int]) -> str
```

**Returns:** `str` - 

### `_continues` 

```python
def _continues(front: str, line_end: int) -> bool
```

True when the next frontmatter line continues this scalar (multiline).

**Returns:** `bool` - 

### `_render_scalar` 

```python
def _render_scalar(value: Any) -> str
```

**Returns:** `str` - 

### `_parses_as_number` 

```python
def _parses_as_number(text: str) -> bool
```

A string that YAML would read as a number must be quoted to stay one.

**Returns:** `bool` - 

### `_write_verified` 

```python
def _write_verified(path: Path, original: str, new_text: str, *, verify, what: str) -> None
```

**Returns:** `None` -
