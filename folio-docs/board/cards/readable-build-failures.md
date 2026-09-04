---
title: Readable build failures
status: backlog
created: '2026-07-16'
tags: [dx]
milestone: "0.3"
---

Every build failure caused by user input should name the file or config key at fault and state the fix. Raw stack traces are reserved for genuine internal errors; a typo in docs.yaml or a bad frontmatter field must never surface as a traceback.

## Acceptance criteria
- [ ] user-error failures name the file or config key and the fix
- [ ] no raw stack traces for user errors
- [ ] internal errors remain distinguishable from user errors

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
