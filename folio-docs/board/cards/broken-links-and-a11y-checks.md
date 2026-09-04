---
title: Broken links and a11y checks
status: backlog
created: '2026-07-16'
milestone: "0.3"
tags: [quality]
---

folio check gains internal link and anchor checking, optional external link checking, and an accessibility audit covering image alt text and contrast. The checks are wired in as a build gate so a broken link or a missing alt attribute fails the build instead of shipping.

## Acceptance criteria
- [ ] internal link and anchor checking in folio check
- [ ] optional external link checking
- [ ] image alt and contrast audit
- [ ] checks wired as a build gate
- [ ] docs quality gates GitHub Action (links, coverage, style linting)

## Comments
- 2026-08-27 @claude: Internal link checking shipped (folio/link_checker.py, wired at folio/build.py:979) — remaining scope is anchor checking, optional external links, the alt/contrast audit, and the GitHub Action. The shipped checker's defects (JSX-prop blind spot, /_folio/ false positives, relative-href resolution) live on links-resolve-everywhere-they-render; that bug card is a sibling, not a duplicate.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
