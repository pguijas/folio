---
title: OpenAPI plugin on the current extension API
status: ideas
created: '2026-07-16'
milestone: "0.6"
tags: [spec, plugins, openapi]
type: feature
source: folio#18
---

Turn an OpenAPI document into endpoint pages and agent-readable Markdown
without executing the documented service. The plugin should enter through the
current extension registry, reuse Folio's normal routes and link validation,
and stay opt-in.

PR #18 proved the direction on an older plugin surface. Its 42-file
implementation is deleted because adapting it costs more than rebuilding the
smallest useful slice against the current API.

## Acceptance criteria
- [ ] OpenAPI input produces one stable page per operation without importing the service
- [ ] Generated pages participate in search, sitemap, Markdown mirrors, and `llms.txt`
- [ ] Components and config are registered through the current public plugin contract
- [ ] Invalid documents and route collisions fail before writes
- [ ] A small FastAPI fixture proves examples, schemas, links, and clean rebuilds
- [ ] The implementation starts from current main rather than copying PR #18

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round.
- 2026-08-29 @codex (PR #18): old implementation and branch deleted; OpenAPI remains a clean-slate product idea.
