---
title: Project OS technical plan
status: ideas
created: '2026-07-16'
milestone: "0.2"
tags: [spec]
type: plan
---

The write path for agents plus board maturity: agents move from reading the site to acting on it through a write-MCP and a generated authoring contract, while the board grows the metadata, views, and generated-roadmap machinery it needs to serve as the project's operating layer. The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.

## Acceptance criteria
- [ ] write-MCP for boards (move_card / update_phase via PR)
- [ ] Folio skill for Claude Code / Hermes / OpenClaw
- [ ] generated authoring contract per project
- [ ] card pages
- [ ] session artifacts render as site pages, attached to the card they moved, in search and llms.txt
- [ ] board drag and drop persists as a commit to the board's branch
- [ ] board webhooks / CI sync (issues to cards and back)
- [ ] metadata + filtering contract (unknown references fail the build, unknown values warn)
- [ ] saved views
- [ ] roadmap generated from the cards
- [ ] folio artifact single-page mode
- [ ] ADR plugin
- [ ] reusable snippets with variables
- [ ] automation recipes running the user's own agent in CI
- [ ] edit-this-page + file-an-issue links
- [ ] agents report doc issues through the MCP

## Comments
- 2026-08-25 @claude: Panel verdict on the skill criterion: not installable, scaffolded. init writes the generic protocol into .claude/skills/kanban-board/SKILL.md and .agents/skills/kanban-board/SKILL.md as identical bytes from one template; board/SKILL.md keeps this board's facts (columns, source convention, site URL). Follow-ups on the same item: folio kanban skill prints the release-matched protocol, check warns when a scaffold's version stamp disagrees with the running folio, the init stub names the board branch and links the docs site. Open: two-directory write as default or opt-in.
- 2026-08-27 @claude: Progress on this branch against the list, none tick-complete: artifacts render as compiled site pages attached to their card (b7fe40a2c) but the search/llms.txt clause is unverified; card-directory documents get routes but there is no page per card yet; drag-and-drop-as-commit now lives in folio-serve-accepts-board-edits; the skill item carries the 2026-08-25 panel verdict (scaffolded, not installable). Tick items only from evidence, one by one.

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
