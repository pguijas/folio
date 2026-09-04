---
title: TypeScript technical plan
status: backlog
created: '2026-07-16'
milestone: "0.4"
tags: [spec, languages]
type: plan
---

Technical plan for TypeScript, the first language of the More Languages phase. The roadmap promises that new languages arrive as parsers, not new toolchains; this card holds the engineering work behind that promise, extending the IR contract with language-aware fields, wiring a pinned typedoc extractor into the same pipeline the Python path uses, and keeping the feature gated until the contract has survived real public exposure.

## Acceptance criteria
- [ ] typedoc --json extractor (pinned, versioned contract)
- [ ] ModuleIR.language / ClassIR.kind fields
- [ ] per-language cross-references + route namespacing
- [ ] cross-language llms.txt / ir.json
- [ ] Twoslash inline type info
- [ ] golden-fixture TypeScript test suite
- [ ] gated experimental until the IR contract survives public exposure

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
