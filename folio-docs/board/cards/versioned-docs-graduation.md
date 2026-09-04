---
title: Versioned docs graduation
status: ideas
created: '2026-07-16'
milestone: "0.4"
tags: [release]
---

The versions: config references tags v0.2.0, v0.1.0, and v0.0.1 that do not exist in git, so versioned builds rest on references that cannot resolve. Create the real tags and graduate versioned builds out of experimental once they build against tags that actually exist.

## Acceptance criteria
- [ ] git tags exist for every version referenced in versions: config
- [ ] versioned builds resolve against real tags
- [ ] versioned docs graduated out of experimental

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
