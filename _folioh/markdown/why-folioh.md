# Why Folioh

*The questions that decide whether Folioh is for you — answered honestly.*

**Why Folioh exists**

  Documentation rots because it lives apart from the code. Folioh generates your docs
  from your source — the reference rebuilds from the current code, and the site it ships in
  is one you're proud to put your project's name on.

That's the whole pitch: you keep writing docstrings and markdown, Folioh turns them into a modern site with a generated API reference, instant search, and theming down to the last token. One command against your codebase produces:

## Folioh against the field

And the capabilities the standard matrix doesn't capture:

The last row is the honest one: Sphinx's extension depth is real, and if your docs depend on exotic extensions, evaluate Folioh on a branch first. Folioh's structural differentiator is one source model feeding both the human site and the machine artifacts.

## Choosing a docs tool

### Why Folioh instead of Sphinx or MkDocs Material?

    Same job — parse Python source into reference docs — with a different output ceiling: a modern Next.js/shadcn site, instant search, theming to full template ownership, and agent-readable artifacts, from one `docs.yaml`. The trade: Sphinx's extension ecosystem is twenty years deep, and Folioh's static analysis doesn't cover everything (see the SWOT below — we put it in writing).

### Why not Docusaurus, Nextra, or Fumadocs?

    Excellent site frameworks for hand-written pages. Python API reference needs a separate integration; Folioh reads it from source and supplies the site as one workflow (built on Nextra internally).

### Why not Mintlify or GitBook?

    Hosted products, per-seat pricing, and they ingest prose, not source. Folioh is a build tool: static output you deploy anywhere (GitHub Pages workflow included), no vendor in the serving path, and the reference is generated from code rather than scraped from markdown you maintain by hand.

### I'm migrating from Sphinx. What doesn't convert?

    Being honest: Folioh's parser is static AST analysis, and it never imports your package. Inherited members and runtime-generated APIs are not covered. Intersphinx, Sphinx cross-links, and a migration run by your agent: Not available in this release. The roadmap puts the migration in 0.4 Agent Ready: your agent moves the site with a migration skill and a few scripts. [Migrating from Sphinx](/docs/migration) walks the manual move.

## Why not just have an LLM emit the HTML?

Because docs have exactly one non-negotiable property — being *true* — and that's a provenance problem, not a fluency problem. Six concrete reasons, each one structural:

### 1 · Ground truth beats plausible text

    An LLM writing HTML documents what it *believes* your API is. Folioh reads signatures, types, and defaults from the source AST instead of asking a model to invent them. Static analysis has limits, but provenance stays inspectable.

### 2 · A snapshot vs a function

    Emitted HTML rots on the first commit that changes your code. Folioh is `f(source, markdown) → site`: re-run on every push, the reference updates itself, and every internal link is checked, with the broken ones named in the build output. Regenerating HTML re-rolls the hallucination dice on content that didn't change — and bills you tokens for markup boilerplate.

### 3 · Reviewable diffs are the safety rail

    When an agent updates the docs here, the diff is a few lines of Markdown or one key in `docs.yaml`, and a human reviews it in seconds. If agents regenerated HTML, the diff would be megabytes of unreviewable markup. Small semantic sources of truth are the only real safety rail in human–agent collaboration.

### 4 · A site needs a linker

    A whole site needs shared navigation, one search index, cross-references that resolve, social cards. LLMs emit locally plausible pages that don't cohere globally; Folioh provides the global invariants: xref resolution, a link checker that names every broken internal link, generated sidebars.

### 5 · Constrained generation appreciates over time

    In raw HTML every div soup is "valid" — infinite ways to be wrong. Writing Folioh markdown, an agent picks from a typed component vocabulary and the build rejects what doesn't exist. And the same markdown renders *better over time* as the template improves: HTML artifacts depreciate, Folioh artifacts appreciate.

### 6 · The next reader is an agent

    Emitted HTML is the worst format for other agents — it forces lossy scraping. Folioh keeps the semantic source as the artifact and emits every output from one pass: HTML for people, markdown mirrors and machine-readable output for agents.

**That question, compressed**

  LLMs write better assembly every month — that's exactly why you want a build step
  you can trust. Markdown plus typed components is the high-level language; Folioh
  does the generating, the linking, and the checking.

## The honest SWOT

## Practical

### Do I need to know React or Next.js?

    No. You write markdown and a `docs.yaml`. Components are tags in markdown (`<Callout>`, `<Swot>`, `<Roadmap>`...) with documented props. React only becomes relevant if you opt into deep customization.

### Why does Folioh need Node?

    Folioh itself is one native binary, but the output is a Next.js static site — that's where search, theming, and interactivity come from. Folioh manages the frontend workspace (`.build/` is disposable) and checks your toolchain up front, but Node ≥ 20.19 and pnpm must exist on the build machine. The *deployed* site needs neither.

### Other languages? Versioned docs? i18n?

    Python, JavaScript and Rust read today; [Languages](/docs/languages) covers each reader. TypeScript is on the roadmap for 0.5 Every Language, and Go, C#, and Java follow it there. Versioned docs and i18n: Not available in this release; the roadmap places them in 0.5.

A question this page doesn't answer? [Open an issue](https://github.com/pguijas/folioh/issues) — unanswered questions are documentation bugs.
