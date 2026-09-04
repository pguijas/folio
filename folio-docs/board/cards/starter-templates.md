---
title: Starter templates
status: ideas
created: '2026-07-16'
milestone: "0.3"
tags: [cli, launch]
---

folio init scaffolds a new project from a small set of maintained templates: library, CLI tool, and API service. Each template is kept deliberately small, is maintained alongside the core, and builds green out of the box — a fresh init followed by a build must succeed with no edits.

## Acceptance criteria
- [ ] folio init offers the library, CLI tool, and API service templates
- [ ] Each template builds green immediately after init with no edits
- [ ] Templates are maintained in-repo so core changes that break them fail CI

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-27 @claude: moved to ideas in the board reorganization — milestone 0.7 is two phases out; criteria are sound but nobody can pick this up before the Public Beta phase opens
