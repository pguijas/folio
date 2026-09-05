# Operating a board

The contract for moving a board without breaking it: the session protocol, and every rule with the reason it holds. This is the page an agent reads before it touches `board/`.

`folio board init` writes `board/SKILL.md` into the project that owns the
board, giving agents an in-repo entry point even when they have not opened the
published docs. Any agent follows the same steps, whether Claude Code, another
framework, or a human with an editor; git is the only backend.

## How an agent finds this

Nothing installs this protocol. An agent arrives at it by one of three paths,
each of them an ordinary file.

- **`board/SKILL.md`, in the checkout.** `folio board init` writes it with a
  skill preamble: a `name`, and a `description` naming when it applies. The
  preamble is the shape skill-reading runtimes recognize, but those runtimes
  scan their own directories, not `board/`, so today an agent reaches this
  file because something points at it: a line in the repository's agent
  instructions, or whoever opened the session. Folio registers the file with
  nothing: it calls no runtime and knows of none.
- **The published guide, when configured.** The optional Folio Docs adapter can
  include these pages and the board in an agent-readable static site.

What `init` scaffolds is a stub, not the contract: how to read the board, four
commands, five rules, and a closing line sending the reader to these pages for
the card schema and the validation rules. It is meant to grow with the project.

The checked-in skill remains canonical even when a site publishes a copy.

## Session lifecycle

1. **Start**: move your card into the working column before the feature work begins.

   ```bash
   folio board move my-card in-progress --commit
   ```

2. **During the session**: ordinary code commits. The board stays untouched.

3. **End of session**:
   - Append one trail line to **every card you touched**, with the commit sha or PR number as the ref.
   - Move cards whose state changed.
   - Commit work outputs (research, analysis, designs) into the card's own directory, `board/cards/<id>/`. The files at its top level **are** the card's artifacts, derived at build: Markdown compiles into site pages, other files publish verbatim, and each one opens on the served board. Attaching by hand is for labels and for what is not a file (`pr:`, `url:`, `api:`); a sibling's target is its bare name. A `doc:` elsewhere opens only when a docs source publishes that page; anything else validated-but-unpublished is shown as its path.
   - Run [`folio board check`](./cli#check) before committing. It is the
     standalone board gate; the optional Docs adapter consumes the same loader.

   ```bash
   folio board trail my-card --note "loader landed" --ref abc1234 --commit
   folio board move my-card done --commit
   folio board attach my-card --doc loader-analysis.md --label "Loader analysis" --commit
   folio board check
   ```

## What a session leaves behind

The card's directory, `board/cards/<id>/`, is the session's workspace, and
because the build publishes it, what a session produced is readable from the
board rather than only from a clone.

- **One file per output.** A brief is a file, a comparison is a file, each
  prototype is a file. One `notes.md` accumulating a whole session is not
  something a later reader opens twice.
- **The top level is the band on the card.** Every file at the directory's
  top level is an artifact, derived — so curation is placement. What a later
  reader would open sits at the top level; supporting material (a prototype's
  stylesheet, its data) goes in a subdirectory, which still publishes but is
  not listed.
- **Scratch stays out.** Screenshots from a verification run, throwaway scripts,
  downloaded fixtures: those go outside the board entirely, or into a
  dot-directory inside the card's own (`.verify/`, `.cache/`), which the build
  leaves behind. A `_`-prefixed file stays in the bundle but off the band and
  out of compilation.

When a decision needs looking at rather than arguing about, keep a brief stating
the problem and the rules, one file per variant, and a comparison that says
what each variant is bad at. Those files publish from the card's directory and
open from the card's page.

The build enforces little here: a `doc:` or `file:` target that resolves to no
file warns at build and `check`, naming the card and the path, and a directory
whose card is missing is reported. Whether the card owns the path decides only
whether the artifact opens. Everything above is convention. No build fails
because a card directory is one long `notes.md`.

## Two-stage artifact work

Artifact generation uses exactly two compact stages:

1. **Review** creates standalone candidates in one owning card's directory and
   presents their links without changing product files.
2. **Integrate** starts only after explicit owner confirmation, applies the
   selected direction to Folio, and validates it.

Between stages, retain only the objective, confirmed decisions, open choice,
canonical artifact links, and validation state. Generation transcripts,
rejected detail, and repeated file contents are not durable project memory.

### Condense artifact context

An agent using the board skill recognizes this maintenance directive:

```text
condense artifacts <card-id>
```

It is not a shell command or Folio CLI surface. It replaces verbose
artifact-related working context with one compact checkpoint containing the
five fields above. The scope is exactly one permanent card id: the agent may
read only `cards/<id>.md` and `cards/<id>/`. It must reject `all`, `.`, paths,
globs, multiple ids, a missing card, or any attempt to widen the operation.

Condensing context never edits, moves, or deletes files. A durable change found
during maintenance is a separate operation and still requires explicit owner
confirmation.

## Say where it lives

Every operation ends with a report the human can click. Never announce an
outcome without linking what it produced.

Before the handoff, open or request every rendered artifact URL and verify it
responds successfully. A repository path or local filesystem path alone is not
an artifact notification.

- **The card file.** `board/cards/<id>.md` is the permanent home of the plan;
  link it every time you create or change a card.
- **The served board.** The card is on `/kanban/`, and `/kanban/?q=<filter>`
  narrows it to what you are reporting on:
  `/kanban/?q=status:in-review tag:spec` is a link to exactly the cards you just
  described. The filter is [one expression](./#filtering),
  and `?milestone=<v>` still works on its own.
- **Every artifact you attached from the card's directory.** Markdown opens at
  `<docs route>/kanban/cards/<id>/<stem>/`; raw files open at
  `/_folio/kanban/<id>/<file>`. Link the rendered page, not the repository path.

"Card created" is an incomplete report. The contract is:
"Card created: `board/cards/<id>.md` — on the board at `/kanban/`."

## One logical operation, one commit

Every board commit touches only `board/` and carries a conventional message. The CLI's `--commit` flag produces these automatically, scoped to the board directory — unrelated staged changes are never swept in. The message for each operation is listed under [`--commit`](./cli#--commit).

## Editing by hand (no CLI required)

The format is plain files; any editor works, under the same rules the CLI enforces:

- **Move a card**: change the `status` line to another column id.

  ```diff
  - status: backlog
  + status: in-progress
  ```

  That is the whole move: a one-line diff.

- **Add a trail line**: append it as the **last** line of the `## Trail` section, never at the top (create the section at the end of the file if missing).

  ```markdown
  - 2026-08-24 @claude (abc1234): loader landed; moved to in-progress
  ```

- **Create a card**: copy `cards/_TEMPLATE.md` to `cards/<slug>.md`. The filename must be a lowercase slug and is permanent — it is the card id.
- **Lists are hand edits by design**: `tags`, `blocked_by`, and removing an artifact or trail line are one-line edits in the file; the CLI does not do them.

## Rules, and why they hold

| Rule | Why it holds |
| --- | --- |
| Never edit `agents.yaml` during a session | It is the Agents control plane; only `init` writes it, and write commands read it only to resolve `board.source` |
| `board.yaml` is human-owned | Column changes are topology; a human asked for them or they don't happen |
| Never rewrite other cards' files in your commit | One card, one file is what makes conflicts structurally impossible |
| Omit `order` unless placement was requested | Ordering is computed; ranks are the exception, never bulk-renumbered |
| Appends go at the section end | Tail appends make concurrent-session conflicts mechanically resolvable |

How the CLI edits files without destroying your formatting is covered in the [Kanban CLI](./cli); why prose warns and topology fails, in [Board formats](./formats#validation).

The browser never writes card files; it captures intent. A drag stays in the browser until you [export it](./#moving-a-card) as a list of `folio board move` commands, so every mutation still funnels through the validating CLI and ordinary git review.

## Merge conflicts

Conflicts are rare by construction: one card is one file and there is no shared index, so two sessions editing different cards can never conflict. Only two shapes exist, both with mechanical resolutions.

Both sides moved the same card:

```
<<<<<<< HEAD
status: in-progress
=======
status: done
>>>>>>> feature/loader
```

Resolution: read both sessions' trail lines and keep the column that reflects reality after both, `done` here if the other session's trail line records the work landing. Keep both trail lines.

The second shape is both sides appending a trail line to the same card. Keep both lines, ordered by date.

Never use a union merge driver: a silent both-sides merge of a `status` edit corrupts the frontmatter.
