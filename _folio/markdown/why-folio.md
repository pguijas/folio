# Why Folio

*The questions that decide whether Folio is for you — answered honestly.*

**Why Folio exists**

  Documentation rots because it lives apart from the code. Folio generates your docs
  from your source — the reference rebuilds from the current code, and the site it ships in
  is one you're proud to put your project's name on.

That's the whole pitch: you keep writing docstrings and markdown, Folio turns them into a modern site with a generated API reference, instant search, and theming down to the last token. One command against a Python codebase produces:

## Folio against the field

And the capabilities the standard matrix doesn't capture:

The last row is the honest one: Sphinx's extension depth is real, and if your docs depend on exotic extensions, evaluate Folio on a branch first. Folio's structural differentiator is one source model feeding both the human site and the machine artifacts.

## Choosing a docs tool

### Why Folio instead of Sphinx or MkDocs Material?

    Same job — parse Python source into reference docs — with a different output ceiling: a modern Next.js/shadcn site, instant search, theming to full template ownership, and agent-readable artifacts, from one `docs.yaml`. The trade: Sphinx's extension ecosystem is twenty years deep, and Folio's static analysis doesn't cover everything yet (see the SWOT below — we put it in writing).

### Why not Docusaurus, Nextra, or Fumadocs?

    Excellent site frameworks for hand-written pages. Python API reference needs a separate integration; Folio reads it from source and supplies the site as one workflow (built on Nextra internally).

### Why not Mintlify or GitBook?

    Hosted products, per-seat pricing, and they ingest prose, not source. Folio is a build tool: static output you deploy anywhere (GitHub Pages workflow included), no vendor in the serving path, and the reference is generated from code rather than scraped from markdown you maintain by hand.

### I'm migrating from Sphinx. What doesn't convert yet?

    Being honest: Folio's parser is static AST analysis. Inherited members, intersphinx inventories, and runtime-generated APIs are not covered today — they're tracked on the public roadmap's migration phase alongside a `conf.py`/`mkdocs.yml` importer with a what-didn't-convert report.

## Why not just have an LLM emit the HTML?

Because docs have exactly one non-negotiable property — being *true* — and that's a provenance problem, not a fluency problem. Six concrete reasons, each one structural:

### 1 · Ground truth beats plausible text

    An LLM writing HTML documents what it *believes* your API is. Folio reads signatures, types, and defaults from the source AST instead of asking a model to invent them. Static analysis has limits, but provenance stays inspectable.

### 2 · A snapshot vs a function

    Emitted HTML rots on the first commit that changes your code. Folio is `f(source, markdown) → site`: re-run on every push, the reference updates itself, and every internal link is checked, with the broken ones named in the build output. Regenerating HTML re-rolls the hallucination dice on content that didn't change — and bills you tokens for markup boilerplate.

### 3 · Reviewable diffs are the safety rail

    When an agent moves a kanban card here, the diff is a one-line `status:` frontmatter edit a human reviews in seconds. If agents regenerated HTML, the diff would be megabytes of unreviewable markup. Small semantic sources of truth are the only real safety rail in human–agent collaboration.

### 4 · A site needs a linker

    A whole site needs shared navigation, one search index, cross-references that resolve, versioning, social cards. LLMs emit locally plausible pages that don't cohere globally; Folio provides the global invariants: xref resolution, a link checker that names every broken internal link, generated sidebars.

### 5 · Constrained generation appreciates over time

    In raw HTML every div soup is "valid" — infinite ways to be wrong. Writing Folio markdown, an agent picks from a typed component vocabulary and the build rejects what doesn't exist. And the same markdown renders *better over time* as the template improves: HTML artifacts depreciate, Folio artifacts appreciate.

### 6 · The next reader is an agent

    Emitted HTML is the worst format for other agents — it forces lossy scraping. Folio keeps the semantic source as the artifact and emits every output from one pass: HTML for people, markdown mirrors and machine-readable output for agents.

**That question, compressed**

  LLMs write better assembly every month — that's exactly why you want a build step
  you can trust. Markdown plus typed components is the high-level language; Folio
  does the generating, the linking, and the checking.

## The honest SWOT

## Practical

### Do I need to know React or Next.js?

    No. You write markdown and a `docs.yaml`. Components are tags in markdown (`<Callout>`, `<Swot>`, `<Roadmap>`...) with documented props. React only becomes relevant if you opt into deep customization.

### Why does a Python tool need Node?

    Because the output is a Next.js static site — that's where search, theming, and interactivity come from. Folio manages the frontend workspace (`.build/` is disposable) and checks your toolchain up front, but Node ≥ 20.19 and pnpm must exist on the build machine. The *deployed* site needs neither.

### If I drag cards on the kanban board, who sees it?

    Folio for Agents owns that workflow. Moves become `folio board move`
    commands and ordinary commits; Folio Docs only renders the board when its
    optional integration is installed.

### Other languages? Versioned docs? i18n?

    Python today; TypeScript, Rust, Go, C#, and Java are a roadmap phase, and the machine-readable IR schema is language-aware from day one. Versioned docs and i18n are implemented behind `FOLIO_EXPERIMENTAL` while they stabilize — graduating versions is part of the active phase.

A question this page doesn't answer? [Open an issue](https://github.com/pguijas/folio/issues) — unanswered questions are documentation bugs.
