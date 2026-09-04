# Landing Page

*Configure the optional homepage that appears before the documentation app.*

Folio starts as a docs-first site. The landing page ships as a first-party default
plugin (`folio.plugins.landing`): it is loaded on every build and stays inert until a
`landing:` section appears in `docs.yaml`. When you want a public entry point, add the
section and keep the docs under `/docs/`.

```yaml
landing:
  enabled: true
  hero:
    headline: "Your project"
    notice:                       # optional announcement chip above the kicker
      text: "New — v1.2 released"
      link: "/docs/changelog"     # optional; same href policy as other links
    description: "Generated API reference and guides, straight from your source."
  cta:
    primary:
      text: "Read the docs"
      link: "/docs"
    secondary:
      text: "View source"
      link: "https://github.com/you/project"
```

Use the landing page for project positioning, install commands, and links to the
most important documentation routes. Keep detailed tutorials, configuration
reference, and API content in the docs section.

## Recommended Structure

- **Hero**: project name, one-sentence value proposition, and primary docs link.
- **Install**: the shortest command sequence that gets users to a local preview.
- **Proof**: links to generated API pages, guides, examples, or release notes.
- **CTA**: a final link to `/docs` or the quickstart guide.

The generated landing page uses the same theme tokens, navigation, search
metadata, and static export path as the rest of the site.

## Section Catalog

`landing.sections` composes the homepage below the hero from reusable, config-driven
sections. Each entry needs a `type`; everything else is optional and degrades to
sensible defaults. Available types: `features`, `comparison`, `output`, `routes`,
`pipeline`, `funnel`, `install`, `stats`, `use-cases`, `cta`, `link-grid`, `cells`,
`boards`, `harness`, `mechanism`, and `statement`.

Most sections share the same heading fields (`eyebrow`, `title`, `description`).
Any section may also set `stage: "The mechanism"` — sections with a stage get a
numbered narrative rail above their heading (`STAGE 02 · THE MECHANISM … 02 / 04`),
numbered in page order across all staged sections. Sections without a stage
render unchanged.

The showcase sections below are documented in detail because they render
live plugin data or bespoke layouts.

### `funnel` — the build funnel plate

A technical-diagram centerpiece: source inputs on the left narrow into a single
build node, and every output surface fans out on the right. Inputs marked
`ghost: true` render dimmed and dashed — for roadmap items that are not shipped
yet — and an optional `chip` labels them (for example `"roadmap"`).
An optional `guarantees` list renders as a mono apparatus strip inside the
plate, above the caption. Each input and output may carry an `icon` node
mark, one of: `config`, `python`, `markdown`, `language`, `folder`,
`search`, `agents`, `hash`, `board`. An unknown value is dropped and the
card renders without a mark. Setting `description: ""` suppresses the
heading paragraph, which is how a plate that speaks for itself drops its
prose lead. When `inputs` or `outputs` are omitted the template renders Folio's
own defaults, so a bare `- type: "funnel"` works.

```yaml
landing:
  sections:
    - type: "funnel"
      stage: "The mechanism"
      title: "Your repo narrows to one build."
      command: "folio build"            # default
      command_notes:                    # lines inside the build node
        - "reads source · never runs it"
        - "one build → every surface"
      inputs:
        - label: "docs.yaml"
          icon: "config"                # node mark; unknown values drop
        - label: "more languages"
          icon: "language"
          ghost: true                   # dimmed + dashed: honest roadmap item
          chip: "roadmap"
      outputs:
        - label: "_site/"
          icon: "folder"
      caption: "The build funnel."    # rendered with the mono FIG. treatment
      guarantees:
        - title: "Read, never run."
          detail: "Documenting your package never imports it."
```

### `features` — rows or bento

The default `features` layout is the editorial row list. Setting
`variant: "bento"` switches to a two-column bento grid where each card carries
a small token-only vignette above its copy via `visual`, one of: `components`,
`llms`, `receipt`, `deploy`, `plugins`, `theming`. An unknown `visual` is
dropped and the card renders without a vignette.

```yaml
landing:
  sections:
    - type: "features"
      variant: "bento"
      features:
        - title: "40+ MDX components"
          visual: "components"
          description: "Callouts, tabs, steps, file trees — themed with the site."
```

### `cells` — small feature cells

A bento-style row of compact cards: a mono micro-label, a short claim, a
one-line description, and an optional footer link (the whole cell becomes the
link). The heading is optional — omit `eyebrow`/`title` to render the grid
alone. Cells lay out four per row (three per row when the count is divisible
by three).

```yaml
landing:
  sections:
    - type: "cells"
      items:
        - label: "Agents"                # mono micro-label
          title: "llms.txt output"       # required; cells without it are dropped
          description: "When enabled, the build emits llms.txt alongside the human site."
          href: "/llms.txt"              # optional; makes the cell a link
          link_text: "See this site's llms.txt"
```

### `harness` — two products, one source of truth

Pairs Folio Docs, the docs generator, with Folio for Agents, the meta-harness.
The code-native diagram places the coding harnesses a team already uses inside
the Folio for Agents frame, then shows the portable project surfaces they share:
context, rules, board, and artifacts. It describes a harness over harnesses; it
does not imply that Folio replaces or orchestrates those tools, and it makes no
claim about remote writes.

Every label is configurable. Omit `harnesses` or `unifies` to use the bundled
generic nodes.

```yaml
landing:
  sections:
    - type: "harness"
      eyebrow: "One core, two products"
      title: "Docs for people. A harness over harnesses for agents."
      thesis: "One repository contract."
      docs_label: "Folio Docs"
      docs_detail: "Source and guides become HTML, Markdown, and search."
      agents_label: "Folio for Agents"
      agents_detail: "Portable project state stays readable by the team's coding tools."
      harnesses:
        - label: "Codex"
          detail: "work in the checkout"
        - label: "Claude Code"
          detail: "follows repository rules"
        - label: "Other harnesses"
          detail: "read the same project state"
      unifies:
        - label: "Context"
          detail: "source + Markdown"
        - label: "Rules"
          detail: "contracts in the repo"
        - label: "Board"
          detail: "git-backed work state"
        - label: "Artifacts"
          detail: "durable session output"
```

### `boards` — live board miniatures

Renders compact roadmap and kanban miniatures inside browser-window chrome, each
footed with a link to the full page. The miniatures are the real `Roadmap` and
`KanbanBoard` components reading the data generated by the roadmap and kanban
plugins — the section renders nothing when neither plugin has data, so it is
safe to keep in the config while boards are still empty.

```yaml
landing:
  sections:
    - type: "boards"
      eyebrow: "We run on it"
      title: "The plan is part of the site."
      description: "Both boards are rendered from YAML in this repository."
      roadmap_url: "/roadmap"        # frame URL bar + footer link (default /roadmap)
      kanban_url: "/kanban"          # default /kanban
      roadmap_link_text: "Full roadmap"
      kanban_link_text: "Open the board"
      kanban_embed: true             # false keeps the board off the landing and
                                     # shows the kanban link under the roadmap
      narrow: false                  # true caps a single embedded board at a
                                     # centered max-w-3xl exhibit
```

### `mechanism` — YAML diff to live UI

Shows the edit-commit-rebuild loop: a code window on the left (with an optional
`git log` strip), a pipeline pill rail in the middle, and a live compact kanban
board in browser chrome on the right. Inside `code`, lines starting with `+ `
are tinted as additions and lines starting with `- ` as removals — indented
YAML list items are never mistaken for diff markers. The board pane appears
only when the kanban plugin has data.

```yaml
landing:
  sections:
    - type: "mechanism"
      eyebrow: "Live from this repo"
      title: "The diff is the UI."
      code_title: "board/cards/fix-flaky-test.md"
      code: |-
        ---
        title: "Fix flaky test"
        - status: in-progress
        + status: done
        ---
      commits:
        - hash: "a3f92c1"
          message: "kanban: ship the parser"
      pills: ["git push", "folio build", "deploy"]   # defaults shown
      board_url: "/kanban"
      board_label: "● CURRENT"
      caption: "Change the YAML. Commit. The site updates."
```

### `statement` — typographic closer

A huge centered statement with an optional accent-highlighted substring and
optional CTA links (two work best). `accent` must be an exact substring of
`text`; the first action defaults to the primary button style unless a
`primary` flag says otherwise. `size: "md"` steps the headline and padding
down for a mid-page thesis block (the default suits closers), and
`description` renders a reading-size lead paragraph under the headline.

```yaml
landing:
  sections:
    - type: "statement"
      size: "md"                 # optional: mid-page scale (default is closer scale)
      eyebrow: "The premise"
      text: "No database. No accounts. Just your repo."
      accent: "your repo"
      description: "A few sentences of thesis prose, rendered at reading size."
    - type: "statement"
      eyebrow: "Built with Folio, on Folio"
      text: "If it breaks, our own docs break first."
      accent: "our own docs"
      actions:
        - title: "Read the docs"
          href: "/docs"
```

All hrefs in these sections pass through the same scheme policy as other
configured links; an unsafe value (for example `javascript:`) degrades to the
section default with a warning instead of failing the build.

## Comparison Section

`landing.comparison` adds a feature matrix to the landing page. The table is
yours: you name the tools across the columns and write every row, so the
section says what your project wants to say about its own field.

```yaml
landing:
  comparison:
    caption: "Capability"          # optional label for the top-left header cell
    tools: ["Your tool", "Alternative A", "Alternative B"]
    rows:
      - feature: "Generated API reference"
        values: [true, true, false]
      - feature: "Static export"
        values: [true, "~", false]
        note: "optional gloss under the feature name"
```

Each row needs a `feature` name and exactly one entry in `values` per name in
`tools`. A cell is `true` (yes), `false` (no), or `"~"` (partial); the strings
`yes`, `no`, `true`, and `false` are accepted too, and anything else reads as
partial so a typo never turns into a claim about a named tool. Quote the tilde:
a bare `~` is YAML's null, which also reads as partial.

Malformed config degrades instead of failing the build. A row whose value count
disagrees with `tools` is dropped with a warning, because its cells would
otherwise slide under the wrong column. Rows without a `feature` and rows whose
`values` is not a list are dropped quietly. A `comparison:` mapping left with no
usable row renders nothing and warns.

The same keys work on a `comparison` entry in `landing.sections`, next to the
usual `eyebrow`, `title`, and `description` heading fields:

```yaml
landing:
  sections:
    - type: "comparison"
      title: "Where this fits"
      tools: ["Your tool", "Alternative A"]
      rows:
        - feature: "Runs offline"
          values: [true, false]
```

The two forms place the table differently. A `comparison` entry in
`landing.sections` renders where you put it. The top-level `landing.comparison`
key feeds the default section list instead, which a site uses only when it sets
no `landing.sections` and its hero variant is `source-pipeline`.

### Deprecated: `comparison: true`

`landing.comparison: true` renders Folio's own built-in matrix, which names the
documentation tools Folio compares itself against. It still works and warns on
every build; it will be removed. A `comparison` section with no `tools` and
`rows` falls back to the same built-in matrix and warns the same way. Replace
both with your own `tools`/`rows` table.

## Live demo

This site uses the plugin itself: the [landing page at the site root](/) is rendered from the `landing:` section of this repository's `docs.yaml`.
