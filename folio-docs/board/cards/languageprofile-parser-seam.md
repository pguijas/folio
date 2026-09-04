---
title: LanguageProfile parser seam
status: backlog
created: '2026-07-16'
milestone: "0.4"
tags: [core, languages]
---

Introduce a LanguageProfile abstraction and a parser registry in core, with Python as the only profile for now. The IR carries language identity, and registering a second profile touches only the registry — nothing else in the pipeline changes. The docs state the contract plainly: new languages are parsers, not toolchains.

That contract is the constraint, and it rules out the obvious route for every language after TypeScript. Reading Rust through `rustdoc --output-format json` needs a Rust toolchain, Go through `go/doc` needs Go, Java through `javadoc` needs a JDK — each one turns "add a language" into "install an ecosystem", which is the objection Folio exists to answer for Sphinx-era maintainers. TypeScript is the exception: its compiler is reachable through the Node runtime Folio already requires.

So the profile for everything else reads a grammar, not an SDK. That keeps the same posture Python already has: `ast` reads annotations as written and infers nothing, and a grammar-based profile behaves identically. The cost is honest and should be written down rather than discovered — a grammar gives syntax, not semantics, so a type that is only knowable by inference will not appear. For reference pages built from signatures and doc comments, that is the same trade Python already makes.

## Acceptance criteria
- [ ] LanguageProfile and parser registry exist in core with Python as the only profile
- [ ] IR carries language identity
- [ ] registering a second profile touches only the registry
- [ ] docs state the contract: new languages are parsers, not toolchains
- [ ] the grammar-versus-SDK decision is recorded, with the syntax-not-semantics limit stated

## Trail
- 2026-07-16 @claude: carded in the roadmap de-teching round — technical detail moved off the roadmap.
- 2026-07-29 @claude: roadmap 0.5 now names Rust, Go, then the JVM and C#. Recorded why each one's own doc tooling is off the table under the no-toolchain contract, and that the profile reads a grammar instead.
