# Product

This file is the source of truth for what Folio wants to be — positioning,
voice, and direction. Copy, design, and roadmap decisions should agree with it;
when they can't, change this file first, deliberately.

## North Star

Documentation and agent context start from the same repository truth, but they
are independent products. Their core runtimes, configurations, versions, and
releases remain separate while one extensible `folio` CLI presents the product
family to users.

Everything else a project needs to organize itself follows that rule. The
roadmap, the work board, and the artifacts a working session leaves behind live
in the repo, operable by humans and agents through ordinary commits. No server,
no account, no vendor in the path.

Folio is one family with two products. **Folio Docs** is the docs generator: it
turns source and guides into HTML for people plus Markdown and indexes for
agents. **Folio for Agents** is the meta-harness, a harness over harnesses: it
gives the coding tools already in use one shared board, one set of repository
rules, and durable artifacts. It does not replace or orchestrate those
harnesses. `folio-docs` and `folio-agents` are separate distributions with
separate release cycles. Folio Docs owns the `folio` CLI host and installed
products contribute command groups through entry points; Folio for Agents adds
`folio board`. Publishing an Agents board in a Docs site remains an explicit,
optional build integration.

## Users

Maintainers, library authors, internal platform teams, and developer-tooling
teams who want a polished documentation site that stays close to source,
config, tests, and release automation. Python maintainers are the first
audience; the product is not Python-only and must never read as if it were.

Agents are first-class readers of Folio Docs: with LLM output enabled, the docs build emits
`llms.txt` and `llms-full.txt` beside the human site. The direction of travel
(agent surfaces, the artifact board) treats agents as operators, not an
afterthought.

Primary visitor contexts:

- A maintainer evaluating whether Folio can replace Sphinx or MkDocs.
- A contributor opening the generated docs to understand the project.
- A developer reading API reference, guides, or migration notes.
- An agent consuming `llms.txt` or operating the project's board.

## Positioning & Voice

Approved hero copy (August 30 2026 round; change only through a deliberate
copy round):

- No kicker. The hero opens directly on the product promise.
- Headline: `HTML for people, Markdown for agents.`
- Description: `With one docs.yaml, Folio builds a complete documentation
  site from the Python source and guides already in your repository.`
  This string doubles as the llms.txt summary blockquote, so it must
  stand alone outside the page.

Page-level copy rules from the July 2026 round: no meta-copy (never describe
the page or count its cards); each product claim is argued in exactly one
owning section and at most mentioned elsewhere; section links point at live
artifacts (the generated reference, Folio's dedicated `board` branch) over
generic routes.

Register: affirmative and outcome-led — sell what the user gets and what it
enables (the discourse family of "knowledge infrastructure", "self-updating
made honest"). Execution stays dry, editorial, engineering-native.

Vocabulary rules:

- No compiler jargon in user-facing positioning ("compiler", "compile",
  "compiled" are banned by owner directive). **Docs generator** is the category
  for Folio Docs. **Meta-harness**, glossed once as "a harness over harnesses",
  is the category for Folio for Agents. Mechanism language is
  *reads / generates / builds*.
- No hype words, no exclamation marks, no emoji.
- No insider industry jargon in user-facing copy: "dogfood" in any form is
  banned (owner directive). Say what it literally means — "this site runs
  on it", "built with Folio, on Folio", "rendered from this repository".
  The concept stays; the jargon doesn't.
- Competitor attack ladders are retired. Competitors are named only in
  explicit comparison contexts (the docs comparison table), never in the hero.

Honesty rules (non-negotiable):

- Present tense only for shipped facts. `llms.txt` is shipped; `folio mcp`,
  `ir.json`, and multi-language are roadmap — say so.
- The language is scope, not identity: name Python as a bound on what gets
  read ("the Python source"), never as a label in the kicker, and never
  imply "Python only". Multi-language is an architecture claim (new
  parsers, same funnel), not a shipped feature.
- "Current" means current at the last build — never claim live updating.
- No platform, hosting, accounts, analytics, or AI-chat claims: Folio is
  open source and static, with no server and no vendor in the serving path.
- Ghost/dashed visuals mean roadmap-future; never render unshipped work as
  shipped.

## Direction

The roadmap traces direction: where the product is going, and what a user
gets when it arrives. Maintenance, release hygiene, and repair stay out of
it — a release that lags the repository is a bug, and a bug is fixed, not
scheduled as direction. Folio tracks that work as cards in the dedicated
`board` branch, never in a code or release branch.

The products compound independently and keep separate roadmap versions.

### Folio Docs

1. **Agent-readable documentation** — the site is ground truth for people and
   agents. `llms.txt`, per-page Markdown mirrors, and the authoring contract
   ship today; a scorer, typed exports, and richer discovery come next.
2. **More languages** — TypeScript comes first, followed by Rust, Go, C#, and
   Java. New languages arrive as parsers, not new toolchains.
3. **Adoption without rewrites** — existing documentation moves into Folio with
   redirects, preserved cross-links, and an honest conversion report.
4. **Static forever** — output runs anywhere static files do. Access control
   happens at build time, never as client-side password theater over shipped
   data.

### Folio for Agents

1. **Git-native work state** — the cardfile board, operating protocol, and
   artifacts remain in the repository and move through reviewable commits.
2. **Sessions leave conclusions** — useful decisions and outputs attach to the
   work they moved instead of disappearing into a transcript store.
3. **Project coordination** — milestones, dependencies, ownership, issues, and
   CI reconcile into one repository-owned view without replacing the coding
   harnesses already in use.
4. **A network for meta-harnesses** — teams can discover and share portable
   skills and context contracts while each repository retains its state and
   permissions.

## Market

Researched July 2026 (Mintlify teardown, competitive sweep, Entire read on the
31st); durable facts only, refreshed deliberately rather than casually.

- **The open quadrant**: open-source × agent-ready-by-default is nearly empty
  in every language ecosystem. Hosted platforms (Mintlify, GitBook, Fern) own
  the agent story; OSS generators treat it as a bolt-on plugin. Python is the
  entry wedge — its incumbent, Material for MkDocs, entered maintenance mode
  in November 2025 — but the strategy is the quadrant, not the language:
  Folio generalizes (new parsers, same funnel) rather than staying a Python
  tool.
- **What incumbents monetize**: Mintlify gives the static generator away and
  charges $540/mo plus metered AI credits for hosted AI over the corpus,
  agent analytics, and enterprise compliance. Their renderer is closed and
  local dev phones home. The artifact layer (static site, llms.txt, and .md
  mirrors) is commoditizing. Folio ships that layer free, with no vendor in the
  serving path; MCP remains roadmap work.
- **Who picks Folio**: MkDocs/Sphinx-era maintainers who do not want to own a
  bespoke JS docs app; teams with no-SaaS or air-gapped constraints;
  cost-refusers who want the artifacts without the credit meter; agent-native
  workflows where the coding agent edits docs in the same PR as the code.
- **The agent layer is standardizing** (July 2026 teardown): skill.md,
  `.well-known` discovery, `Accept: text/markdown` negotiation, and the
  Agent-Friendly Documentation Spec (AFDocs) are becoming conventions —
  target the specs, not any vendor's behavior. Mintlify gives away an
  agent-readiness scorer as top-of-funnel; `folio score` (roadmap 0.7) is
  our open equivalent and doubles as the migration hook. Their hosted AI
  translations were retired — validation for not chasing that.
- **Entire** (entire.io): the sharpest adjacent product. "Every agent session
  stored in your repo" — session, prompt and tool call checkpointed beside the
  commit, searchable, portable across Claude Code, Codex, Gemini, Cursor and
  Copilot. Do not reach for the usual contrast: their capture is MIT, needs no
  account, and pushes to your own remote, so "we are open and they are hosted"
  is not an argument. Three real differences. Their payload never enters the
  working tree — it lives on a checkpoints branch and custom refs as raw JSONL
  under an id nobody will type, unreadable in an editor or a PR diff. It is a
  transcript, and a transcript is not a decision. And their schema has no work
  state at all: no status, no acceptance criteria, no parent, no milestone.
  Folio's card has all four, in Markdown, in the tree, reviewed in the same
  diff as the code. They store the transcript; Folio publishes the conclusion.
- **Docs × agents is the position**: Entire has the agent side without docs;
  Mintlify has docs with hosted AI and a meter; the OSS generators have docs
  with agents bolted on. Folio is the only one holding both. That combination
  is the claim to defend, not any single artifact.
- **Do not build agent hook adapters.** Entire writes per-agent integrations
  into eight vendor directories and pays to keep them working. Folio's board is
  driven by ordinary CLI commands any agent can call with nothing installed;
  that is cheaper and outlives any one agent's plugin format.
- **Respect**: Fumadocs (first-party llms.txt tooling, React-only) and
  Zensical (MkDocs' successor, unproven) are the nearest OSS threats; llms.txt
  alone is not a moat — the durable wedge is the combination: agent artifacts
  by default + open renderer + git-native + language generalization.
- **Proof style vs their logo walls**: every Folio proof ends in a live,
  clickable artifact we own — this site itself, live plugin demos with
  their source alongside, themed example galleries. No customer theater.

## Brand Personality

Precise, spare, engineering-native. Folio communicates confidence through
clean structure, exact copy, and working artifacts — never decorative claims.
Folio proves itself through generated pages, the live roadmap, and the
operational board published from its dedicated branch. The proof is a working
artifact, not a claim embedded in the landing page.

## Anti-references

- Generic SaaS landing pages with oversized icon grids, vague feature cards,
  and decorative gradients.
- Documentation sites that require extensive theme hunting before they look
  acceptable.
- Heavy process artifacts in the repository that age faster than code.
- Decorative icon packs when a real artifact (terminal output, generated
  page, live board) carries the message better.
- Client-side password gates on static output — security theater.
- Attack-ladder hero copy that leads with competitors instead of outcomes.

## Design Principles

1. Show the artifact. Prefer real generated docs, command output, API pages,
   and live boards over decorative abstractions.
2. Keep the promise small and provable. Three commands, one config file,
   generated docs from source.
3. Make minimal feel deliberate. Fewer links, fewer cards, fewer icons,
   stronger hierarchy.
4. Treat documentation as product quality. Code, docs, and configuration must
   agree.
5. Keep customization structured. Plugins, named components, presets, and
   config should be explicit and testable.
6. One grammar per surface family: dedicated plugin pages share the same band
   and header rule; checklists are the shared motif for roadmap features and
   board criteria; ghost/dashed marks roadmap-future everywhere.

## Accessibility & Inclusion

Target WCAG AA for generated sites. Preserve keyboard navigation, visible
focus, skip links, reduced-motion behavior, readable contrast in light and
dark modes, and responsive layouts that do not require horizontal scrolling
for normal prose.

Motion should clarify build or state transitions, and must be disabled by
`prefers-reduced-motion`.
