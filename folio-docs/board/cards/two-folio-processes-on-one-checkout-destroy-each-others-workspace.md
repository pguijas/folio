---
title: Two folio processes on one checkout destroy each other's workspace
status: backlog
tags: [core, dx]
type: bug
created: '2026-08-27'
---

`.build/` is one shared mutable directory per checkout, and nothing guards
it. A `folio build` or a second `folio serve` rewrites it under a live
`next dev`: the running server watches `app/` vanish and throws an ENOENT
unhandledRejection storm (`scandir .build/app`), wedges, or respawns
serving a half-written tree that looks like phantom 500s. Seen repeatedly
on 2026-08-27: parallel agent serves colliding on ports 4180/4190/4321,
and the owner's own serve broken by every build the session ran — "asi
todo el rato que haces un cambio".

The shape of the fix is occupancy, not cleverness: a process that wants
the workspace either takes it or names who holds it.

## Acceptance criteria
- [ ] A build refuses (or isolates its workspace) while a serve holds `.build`, naming the holder's pid and port instead of wrecking it
- [ ] A second serve on the same checkout refuses, naming the live serve's port
- [ ] A crashed holder's stale claim never blocks forever — staleness is detected and cleared with a message
- [ ] A test runs a fake holder and asserts both refusals and the stale-claim recovery

## Trail
- 2026-08-27 @claude: carded from the owner's ENOENT report — every build this session ran broke the owner's live serve; root cause is the unguarded shared workspace
