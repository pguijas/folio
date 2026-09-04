---
title: Rust fast path for source reading
status: ideas
tags: [dx, core]
created: '2026-07-27'
milestone: "0.4"
---

Move the hot parsing passes to a native implementation for a large build-time speedup. Before any of it is written, the premise needs a measurement, because on this repository it does not hold: a full parse of Folio's own 45 modules takes 0.105s, while a cold `folio serve` takes about four minutes to reach a served page. The template phase accounts for nearly all of that, so a native parser would save a tenth of a second.

The idea stays open because the premise may hold on inputs Folio has not been pointed at yet: a repository with thousands of modules, or the Markdown and MDX passes, or the link resolution and search index passes. Profile a large repository first and publish per-phase numbers. Build native code only for a phase the numbers convict.

## Acceptance criteria
- [ ] per-phase build timings published for a large repository, not just this one
- [ ] the dominant phase named with a number behind it
- [ ] a recorded decision on which phase, if any, justifies a native implementation
- [ ] if none does, the card closes and the numbers are the reason

## Trail
- 2026-07-27 @claude: carded on request. Measured `parse_python_directory` at 0.105s for 45 modules against a roughly four-minute cold serve, so the current bottleneck is the template phase rather than source reading.
- 2026-08-27 @claude: moved backlog -> ideas in the reorganization: the card's own trail shows the premise fails on this repository; it is a profile-first exploration that closes on numbers, not shaped build work. Milestone 0.5 kept — the roadmap names the fast path there.
- 2026-08-29 @codex: Release 0.3 validation: clean build took 491.6s and incremental serve preparation 260.5s under concurrent load; profile parser, generation, preview, rewrite, and frontend phases separately before assigning work to Rust.
