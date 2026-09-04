---
title: Links resolve everywhere they render
status: backlog
tags: [bug, core]
created: '2026-08-25'
type: bug
milestone: "0.3"
---

Three link-system defects exist across the repository and build checker. The first: Next's client router resolves raw relative MDX hrefs against the route rather than the file, breaking over 40 links repository-wide when a documentation page includes a relative link like `[text](./sibling.md)`. The second: the checker cannot see hrefs inside JSX props, so `class-overview.md` carries dead links to `/docs/api-reference/base-node` and `/docs/api-reference/serializable` that the checker never reports. The third: `/_folio/` asset links are reported as broken by the checker even when they resolve correctly on the built site, creating 9 false positives today.

These defects share one root cause: links are validated, transformed, and resolved in separate passes without a unified contract. The docs' absolute prototype link and the checker's `/_folio/` blind spot need resolution together.

## Acceptance criteria
- [ ] Relative MDX hrefs resolve correctly on the built site, matching their behavior in the repository
- [ ] The checker validates hrefs inside JSX props and reports dead api-reference links
- [ ] `/_folio/` asset links are validated correctly and stop producing false positives
- [ ] The link system has a unified contract for validation, transformation, and resolution

## Comments
- 2026-08-27 @claude: Live defects on the served site (40+ broken relative links, 9 checker false positives) belong to the current phase; the checker fixes map to 0.4's quality-gates feature.
- 2026-08-27 @pguijas: Update 2026-08-27: the checker's false positives grew from 9 to 30 with the derived-artifacts feature — every generated card index now carries an /_folio/kanban/<id>/<file> tile href, and check_links validates site-absolute targets only against the route registry, which knows nothing of published static assets. Verified pre-existing: a cold build of bbe8fe2a4 (before the docs move) reports the identical 30. The fix is teaching folio/link_checker.py (or the builder's registry) about published asset paths; until then no commit builds link-warning-free.
