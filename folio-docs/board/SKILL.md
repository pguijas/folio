---
name: folio-docs-board
description: Use when reading or changing the independent Folio Docs board, anything touching folio-docs/board/board.yaml or folio-docs/board/cards/*.md, moving a Docs card, appending a trail line, or attaching an artifact.
---

# SKILL: Operate the Folio Docs board

This directory is a **cardfile board**: `board.yaml` defines the columns,
and every file in `cards/` is one card. Git is the only backend: you
change the board by editing files and committing. Any agent (Claude Code,
Hermes, OpenClaw, a human with an editor) follows the same protocol.

## Read the board

- Whole board: `folio-agents board` (table with ids) or `folio-agents board check`
  (validation + card count).
- One card: read `cards/<id>.md`. The filename stem IS the card id.
- Machine state lives in the frontmatter; prose lives in the body:
  description first, then optional `## Acceptance criteria` (checkbox
  list), `## Comments` (the conversation: `- YYYY-MM-DD @actor: text`,
  oldest first) and `## Trail` (one line per session, oldest first).

## Card schema

```markdown
---
title: "Human-readable title"        # required
status: backlog                      # required; a column id from board.yaml
priority: high                       # optional: low | normal | high
order: 200                           # optional rank; omit unless ordering matters
tags: [plugins, cli]
assignee: [ana, bo]                  # or one name: `assignee: ana`
size: M                              # S | M | L | XL, the one closed scale
source: folio#feat/x               # where the work lives: branch, repo#branch, URL
type: bug
milestone: "0.4"                    # optional Folio Docs release id
parent: some-epic-card-id            # optional, must exist on this board
blocked_by: [other-card-id]          # optional, ids must exist on this board
created: 2026-07-12
artifacts:                           # what is not a file, plus labels
  - doc: docs/research/analysis.md   # opens when a docs source publishes it
  - file: folio/build.py#L890        # card directory first, then project root
  - pr: 23                           # pull request number
  - api: folio.plugins.kanban        # API symbol (not validated yet)
  - url: https://example.com/spec
    label: External spec             # optional label on any artifact
---

The description: markdown prose before the first `##` heading.

## Acceptance criteria
- [ ] something verifiable
- [x] something already done

## Comments
- 2026-07-12 @actor: comments are conversation, not record

## Trail
- 2026-07-12 @actor (shortsha or PR #n): what happened this session
```

`assignee` takes one name (`assignee: claude`) or a list. `size` may be
written in any case; the board shows it uppercase. A `source` that is a
URL renders as a link on the card dialog; a branch or `repo#branch`
stays text.

A card with a directory does not list its files. Every regular file at
the top level of `board/cards/<id>/` **is** an artifact, derived at
build: `.md`/`.mdx` as `doc`, the rest as `file`, sorted by name.
Dotfiles, `_`-prefixed names, subdirectories and symlinks stay off the
band. The `artifacts:` block remains for what is not a file (`pr:`,
`url:`, `api:`) and for labels: a `doc:`/`file:` line naming a sibling
by its bare name puts its label on the derived entry instead of adding
a second one. Other `doc:`/`file:` targets resolve against the card's
directory first, then the project root.

Board topology mistakes (unknown status, dangling `parent`/`blocked_by`,
a `size` outside S/M/L/XL, a `doc:`/`file:` artifact path that is
absolute or escapes the project) **fail the build**. A path that
resolves to no file only **warns** — a stale path in one card is prose,
not topology — as does a card directory whose card file is gone. Run
`folio-agents board check` before committing; it replays those warnings.

This board contains Folio Docs work only. Folio for Agents has a separate
board, configuration, milestones, and release cycle. Do not bridge the two
with a `track` field. `milestone` names a Folio Docs release.

## The session protocol

**One logical operation = one commit touching `board/`.** Conventional
messages: `board: <id> <from> -> <to>`, `board: add <id>`,
`board: update <id>`, `board: trail <id>`, `board: comment on <id>`,
`board: attach <kind> to <id>`, `board: attach <id> <filename>`.

Prefer the CLI: every command validates and rolls back on error, and
`--commit` makes the commit for you.

```bash
folio-agents board add "Fix the flaky test" --status backlog --tags ci --commit
folio-agents board move fix-the-flaky-test in-progress --commit
folio-agents board trail fix-the-flaky-test --note "root cause found" --ref abc1234 --commit
folio-agents board comment fix-the-flaky-test "the retry masks the race" --by claude --commit
folio-agents board attach fix-the-flaky-test --doc docs/research/flaky-analysis.md --commit
folio-agents board update fix-the-flaky-test --set assignee=claude --commit
folio-agents board move fix-the-flaky-test in-review --commit
```

Without the CLI, every operation is a one-line file edit:

- **Move a card**: change the `status` line in `cards/<id>.md`.

  ```diff
  - status: backlog
  + status: in-progress
  ```

  That is the whole move: a one-line diff.

- **Log a session**: append `- YYYY-MM-DD @you (ref): note` as the LAST
  line of the `## Trail` section (create the section at the end of the
  file if missing). Never insert at the top.

  ```markdown
  - 2026-08-24 @claude (abc1234): loader landed; moved to in-progress
  ```

- **Comment**: append `- YYYY-MM-DD @you: text` as the LAST line of the
  `## Comments` section (create it BEFORE `## Trail` if missing). The
  conversation reads before the record.
- **Attach an artifact**: add one `  - kind: target` line at the end of
  the `artifacts:` block. A file in the card's own directory needs no
  line at all — it is already derived; a line naming it by its bare
  name only adds a label.
- **New card**: copy `cards/_TEMPLATE.md` to `cards/<new-slug>.md` and
  fill it in. The filename must be a lowercase slug; it is permanent.
- **Give a card a directory**: `folio-agents board attach <id> <path>` copies
  a file into `board/cards/<id>/`, creating the directory the first
  time (`--move` moves it; by hand, `mkdir` and copy). The card stays
  `cards/<id>.md`; the directory is published, and its top-level files
  are the card's artifacts, so what goes in it opens on the board.

At the start of a work session on a card: move it to `in-progress` in
the same commit that opens the branch or session, so the served board
shows work that is actually underway.

At the end of a work session that touched project code: append a trail
line to every card you worked on (with the commit sha or PR number),
move cards whose state changed, attach what you produced, and check.

```bash
folio-agents board trail my-card --note "loader landed" --ref abc1234 --commit
folio-agents board move my-card in-review --commit
folio-agents board attach my-card /tmp/loader-analysis.md --label "Loader analysis" --commit
folio-agents board check
```

Work outputs (research, analysis, comparisons, prototypes) go in the
card's own directory, `board/cards/<id>/`. The files at its top level
are the card's artifacts, derived at build: Markdown and MDX compile
as Folio pages, other files publish as a raw bundle, and each one opens
on the served board. A file produced elsewhere gets in with the attach
command; the flag form is for labels and for what is not a file:

```bash
folio-agents board attach <id> /tmp/prototype.html --move --label "Tree table"
folio-agents board attach <id> --file prototype.html --label "Tree table"
```

An artifact anywhere else in the project is printed as a path; it opens
only when a docs source publishes that page. Supporting material (a
prototype's stylesheet, its data) goes in a subdirectory — still
published, never listed. Scratch that nobody will read again, such as
screenshots from a verification run or throwaway scripts, goes outside
the board or in a dot-directory (`.verify/`), which the build leaves
behind. An artifact is something worth keeping.

## Two-stage artifact work

Always run artifact generation in exactly two compact stages:

1. **Review**: create standalone candidates in one owning card's directory
   and present their links. Do not change product files.
2. **Integrate**: only after explicit owner confirmation, apply the selected
   direction to Folio and validate it.

Keep working context to the objective, confirmed decisions, open choice,
canonical artifact links, and validation state. Do not carry generation
transcripts, rejected detail, or repeated file contents between stages.

## Condense artifact context

The skill maintenance directive is:

```text
condense artifacts <card-id>
```

This is an agent directive, not a shell command or Folio CLI surface. It
replaces verbose artifact-related working context with one compact checkpoint:
the objective, confirmed decisions, open choice, canonical artifact links, and
validation state.

The scope is exactly one permanent card id. Read only `cards/<id>.md` and
`cards/<id>/`. Reject `all`, `.`, paths, globs, multiple ids, a missing card,
or any request to widen the scope. The directive never edits, moves, or deletes
files. If the checkpoint reveals a needed durable change, propose that as a
separate operation and wait for explicit confirmation.

## Say where it lives

Every operation ends with a report the human can click. Never announce
an outcome without linking its artifact:

Before the handoff, open or request every rendered artifact URL and verify it
responds successfully. A repository path or local filesystem path alone does
not satisfy this report.

- **The card file** — `board/cards/<id>.md` is the permanent home of
  the plan; link it every time you create or change a card.
- **The served board** — the card is visible at `/kanban/` on the
  built site; deep-link `/kanban/?q=<filter>` to narrow it to what you
  are reporting on. The filter is one expression: a space is and, a
  comma is or, a minus excludes, quotes are exact, and `none`/`any` ask
  whether a field is set. Most field names are the card's frontmatter
  keys; `tag`, `artifact`, `id` match those lists/the filename; `status`
  is the column. So
  `/kanban/?q=status:in-review tag:spec` is a link to exactly the cards
  you just described. `?milestone=<v>` still works on its own.
- **Every artifact in the card's directory** — Markdown opens at
  `<docs route>/kanban/<id>/<stem>/`; raw files open at
  `/_folio/kanban/<id>/<file>`. Link the rendered output, not just the
  repo path.

"Card created" is an incomplete report. The contract is:
"Card created: `board/cards/<id>.md` — on the board at `/kanban/`."

The same section on the site:
https://pguijas.github.io/folio/docs/kanban/agents/#say-where-it-lives

## Rules, and why they hold

| Rule | Why it holds |
| --- | --- |
| Never edit `agents.yaml` | It is the control plane; only `init` (setup, not session work) ever writes it, and write commands read it only to resolve `board.source` |
| `board.yaml` is human-owned | Column changes are topology; a human asked for them or they don't happen |
| Never rewrite other cards' files in your commit | One card, one file is what makes conflicts structurally impossible |
| Omit `order` unless placement was requested | Ordering is computed; ranks are the exception, never bulk-renumbered |
| Appends go at the section end | Tail appends make concurrent-session conflicts mechanically resolvable |

`folio-agents board move X <col> --after Y` computes a rank for you when a
specific placement really was requested. How the CLI edits files without
destroying your formatting is covered in
`docs/guide/kanban/cli.md`; why prose warns and topology fails,
in `docs/guide/kanban/formats.md`.

The browser never writes card files; it captures intent. A drag stays in
the browser until you export it as a list of `folio-agents board move`
commands, so every mutation still funnels through the validating CLI and
ordinary git review.

## Merge conflicts (rare by design, resolve mechanically)

Two sessions editing DIFFERENT cards can never conflict: one card, one
file. Only two shapes exist.

Both sides moved the same card:

```
ours:
status: in-progress
theirs:
status: in-review
```

Resolution: read both sessions' trail lines and keep the column that
reflects reality after both, `in-review` here if the other session's
trail line records the work landing. Keep both trail lines.

The second shape is both sides appending a trail line to the same card.
Keep both lines, ordered by date.

Never use a union merge driver; a silent both-sides merge of a `status`
edit corrupts the frontmatter.
