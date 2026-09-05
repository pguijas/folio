# Panel verdict — the board takes the name and absorbs the roadmap

Five agents, 2026-08-28: one merge assessor, three name generators
(plain-literal, market, prior-art lenses), one adversary with kill
authority. The owner confirmed the verdict the same day: `folio board`,
roadmap included.

## Question one: does the roadmap plugin fold into the board plugin?

Four options were weighed. The decisive facts came from the code, not
from taste:

- The two plugins already cannot render their own pages without peeking
  at each other's raw config in three places (`kanban.py:174` reads
  `roadmap:`, `roadmap.py` reads `config.extra['kanban']`, `kanban.py`
  reads `config.extra['roadmap']` back).
- Phases are the only board-adjacent data with no git history, on a
  product that sells on git history.
- Phase 0.4's shipped public text says "the roadmap reads from the
  board". Under the current dependency direction (the board reads FROM
  the roadmap) that sentence is unshippable without either this merge or
  a two-sources-of-truth sync mechanism of the kind this project just
  spent a milestone eliminating for cards.

**Rejected — status quo:** defers a decision the 0.4 text already made
in public, and the cheap-breakage window (pre-beta) is exactly the
window that closes. Renaming around a boundary you intend to erase pays
the ~1350-mention rename cost twice.

**Rejected — one data model, two plugins:** takes the full migration
cost of the merge while keeping the coordination cost of the seam; the
"independent" renderer would have a hard load-order dependency on the
board plugin anyway. Acceptable only as a one-commit intermediate step.

**Chosen — merge with preserved surfaces:**

1. Milestones/phases move out of `docs.yaml` into board data as a
   first-class registry; a phase moving next → active is a commit, same
   as a card move.
2. `/roadmap` stays, as a view of that registry, with its own routes
   toggle independent of the board's visibility — the landing's public
   roadmap can outlive a private board.
3. `folio roadmap` survives as a top-level command, printing the same
   registry `folio board check` validates.
4. A milestone registry with zero cards is legal: the timeline-without-
   a-board user never has to adopt the full board.

**Strongest counterargument, recorded:** the roadmap is a calm public
surface (239 lines that essentially cannot fail) and the board is a
volatile operational one mid-rewrite; merging chains the calm surface to
the volatile one. Conditions 2 and 4 above are the answer, and they are
not optional.

## Question two: what is the name?

25 candidates from three lenses. Killed with cause: `project` (collides
with the `project:` site-metadata key on line 1 of docs.yaml), `work`
(collides with the workspace view; ungreppable), `backlog` (names the
whole with one of its columns), `tickets`, `cardfile`, `cards`
(overloads the vocabulary's cleanest term).

Top survivors, ranked: **board**, tracker, tasks, agenda, docket.

**The bet: `board`.** It is unification, not invention — the data
directory is already `board/`, the config already says `source: board`,
the commit log already says "board:", the landing says "Release board",
and 0.4 says "the roadmap reads from the board" verbatim. Plugin name,
config key, CLI word, route, directory, and roadmap promise collapse
into one word already in use. "The board's kanban view" and "the board's
roadmap view" read as natural English; kanban demotes to the name of the
column view. `board` emerged independently from all three lenses, each
placing "Project OS" (the 0.4 phase title) above it as the family
umbrella.

Runner-up for the record: `tracker` — the only candidate that names the
function ("a file-based project tracker your agents operate through
commits"), held back by bug-tracker heritage and the telemetry smell of
a public `/tracker` route.

## The honesty rule, applied to the name

The owner asked for a name that says organization and agent
orchestration. The panel's ruling: the product today does not
orchestrate agents — agents operate the board through the CLI and
SKILL.md; folio does not schedule or supervise them (that is the
`agents-claim-and-orchestrate` idea, unshipped). A name promising
orchestration would violate the project's own docs-honesty rule for as
long as that stays true. The orchestration story rides in the sentence,
not the noun: *the board — files your agents operate through ordinary
commits*. When orchestration ships, `board` absorbs it without a second
rename.

## Sequencing

Merge and rename happen in the same pre-beta breaking window: the rename
touches every one of the ~1350 "kanban" mentions anyway, and the merge
is what makes the promoted name true. Both known consumers (folio,
pguijas/kanban) migrate trivially today; the same breakage costs an
order of magnitude more at 0.7. The open sequencing question — before or
after the write path's Part One lands — is recorded on the
implementation card, not decided here.
