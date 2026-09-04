---
title: Hidden pages and ignore rules
status: backlog
created: '2026-07-16'
milestone: "0.3"
tags: [core]
---

Two levels of page visibility: a hidden: frontmatter flag that keeps a page out of nav and search while leaving it reachable by URL, and an ignore file that excludes content from the build entirely. Visibility is decided at build time, never client-side, so hidden content is not merely styled away.

## Acceptance criteria
- [ ] hidden: frontmatter removes a page from nav and search but keeps it reachable by URL
- [ ] ignore file excludes matched content from the build entirely
- [ ] visibility decided at build time, never client-side

## Comments
- 2026-08-27 @claude: Milestone 0.4 dates from the 2026-07-16 de-teching round; no 0.4 roadmap feature names page visibility, so reconfirm the phase when the milestone registry tightens — kept for now rather than guessed elsewhere.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
