---
title: Plugin catalog technical plan
status: ideas
created: '2026-07-16'
tags: [spec]
type: plan
---

Technical plan for the Public Beta catalog work. The roadmap promises a plugin catalog outsiders can publish into; this card holds the engineering work behind that promise, covering the plugin catalog and hookspecs that let outsiders extend the system, the eval tooling that keeps docs honest at scale, and the git sync that connects the board to the rest of a team's infrastructure.

## Acceptance criteria
- [ ] plugin catalog + scaffold + three flagship external plugins
- [ ] register_language hookspec
- [ ] agent-docs eval benchmark (folio eval)
- [ ] git sync
- [ ] i18n plugin for localized sites

## Comments
- 2026-08-27 @claude: The 'git sync' criterion overlaps the decided 0.4 write-path chain (a-published-board-syncs-through-a-configured-backend); when 0.7 opens, rescope that bullet to whatever the 0.4 backend did not cover (issues/CI sync direction lives on project-os-technical-plan).

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-08-27 @claude: reorganization: 0.7 phase plan — ideas until the phase opens
