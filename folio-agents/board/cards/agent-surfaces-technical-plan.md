---
title: Agent surfaces technical plan
status: ideas
created: '2026-07-16'
milestone: "0.2"
tags: [spec]
type: plan
---

The read path for agents, in three layers: formats (Markdown mirrors and llms.txt variants that any crawler or agent can consume), typed export (a versioned intermediate representation that tools can build on), and live surface (MCP and skills served from the static artifacts). The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.

## Acceptance criteria
- [ ] spec-correct llms.txt / lossless llms-full.txt
- [ ] lossless per-page .md mirrors (today's mirrors strip component tags)
- [ ] frontmatter descriptions feeding llms.txt
- [ ] Accept: text/markdown content negotiation + rel=alternate links
- [ ] .well-known discovery (skills, MCP card)
- [ ] install.md aggregation
- [ ] contextual menu (copy page as Markdown, open in agent tools) as static config
- [ ] JSON-LD structured data + SEO/GEO meta controls
- [ ] Content-Signal directives in robots.txt
- [ ] folio-ir.json versioned language-aware schema
- [ ] per-version IR sidecars
- [ ] process_ir / emit_llm hookspecs
- [ ] folio mcp (stdio, over static artifacts)
- [ ] skill.md at the site root
- [ ] charter plugin serving project contracts (PRODUCT.md, DESIGN.md, AGENTS.md; generic boilerplate excluded from auto-detection)

## Comments
- 2026-08-25 @claude: The .well-known discovery and skill.md-at-the-site-root items are the site half of the skill decision recorded on project-os-technical-plan: the checkout side ships as a scaffolded project skill, the published side serves the same protocol to agents with no clone (today a board-only site publishes no protocol page at all, and the init stub ends without a URL).

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
