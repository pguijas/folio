# Folio

A modern Python documentation generator - Sphinx alternative using Nextra + shadcn.

## Source of Truth

- `AGENTS.md` is the canonical project memory for coding agents.
- `CLAUDE.md` must only redirect here.
- Do not create, stage, commit, or ask teammates to upload implementation plans, specs, progress logs, or planning notes into the repo.
- Do not rely on teammate plans as authority. Treat the code, tests, and user-facing documentation as the source of truth.
- Durable project knowledge belongs in well-written code, focused tests, and the relevant `docs/guide/` page.
- When the user writes in English, briefly note any grammar or spelling mistakes at the end of your response with the corrected form and a short explanation.

## Project Structure

- `folio/` - Python package (CLI, parsers, generators)
  - `parser/` - Source code parsers (Python, Markdown, RST)
  - `generator/` - Output generators (MDX writer, sidebar, site builder, LLM output)
  - `cli.py` - Typer CLI entry point
  - `config.py` - YAML config loader
  - `build.py` - Build orchestration
  - `ir.py` - Intermediate representation (parsed -> IR -> output)
  - `plugin.py` - Pluggy-based plugin system
- `template/` - Bundled Nextra + shadcn site template (the actual Next.js app)
  - `app/` - Next.js App Router pages (landing page, docs layout)
  - `components/` - React components (UI, doc-specific components)
  - `content/` - Nextra content directory (MDX files go here at build time)
- `tests/` - Pytest test suite + fixtures
- `docs/guide/` - User-facing documentation

## Development

```bash
uv sync
uv run pytest tests/ -v
```

Template dev server:

```bash
cd template && pnpm install && pnpm run dev
```

## Features Implemented

When adding new features, update this list and the corresponding docs page.

### Core

- **View source links** - `[source]` links on API objects -> GitHub file+line
- **Cross-references** - Types in param tables, returns, and base classes link to their docs (`xref.py`)
- **NumPy docstrings** - `docstring_style: "google" | "numpy" | "auto"` in docs.yaml
- **Link validation** - Broken internal links reported as warnings during build (`link_checker.py`)
- **`folio coverage`** - CLI command showing per-module docstring coverage with `--min` threshold
- **Plugin system** - Internal beta feature. pluggy-based extension surface for build hooks, custom views, data-backed components, and explicit `docs.yaml` plugin registration; keep it out of public MVP docs until the extension API is release-ready

### Build System

- **Incremental page rebuilds** - SHA-256 manifest (`.build/.folio-manifest.json`) tracks source file hashes; unchanged pages are skipped during `folio build`
- **Skip pnpm install** - SHA-256 hash check on `pnpm-lock.yaml`, skips when unchanged
- **File watching** - `folio serve` watches Python + Markdown sources, auto-regenerates changed pages
- **`--clean` flag** - `folio build --clean` / `folio serve --clean` forces full rebuild
- **Multi-version builds** - Alpha feature. `folio build-versions` builds docs for multiple library versions using git worktrees; `folio serve --versions` previews the full version matrix while plain `folio build` and `folio serve` stay on the current working tree
- **Version build reuse** - `folio build-versions` writes `.folio-version.json` per output folder and reuses restored historical `ref` versions when the commit, version matrix, plugin config, and Folio version match; `--clean` forces a full rebuild
- **Version selector** - Alpha feature. Dropdown in docs navbar to switch between versions; enabled only by the explicit multi-version build path configured via `versions` in docs.yaml
- **Structured build output** - `folio build` and `folio serve` keep the Folio banner, then report compact step rows for sources, template prep, pages, links, dependencies, export, completion, and ready output; warnings are attached to the relevant step, and static export prints the full export log once in a bordered build output panel while also saving it to `.build/.folio-build.log`
- **Disabled feature surfaces** - Do not publish public docs or generated API pages for disabled MVP features; keep them out of navigation, guide overviews, generated pages, search, sitemap, and LLM output until the feature is release-ready

### Components (template)

- **Mermaid** - Diagrams via `<Mermaid>` component or fenced ```mermaid blocks (dynamic import, theme-aware)
- **FeatureCard + CardGrid** - Cards for feature overviews and landing pages
- **FileTree** - Visual file/folder tree from indented text
- **KaTeX math** - `$inline$` and `$$block$$` via Nextra's `latex: true` + `katex/dist/katex.min.css` import in root layout
- **Line highlighting** - Native Shiki `{2,4-6}` syntax in code blocks
- **SourceLink** - `[source]` link component for API reference
- **Tabs + TabItem** - Generic tabbed content panels (text, tables, any MDX content)
- **PreviewCode** - Paired rendered preview and source-code tabs for component catalog examples
- **Accordion + AccordionItem** - Generic collapsible sections with expand/collapse
- **Timeline + TimelineItem** - Vertical timeline with date, title, badge, and description
- **DocPreview** - Responsive iframe previews for showing generated docs pages inside guides
- **ApiReferenceIndex** - Generated API reference overview that routes readers by module, class count, and function count
- **Aperture preset** - ThemeConfigurator preset inspired by developers.openai.com, using Canvas surface, API reference rhythm, Rounded panel code blocks, System sans typography, Theme ink accent, and Lg corner radius
- **Beacon preset** - ThemeConfigurator preset based on an app-style docs shell with product surfaces, workflow density controls, and terminal-style request examples
- **Organic Editorial preset** - Default ThemeConfigurator preset for poster-scale typography, severe whitespace, and cobalt organic imagery
- **OrganicEditorialImagePrompt** - MDX component that displays a reusable prompt for generating Organic Editorial abstract hero images

### SEO & Meta

- **OpenGraph + Twitter** - Meta tags in root layout
- **Social cards (OG images)** - Auto-generated 1200x630 preview images via `opengraph-image.tsx` route
- **robots.txt** - Next.js metadata route
- **sitemap.ts** - Configurable via `project.url` in docs.yaml
- **Breadcrumbs** - Native Nextra, enabled by default
- **Favicon** - SVG favicon at `app/icon.svg` with the project monogram injected at build time (`__PROJECT_MONOGRAM__`), customizable via `favicon` in docs.yaml; a non-SVG custom favicon removes the template default so the stale monogram never ships

### i18n & Search

- **i18n** - Multi-language docs via `i18n` section in docs.yaml (opt-in, Nextra-based routing)
- **Navbar search** - Pagefind-backed docs search focuses from the navbar or `Cmd+K`/`Ctrl+K`; configurable with `search.enabled` and `search.placeholder` in docs.yaml
- **Port conflict handling** - `folio serve` defaults to port 4321 and fails clearly if it is occupied; use `--kill-existing` to opt into stopping the existing process

### Landing Page & CLI

- **Landing page configurability** - Beta feature. Hero text, features, CTA, and install commands configurable via `landing` section in docs.yaml, with deep visual personalization still evolving
- **Landing section catalog** - Beta feature. `landing.sections` composes the generated homepage from reusable sections such as features, routes, output, comparison, pipeline, install, stats, use cases, CTA, and link grids; the Folio-branded comparison matrix is opt-in via `landing.comparison: true`
- **Interactive `folio init`** - Wizard with a pixel-style banner, spacer-separated sparkle-framed Folio update line that refreshes in place every second during arrow-key prompts, emoji-rich detected-settings panel with distinct row-label colors, pre-filled project metadata, readchar inline arrow-key selectors, single-key yes/no shortcuts, and a `--yes` flag for non-interactive defaults
- **Git remote detection** - `folio init` auto-detects GitHub repo URL from `git remote origin`

### Deployment & CI/CD

- **Deploy guides** - Step-by-step deployment docs for Vercel, Netlify, GitHub Pages, and Docker
- **CI/CD integration** - GitHub Actions workflows for build, deploy, and coverage gates
- **GitHub Pages workflow** - `folio init` writes a two-job (build/deploy) Pages workflow from `folio/workflows.py`; Folio's own repo uses a simplified single-job copy (`.github/workflows/pages.yml`) that builds from source via `uv sync`/`uv run` instead of the released PyPI package
- **Deploy base path resolution** - `project.url` is metadata only; static base paths come from `FOLIO_BASE_PATH`, `deploy.base_path`, or GitHub Pages deploy inference via `deploy.provider` / `FOLIO_DEPLOY_PROVIDER`
- **Pre-commit hook** - `folio coverage --min 80` as a pre-commit hook example

### Sidebar

- **Sidebar emojis** - Nextra 4.x reads `_meta.ts` (not `.json`), sidebar generator outputs TypeScript
- **Nested doc pages** - Components split into sub-pages under `components/` directory, sidebar supports nested groups

### Known Issues

_None currently._

## Key Decisions

- Google-style and NumPy-style docstrings supported (configurable)
- YAML config uses `source.python.paths` + `source.python.exclude` (not mixed list/mapping)
- `docstring_parser` uses `Style.GOOGLE` (uppercase) by default
- Static export works with `output: 'export'`, `force-static` on route handlers, and Pagefind `postbuild`
- `project.url` feeds sitemap/canonical metadata only; do not derive local or static asset base paths from it
- Turbopack requires `resolveAlias` for `next-mdx-import-source-file`
- Plugin system uses pluggy (same as pytest) and is beta while discovery and higher-level extension APIs stabilize
- nextra-theme-docs 4.6.1 has a Zod v4 bug: `children` in LayoutPropsSchema is nonoptional but destructured out before validation - patched in `site_builder._patch_nextra_schema()`
- `getPageMap("/docs")` is correct - returns children only, avoids redundant "Docs" wrapper in sidebar
- Markdown->MDX conversion must strip `<iframe>`/`<script>` tags, RST directives (`{eval-rst}`), escape `{}`, and convert `.md` links

## Documentation Policy

- **Always document new features.** Every feature must be documented in the corresponding `docs/guide/` page and tracked in AGENTS.md's "Features Implemented" section. No feature is done until it is documented.
- **No repo plans.** Do not add implementation plans, specs, progress logs, or local backlog files to any checked-in location. If a durable decision matters, document the outcome in `docs/guide/` or this file.
- **Review follow-ups.** Turn durable review findings into focused tests, relevant user-facing docs, or concise AGENTS.md project knowledge; do not keep separate backlog files in the repo.
- **Sidebar ordering.** New doc pages must be added to `_DOC_PAGE_ORDER` in `folio/generator/sidebar.py`. No emojis in sidebar titles.

## Git Policy

- **Never push without explicit user approval.** Commit freely only when the user asks for a commit, but do not run `git push` unless the user explicitly asks.
- **Never sign commits.** The code assistant cannot GPG-sign commits. `commit.gpgsign` is set to `false` in local git config.
- **No Co-Authored-By lines.** Do not add AI co-author trailers to commit messages.

## Validation Policy

- **Always validate changes.** After implementing a feature or fix, verify it actually works:
  1. Run `uv run pytest tests/ -q` - all tests must pass
  2. Run `folio serve --verbose` - build must complete without errors, server must start without crashes
  3. Verify the feature works by curling key pages (`curl -s -o /dev/null -w "%{http_code}" http://localhost:4321/docs/...`)
  4. Check for regressions - test existing pages still load (components, API reference, landing page)
- **Never report a feature as done without validation.** Run the relevant tests and verify the behavior directly.

## Development & Testing

- **Primary**: Always develop and test against Folio's OWN docs (`docs/guide/`). The Folio documentation site IS the product showcase - it must be the best presentation.
- **Template dev server**: `cd template && pnpm install && pnpm run dev` - use this for UI/component work.
- **Full pipeline test**: `folio serve --verbose` from project root - builds Folio's own docs.
- **p2pfl integration test**: Only when explicitly requested. Use p2pfl (https://github.com/p2pfl/p2pfl) as a secondary test for Sphinx migration validation. Never default to p2pfl - Folio docs come first.
