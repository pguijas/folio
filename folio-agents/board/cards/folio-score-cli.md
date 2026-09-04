---
title: Folio score CLI
status: ideas
created: '2026-07-16'
milestone: "0.3"
tags: [launch]
---

An open agent-readiness audit runnable against any docs site, whether given a URL or a local directory. It checks llms.txt presence and spec-correctness, .md mirrors, well-known discovery paths, sitemap, and metadata, and produces an honest score against published criteria — no grading on a curve toward Folio-built sites. Exit codes make it usable in CI. It doubles as the migration hook: score your current site, see what is missing, then migrate.

## Acceptance criteria
- [ ] Runs against both a URL and a local directory
- [ ] Checks llms.txt presence and correctness against the spec
- [ ] Checks .md mirrors, well-known discovery paths, sitemap, and metadata
- [ ] Scoring criteria are published and the score is reproducible from them
- [ ] Non-zero exit code on failing score so it works as a CI gate
- [ ] Works against docs sites not built with Folio

## Comments
- 2026-08-27 @claude: Scores the same surfaces agent-surfaces-technical-plan (0.4) builds — llms.txt, .md mirrors, .well-known — so it naturally sequences after that card lands; not a blocked_by, just ordering.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-27 @claude: reorganization: confirmed 0.7 in PRODUCT.md and the roadmap — top-of-funnel launch tool, not near-term; ideas until the phase opens
