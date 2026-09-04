---
title: Kanban CLI
description: Every folio board command, what it writes, and the commit it makes.
---

# CLI reference

`folio board` is a command group. Bare invocation is a read-only table; the write subcommands (`add`, `move`, `update`, `trail`, `comment`, `attach`) operate boards: one logical operation, one targeted file edit, optionally one conventional commit.

### Shared behavior

| Option | Meaning |
| --- | --- |
| `--project-dir PATH` | Project directory. Defaults to the current directory. |
| `--config`, `-c` | Config file path. Defaults to `agents.yaml`. |
| `--commit` | On any write command, wraps the operation in one conventional commit scoped to the board directory. |

| What happened | Output | Exit code |
| --- | --- | --- |
| Validation or write error | `Error: <message>` | 1 |
| Usage error (missing argument, bad option) | usage panel | 2 |
| Warning only | `warning: <message>` | 0 |
| Failure upstream of the validator | Python traceback | nonzero |

Scripts should treat any nonzero exit as failure rather than parsing for the `Error:` prefix.

Write commands and `check` require a board directory. When the config has no `board.source`, when the source names a file or missing path, or when a `columns:` key is present, the commands exit 1 and nothing is written. Edits are targeted line surgery, never a YAML round-trip, so hand formatting and comments survive. Structurally unusual files (block scalars, multiline values, flow-style `artifacts:`) get a loud refusal ("edit the file manually") with the file left untouched.

Each write is checked before it is allowed to stand:

| Command | After the edit |
| --- | --- |
| `move`, `update`, `attach` | The whole board is silently reloaded. If the edit made it invalid, the original file bytes are restored — a file attach also deletes the copy, or moves it back — and the command errors with "the edit was rolled back". |
| `add` | The whole board is reloaded, and a rejected card has its new file deleted: a rejected card must never survive to break the next build. |
| `trail`, `comment` | Only the written line is validated, with no full reload. A prose line can warn, but it cannot break board topology. |

### init

```bash
folio board init
```

Creates a board and wires it into the config:

<FileTree tree={`
board/
  board.yaml
  cards/
    read-me-first.md
    _TEMPLATE.md
  SKILL.md
agents.yaml
`} />

`board.yaml` declares three columns, `cards/` holds one starter card and the copy-me template, `SKILL.md` is the in-repo operating protocol, and a `board:` section is appended to `agents.yaml` so the standalone CLI can find it.

| Flag | Meaning |
|---|---|
| `--path` | Board directory to create (default `board`) |
| `--branch` | Branch to create the board on (default `board`) |
| `--no-branch` | Scaffold on the current branch instead |
| `--commit` | Commit the new board and the config change together |

Refuses rather than overwrites; the four refusal conditions are listed in [Start a board](./start/). The config is appended to as text, never round-tripped, so comments and hand formatting survive. The generated board is loaded and validated before the command reports success.

This is the only command that writes `agents.yaml`, and it runs before a board exists; see the rules in [Operating a board](./agents).

### show

```bash
folio board [--project-dir PATH]
folio board show [DIRECTORY]
```

The board as a table: column (with `n/limit` counts), card id, title, type, size, assignee, tags. Blocked cards are marked with the blocking ids. `show` accepts the project directory as a positional argument as an alternative to `--project-dir`; passing both (with different paths) is an error.

A board straight out of `init`, with three cards added and one moved:

```bash
folio board add "Fix flaky test"
folio board add "Ship browser canvas"
folio board add "Write release notes"
folio board move fix-flaky-test in-progress
```

```
                                         my-project Kanban
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Column            ┃ Id                  ┃ Card                ┃ Type ┃ Size ┃ Assignee ┃ Tags    ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ Backlog (3)       │ read-me-first       │ Read me first       │      │      │          │ example │
│                   │ ship-browser-canvas │ Ship browser canvas │      │      │          │         │
│                   │ write-release-notes │ Write release notes │      │      │          │         │
├───────────────────┼─────────────────────┼─────────────────────┼──────┼──────┼──────────┼─────────┤
│ In progress (1/3) │ fix-flaky-test      │ Fix flaky test      │      │      │          │         │
├───────────────────┼─────────────────────┼─────────────────────┼──────┼──────┼──────────┼─────────┤
│ Done (0)          │                     │ -                   │      │      │          │         │
└───────────────────┴─────────────────────┴─────────────────────┴──────┴──────┴──────────┴─────────┘
```

### check

```bash
folio board check
```

Validates the cardfile board — the pre-commit and CI gate. Runs the exact normalization the build runs, prints every warning, and exits 1 on the first topology error (the fail list in [Board formats](./formats#validation)). On success:

```
Board OK: 4 cards across 3 columns
```

### add

```bash
folio board add TITLE [--status ID] [--description TEXT] [--tags LIST] [--assignee LIST] [--priority LEVEL] [--track NAME] [--milestone ID] [--parent ID] [--commit]
```

Creates `cards/<slug-of-title>.md`.

| Flag | Meaning |
| --- | --- |
| `--status`, `-s` | Target column id; defaults to the **first** column. |
| `--description`, `-d` | Initial body text. |
| `--tags` | Comma-separated tags. |
| `--assignee` | Comma-separated assignees. One name is written scalar, several as a list. |
| `--priority` | `low`, `normal`, or `high`. |
| `--track` | Optional workstream inside this product. |
| `--milestone` | Release id for this product, such as `0.2`. |
| `--parent` | Parent card id; must exist on the board. |

The card id is the slugified title. An existing `cards/<id>.md` is an error ("already exists"), as is an unknown `--status` or `--parent`. `created` is set to today. This is the one place the CLI uses a YAML dumper: a brand-new file has no hand formatting to preserve, and the dumper safely quotes titles and tags containing YAML metacharacters.

```bash
folio board add "Fix flaky test" --status backlog --tags ci,tests --priority high --commit
```

### move

```bash
folio board move CARD_ID STATUS [--after CARD] [--commit]
```

A one-line `status` edit. An unknown card or target column errors before anything is written.

| Flag | Meaning |
| --- | --- |
| `--after CARD` | Place the card after an anchor by writing an `order` rank. |
| `--commit` | Commit the move. |

Two conditions **warn instead of refusing**, at exit 0 with the move applied:

| Warning | Condition |
| --- | --- |
| WIP limit | The destination column is at or over its limit. |
| Open blockers | The card has `blocked_by` entries whose card is not in the terminal (last-listed) column. |

The `--after` anchor must be in the destination column and must itself carry a numeric `order`; ranks are the explicit-ordering exception, so the CLI refuses to invent one for the anchor. The new rank is the midpoint between the anchor and the next-higher rank, or anchor + 100 if the anchor is the highest-ranked:

- Anchor at `order: 200`, next rank `300` → the moved card gets `250`.
- Anchor highest at `200` → it gets `300`.

All `--after` validation and math run before any write, so a bad anchor leaves the file untouched. See [Ordering](./formats#ordering-inside-a-column) for the sort rules.

```bash
folio board move fix-flaky-test in-progress --commit
folio board move fix-flaky-test in-progress --after other-card
```

### update

```bash
folio board update CARD_ID --set field=value [--set field=value ...] [--commit]
```

| Flag | Meaning |
| --- | --- |
| `--set field=value` | Repeatable. Only the eleven fields below are accepted. |
| `--commit` | Commit the update. |

The `priority`, `order`, and `created` warnings below print when the board is next loaded, by `check`, `build`, or the next CLI command, rather than at update time: the update's own revalidation runs with warnings suppressed.

| Field | Rule |
| --- | --- |
| `title` | Any string. |
| `assignee` | `--set assignee=ana,bo` writes the list form `assignee: [ana, bo]`; a single name stays scalar. |
| `priority` | `low`, `normal`, or `high`. Any other value warns and sorts as `normal`. |
| `size` | Validated against the scale `S`, `M`, `L`, `XL`: any case in, uppercase written. |
| `order` | The explicit rank. A non-numeric value warns and is ignored. |
| `parent` | Must name an existing card and not the card itself; anything else rolls the edit back. |
| `created` | `YYYY-MM-DD`. Any other shape warns, and the card stops ordering and filtering by date. |
| `type` | Any string. |
| `track` | Any string naming a workstream inside this product. |
| `milestone` | Any string. |
| `source` | Any string. |

Status changes go through `move`; `tags`, `blocked_by`, and `artifacts` stay one-line hand edits by design. A multi-`--set` is atomic: if any pair fails, the whole file is restored.

```bash
folio board update fix-flaky-test --set assignee=claude --set type=bug
folio board update fix-flaky-test --set size=M --set source=folio#fix-flaky
```

### trail

```bash
folio board trail CARD_ID --note TEXT [--ref REF] [--actor NAME] [--commit]
```

| Flag | Meaning |
| --- | --- |
| `--note`, `-n` | Required. Whitespace is collapsed and the result must be non-empty. |
| `--ref` | Commit sha or `PR #n`. Must not contain parentheses or newlines. |
| `--actor` | Defaults to the slugified git `user.name`, falling back to `local`. |
| `--commit` | Commit the trail line. |

Appends one session-trail line at the **end** of the `## Trail` section, creating the section at the end of the file if missing. The date is always today.

```bash
folio board trail fix-flaky-test --note "root cause found" --ref abc1234
```

### comment

```bash
folio board comment CARD_ID TEXT [--by NAME] [--commit]
```

| Flag | Meaning |
| --- | --- |
| `--by` | Author name. Defaults to the slugified git `user.name`. |
| `--commit` | Commit the comment. |

Appends one comment at the **end** of the `## Comments` section, creating the section at the end of the file if missing. The date is always today; the text has its whitespace collapsed and must be non-empty.

```bash
folio board comment fix-flaky-test "the retry masks the race — see the trail ref" --by peter
```

### attach

```bash
folio board attach CARD_ID [PATH] [--move] [--label TEXT] [--commit]
folio board attach CARD_ID (--doc PATH | --api SYMBOL | --file PATH | --pr N | --url URL) [--label TEXT] [--commit]
```

Two forms, one at a time: a file path, or exactly one artifact flag.

**A file path** copies the file into `cards/<id>/`, creating the directory if needed — that alone is the attach, since `artifacts:` derives from the directory. The card file stays untouched unless `--label` is given, which also appends one line naming the sibling by its bare name (`doc` for `.md`/`.mdx`, `file` otherwise) so the label lands on the derived entry. `--move` moves the file instead of copying it.

| Flag | Meaning |
| --- | --- |
| `--move` | Move `PATH` instead of copying it. |
| `--label` | Also write the bare-name label carrier line. |
| `--commit` | Commit the file, and the card when `--label` was given. A moved tracked source's deletion rides the same commit. |

Refused: a `PATH` that is missing or not a regular file; a filename already present in the card's directory (remove or rename first — labelling an existing sibling is the `--file` form's job); a name starting with `.` or `_`, which derivation skips, so nothing would publish. After the write the whole board is revalidated; on failure the copy is deleted — or moved back to its source — and the card file restored.

```bash
folio board attach fix-flaky-test .artifacts/flaky-analysis.md --label "Flaky analysis"
folio board attach fix-flaky-test /tmp/repro.sh --move
```

**An artifact flag** appends one line to the `artifacts:` block, creating the block if missing — the form for what is not a file, and for labels.

| Flag | Target |
| --- | --- |
| `--doc` | Project-relative Markdown path. |
| `--api` | API symbol; any non-empty string. |
| `--file` | Project-relative path, optionally with an `#L12` fragment. |
| `--pr` | Pull request number; must be positive. |
| `--url` | URL, subject to the href scheme policy. |
| `--label` | Optional display label, valid on any kind. |
| `--commit` | Commit the artifact line. |

Shape is validated before the write; target validation runs through the full-board revalidation, so a `javascript:` URL or an escaping path is rolled back. A `--doc`/`--file` path that resolves to no file lands and warns at `check` and build time instead — a stale path is prose, not topology. For a file already in the card's directory, attaching by its bare name adds a label to the derived artifact rather than a second entry. A flow-style `artifacts: [...]` block is refused with "edit the file manually".

```bash
folio board attach fix-flaky-test --doc docs/research/analysis.md
folio board attach fix-flaky-test --url https://example.com/spec --label Spec
```

### `--commit`

One operation, one commit, scoped to the board directory:

1. `git add -- <board-dir>`
2. If the board directory has no changes: prints "nothing to commit (the board was already in this state)" and exits 0 without committing.
3. `git commit -m "<message>" -- <board-dir>`

Only files under the board directory are ever staged or committed, so a board commit never carries unrelated project changes. Two exceptions stage what the operation itself touched outside the board: `folio board init` stages the `board:` section it appended to `agents.yaml`, because a board without its config entry is not yet loadable; and `attach --move` of a git-tracked source stages the source's deletion, because the deletion is the other half of the move. A git failure is an error (exit 1).

| Command | Commit message |
| --- | --- |
| `init` | `board: init` |
| `add` | `board: add <id>` |
| `move` | `board: <id> <from> -> <to>` |
| `update` | `board: update <id>` |
| `trail` | `board: trail <id>` |
| `comment` | `board: comment on <id>` |
| `attach` (typed flag) | `board: attach <kind> to <id>` |
| `attach` (file) | `board: attach <id> <filename>` |
