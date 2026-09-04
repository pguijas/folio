---
title: Preflight environment checks
status: backlog
created: '2026-07-16'
tags: [dx]
milestone: "0.3"
---

Check node, npm, network access, and paths before starting a build, and fail with instructions rather than tracebacks. A missing or wrong-version dependency should produce a message that names the problem and the fix, not a raw stack trace from deep inside the build.

## Acceptance criteria
- [ ] node, npm, network, and path checks run before the build starts
- [ ] each failed check prints what is wrong and how to fix it
- [ ] no traceback shown for a failed preflight check

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
