# Panel verdict: the write path lives in `folio serve`

Three architectures were designed independently and attacked by four
adversarial judges (simplicity, data integrity, security and deployment,
product doctrine). Every repository claim the designs made was verified
against the code before judging. This document is the durable record of
what was considered, what won, and what the winner must do differently.

## The three candidates

**serve-integrated.** A stdlib HTTP thread inside the `folio serve` process.
The web UI posts small operations; each one runs through the same
`kanban_edit` surgery and the same one-operation-one-commit discipline the
CLI already has; the existing watcher turns the file change into a refreshed
board in every open tab. Zero new dependencies, zero new processes. The
published static export stays byte-identical.

**standalone-sidecar.** One separate stdlib process that serves the built
`_site` and mounts the same write API, deployable on any small machine. The
board probes for the API on its own origin and stays read-only when nothing
answers.

**forge-mediated.** No server at all: the browser writes through the GitHub
Contents API with a fine-grained token, reproducing the CLI's commits with
GitHub's compare-and-swap on the file sha as the concurrency guard.

## Verdict

All four judges ranked **serve-integrated** first (8, 8, 8, 8.5 out of 10)
and none found a fatal flaw in it. The deciding fact: the backend already
exists as tested pieces — `kanban_edit.py` writes cards with re-parse
verification, `kanban_cli.py` holds the operations and the commit
discipline, and the serve watcher already turns any card-file change into a
refreshed board in about four seconds. The design adds only the missing HTTP
surface, inside the process the owner already runs.

The sidecar died on state: its server-side board cache could diverge from
the files for every non-web writer, and a compare-and-swap against a stale
cache blesses exactly the clobber it exists to prevent. The forge path died
on duplication and custody: a second surgery implementation in TypeScript
policed by corpus infrastructure, a vendor credential in the write path, and
no improvement at all to the local flow where the board actually gets used.

Two ideas from the losers were adopted: commit-per-write as the default (the
forge design was the only one that got this right), and the sidecar's
capability handshake plus expectation guards — every mutating operation
carries what it believes the current state is, and a mismatch is a refusal,
never a wrong write.

## Mandated changes to the winning design

1. Commit-per-operation defaults to on. Uncommitted web edits erode "git is
   the database" at its most casual surface.
2. Server-originated commits use a pathspec narrowed to the touched card
   file. The CLI's current whole-directory `git add` would silently sweep
   unrelated hand edits into a web gesture's commit.
3. `next dev` binds to 127.0.0.1. It listens on all interfaces today, which
   is a pre-existing exposure the write API would inherit.
4. The discovery file (`serve.json`) is deleted and rewritten at every serve
   start and is already deleted on static export; a killed process must not
   leave a stale token behind.
5. No new hookspec for API routes while exactly one plugin wants them; the
   dev server calls the kanban plugin directly.
6. A non-writing tab re-seeds its board state when the baked data module
   changes, so every tab converges after the watcher echo.
7. The write envelope gets adversarial tests (form-encoded posts that skip
   preflight, absent Origin, rebound Host values), and `kanban_edit`'s
   verified write becomes atomic (temp file and rename), which also protects
   the CLI against torn writes.

Accepted limitation: the millisecond race between an editor save and a
server write stays unguarded. With commit-per-operation on, a clobber is a
visible commit; a cross-process lockfile is real complexity for a race no
judge could construct outside a thought experiment.

## Owner delta, 2026-08-26

The published tier is not deferred indefinitely. The owner's direction: a
deployed board (GitHub Pages) must be able to name a sync backend in the
board's own configuration — a `sync:` key in `docs.yaml` — and write through
it. That is the decision card's path 3, and it is the same server component
grown a front door: `folio kanban server` running on a checkout, receiving
the same operations, committing and pushing, and serving fresh board data
back so the board is live even while the static host waits for its rebuild.
The two implementation cards carry the plans:

- `folio-serve-accepts-board-edits` — the local write path, first.
- `a-published-board-syncs-through-a-configured-backend` — the deployed
  tier, on top of the same operations module.

## Owner delta, second round (2026-08-27)

The deployed tier gains a same-origin mount. When `sync.url` is a path
(`/api/kanban`), the backend is the static host's own function runtime —
Vercel's Python functions beside the exported site — and git happens
through the forge's Contents API with the file sha as compare-and-swap.
The real `kanban_edit` surgery runs inside the function, which recovers
the one virtue of the rejected forge design without either of its fatal
flaws: no credential in the browser bundle, no second surgery
implementation. Credentials are personal, by owner directive: either the
deployer's fine-grained token in the deployment's own configuration, or
each visitor's own credential passed through per request and never
stored, with the repository's permissions as the access control. The
security invariants were designed before the code — they are a numbered
section of the sync card's plan.
