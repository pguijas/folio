# Folio

Open-source documentation for the agent era: every docs page ships as HTML for people and Markdown for agents, generated from the Python source without running it. Positioning, voice, and direction live in `PRODUCT.md`.

## Source of Truth

- `AGENTS.md` is the canonical project memory for coding agents.
- `CLAUDE.md` must only redirect here.
- Do not create, stage, commit, or ask teammates to upload implementation plans, specs, progress logs, or planning notes into the repo. Plan and track work as cards on the board in `board/` instead.
- Do not rely on teammate plans as authority. Treat the code, tests, and user-facing documentation as the source of truth.
- Durable project knowledge belongs in well-written code, focused tests, and the relevant `docs/guide/` page.
- When the user writes in English, briefly note any grammar or spelling mistakes at the end of your response with the corrected form and a short explanation.

## Artifact Work

- **Use exactly two compact stages.** Stage 1 creates standalone candidates in the owning board card and presents them for review without changing the product. Stage 2 starts only after explicit owner confirmation and integrates the selected direction into Folio.
- **Keep artifact context compact.** Retain the objective, confirmed decisions, open choice, canonical artifact links, and validation state. Drop generation transcripts, rejected detail, and repeated file contents from working memory.
- **Condense one card at a time.** `condense artifacts <card-id>` is an agent maintenance directive, not a Folio CLI command. It may read only that card and its sibling artifact directory, and it changes no files. Reject `all`, `.`, paths, globs, multiple ids, and any request that would broaden the operation beyond one permanent card id.
- **Report a verified rendered URL.** Every artifact handoff includes a clickable URL to the rendered output and verifies that URL responds successfully before reporting it. A repository path or filesystem path alone is not an artifact notification.

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

While iterating, run the smallest relevant test file or node. Run the full
suite once after the implementation is complete. A new test must pin a
distinct public behavior or failure boundary; extend an existing table when
only the inputs differ, and batch cases that share an expensive subprocess,
Git repository, or site build.

Template dev server:

```bash
cd template && pnpm install && pnpm run dev
```

## Features Implemented

When adding new features, update this list and the corresponding docs page.

For demos and examples in docs pages (component catalog, plugin live demos), prefer `PreviewCode` — the code + rendered preview pair is the house style: readers see the result and the exact source that produced it without duplicated sections.

### Core

- **Core config validation** - `project`, `source`, `theme`, and `llm` must be mappings; source path lists and `nav` must be lists of strings; malformed values fail with field-specific errors instead of leaking internal exceptions or splitting strings into character paths
- **View source links** - `[source]` links on API objects -> GitHub file+line
- **Cross-references** - Types in param tables, returns, and base classes link to their docs (`xref.py`)
- **NumPy docstrings** - `docstring_style: "google" | "numpy" | "auto"` in docs.yaml
- **Link validation** - Broken internal links reported as warnings during build (`link_checker.py`)
- **`folio coverage`** - CLI command showing per-module docstring coverage with `--min` threshold
- **Plugin system** - Released feature. pluggy-based extension surface for build hooks, custom views, data-backed components, and `docs.yaml` plugin registration; first-party default plugins listed in `DEFAULT_PLUGINS` (`folio/plugin.py`) are loaded on every build before `plugins:` entries (imported directly by module path — never via entry-point lookup, so installed distributions cannot shadow them — with a load failure degrading to a warning instead of breaking builds or the CLI) and deduplicated against explicit listings, staying inert until their config key appears in `docs.yaml`; their `configure()` hooks run `tryfirst` so project plugins' `configure()` can override the parsed defaults, and a non-list `plugins:` value fails config loading loudly
- **Plugin API hardening** - Config/plugin components may shadow a builtin name (warning, builtin replaced) while non-builtin duplicates still raise; MDX contract membership is an explicit `contract=True` flag on `ComponentDefinition` (with `source_label`), not inferred from props; plugin API 1.1 adds `collect_docs`, whose `PluginDocument` sources enter the normal documentation pipeline before generation (route collisions fail before writes; search, sitemap, Markdown mirrors, LLM output, local assets, link validation, and incremental cleanup are inherited); the `plugins` feature is released and enabled by default (the `plugins:` key in `docs.yaml` loads plugins on every build); project plugins listed in `./docs.yaml` get `register_cli` dispatched at CLI startup (cwd-resolved, since typer finalizes commands at import time)
- **Roadmap plugin** - Released first-party default plugin (`folio.plugins.roadmap`). Activated by the `roadmap:` config key in `docs.yaml` (no `plugins:` entry or env var needed): registers the `Roadmap` component, writes typed `lib/roadmap-data.ts`, publishes the `/docs/roadmap/` page (`routes.docs`, default on) and optional standalone `/roadmap/` view (`routes.public`), and provides the `folio roadmap` CLI table preview
- **Landing plugin** - Released first-party default plugin (`folio.plugins.landing`). Sole owner of the `landing:` docs.yaml key: its `configure()` hook normalizes the section (bool shorthand, hero variants, CTAs, install/features/sections, opt-in comparison) into the `Config.landing_*` fields consumed by the template injector. `landing.comparison` takes the project's own `{caption, tools, rows}` table, mirroring the `CompareMatrix` prop contract, and carries it into the rendered section; the legacy `comparison: true` still selects Folio's bundled matrix and warns, because that table names Folio's own competitors and only belongs on Folio's pages. Malformed rows drop with a warning rather than failing the build; without the key the site root serves the docs index. The rendered page stays template-bundled (`template/app/page.tsx`) because injection runs before plugin emission hooks
- **Kanban plugin** - First-party default plugin `folio.plugins.kanban` (in `DEFAULT_PLUGINS`, inert without a `kanban:` key). Git-persisted board with in-browser drag-and-drop (localStorage overlay keyed to the committed board, Export moves to commit changes back, Reset to source). `kanban.source` must point at a cardfile directory; a missing source, a non-dict kanban section, an inline `columns:` key, or a source naming a file or missing path fails configure with a migration pointer, never silently. Registers the `KanbanBoard` component (`template/components/kanban-board.tsx`) plus the typed `lib/kanban-data.ts` data module, emits `/docs/kanban/` when `routes.docs` (default true; never overwrites a user page, refreshes only its own marker-tagged generated page) and an optional public `/kanban` view when `routes.public`, and adds the `folio kanban` CLI table (one section per column, `n/limit` WIP counts). Card `link` values are scheme-checked like other hrefs. Docs: `docs/guide/plugins/kanban/` (index, start, formats, cli, agents); tests: `tests/test_kanban_plugin.py` with mirrors in `test_plugin.py`/`test_cli.py`/`test_site_builder.py`
- **Cardfile board (kanban source directory)** - `kanban.source` pointing at a directory loads the cardfile format: `board.yaml` holds only the column set, `cards/<id>.md` holds one card each (filename stem = permanent card id; files starting with `_` are skipped). A card may keep a sibling directory `cards/<id>/` for its own output. Markdown/MDX below it is contributed through plugin API 1.1's `collect_docs` hook and compiled at `<docs route>/kanban/<id>/<stem>/` as a normal Folio page; a leading `_` opts out. The whole directory is also republished as a raw bundle at `/_folio/kanban/<id>/` (dotfiles and symlinks excluded, cleared even when kanban is disabled on a warm build), so HTML/CSS/JS/images keep their relative dependencies. Exact resolved-path ownership prevents `../` cross-card claims; card-directory roots and descendants may not be symlinks. A `doc:`/`file:` artifact inside the owned directory links to the compiled page or raw file. Frontmatter carries machine state — `status` (column membership; a one-line diff moves a card), `priority`, optional `order` rank, `parent`, `blocked_by`, `created`, typed `artifacts` (`doc`/`api`/`file`/`pr`/`url` + optional label; the board builds no repo URLs — only a `url:` and a target inside the card's own published directory are links, everything else renders as its path) — and the body carries prose: description before the first `##`, `## Acceptance criteria` checkboxes, `## Trail` one-line session entries (`- YYYY-MM-DD @actor (ref): note`, appended at section end). Board topology errors fail the build (unknown status, dangling parent/blocked_by, missing doc/file artifact targets, non-slug filenames); prose problems warn (trail grammar, unknown priority, WIP overflow). Intra-column order is computed (rank, priority, created, id). Loader: `folio/plugins/kanban_board.py`; line-surgery editor (`folio/plugins/kanban_edit.py`) mutates cards by single-line edits with re-parse verification and rollback — never `yaml.safe_dump`. `folio kanban` is a command group (`folio/plugins/kanban_cli.py`): bare = table with ids/blocked markers, plus `show`, `check` (CI gate), and write subcommands `add`/`move` (WIP + open-blocker warnings, `--after` rank midpoints)/`update --set`/`trail`/`attach`, all with post-edit board revalidation + rollback and a `--commit` flag emitting conventional `board:` commits scoped to the board dir. The CLI never writes `docs.yaml`. Agent protocol: `board/SKILL.md` (+ `cards/_TEMPLATE.md`); this repository's own board runs on the format, in `board/`. Docs: `docs/guide/plugins/kanban/` (index, start, formats, cli, agents); tests: `tests/test_kanban_board.py`, `tests/test_kanban_edit.py`, `tests/test_kanban_cli.py`
- **Scoped artifact context maintenance** - Board skills recognize the non-CLI directive `condense artifacts <card-id>`. It accepts exactly one permanent card id, reads only that card and its sibling artifact directory, and replaces verbose working context with the objective, confirmed decisions, open choice, canonical artifact links, and validation state. It never edits files or expands to the whole board or repository. Every artifact handoff must include a rendered URL verified to respond successfully; repository and filesystem paths alone do not count. The scaffolded skill and `docs/guide/kanban/agents.md` carry the same boundary.
- **Custom components (`components:`)** - Released docs.yaml key registering user React components into the extension registry with `origin="config"`: entries are either a directory path (every top-level `.tsx`/`.jsx` registers a component named after its PascalCased file stem, which must match a named export) or a `{name, from, export, expose.mdx}` spec; relative paths anchor to the project directory, files are copied into `components/__folio_components/` with automatic import-stem dedup, a missing directory or source file fails the build, an empty directory warns, name collisions with builtins shadow with a `UserWarning` while config/plugin duplicates raise
- **Generated-page refresh contract** - `SiteBuilder` exposes `read_page`/`remove_page`/`list_pages` (all on the `AssetBuilder` protocol, containment-guarded); kanban and openapi use them for marker-guarded write-if-changed refreshes of their generated docs pages on warm builds — user-authored pages are never touched. Kanban keeps every folder route above a published card document resolvable (compiled pages sit below the folder route, which readers reach by trimming or from a breadcrumb, and `output: export` turns a missing folder index into a dev-server error rather than a 404): each folder a card publishes documents under — the card root and any subdirectory — gets a marker-tagged `<folder>/index` rendered as FeatureCard tiles (documents titled by artifact label or first heading with a first-paragraph excerpt; the card root adds the card's status line, description excerpt, and one tile per attached artifact, linked when published), unless the folder ships its own `index.md`/`README.md` or a non-plugin page already owns the folder's public URL (`_canonical_doc_route` maps `x/index` and `x` to one route, so writing both would shadow the user's page — the same collision `_reject_duplicate_doc_routes` fails loudly for collect_docs pages); with `routes.docs: false` the parent `kanban/index` becomes a directory of publishing cards instead of the board page (only written when the route is on, and deferring to a user legacy `kanban.mdx`), and with the documents gone or the `kanban:` section removed every generated page comes down, swept via `list_pages` by marker

### Build System

- **Authoring contract (`/_folio/contract.json`)** - Every build writes one static JSON file into `build_dir/public/_folio/`, carried through the static export like the Markdown mirrors. Payload: the MDX component contract (builtins plus every config/plugin component registered `contract=True`), `configKeys` (`CORE_CONFIG_KEYS` unioned with plugin `config_keys()` claims), and `routes` (emitted docs URLs), under a `folioVersion`/`mdxContractVersion`/`generatedAt` envelope with one instruction to tolerate unknown fields. Deliberately promises no envelope versioning: `mdxContractVersion` versions the components list only. Builders: `folio/generator/mdx_contract.py` (`build_authoring_contract`/`render_authoring_contract`), written by `SiteBuilder.write_authoring_contract`. Docs: `docs/guide/plugins/authoring.md`; tests: `tests/test_mdx_contract.py`
- **Registry-driven MDX contract module** - `apply_extensions()` rewrites `lib/folio-mdx-contract.ts` from the live registry. The prepare-time write runs before `build_registry()` exists, so plugin components marked `contract=True` never reached the emitted contract; the prepare-time write stays so the file always exists, and the registry write supersedes it before the frontend build
- **Incremental page rebuilds** - SHA-256 manifest (`.build/.folio-manifest.json`) tracks source file hashes; unchanged pages are skipped during `folio build`. Skipped pages still call `register_route`, so `emitted_routes()` (and the published contract's `routes`) does not shrink on a warm build
- **Skip pnpm install** - SHA-256 hash check on `pnpm-lock.yaml`, skips when unchanged
- **File watching** - `folio serve` watches Python + Markdown sources, auto-regenerates changed pages
- **`--clean` flag** - `folio build --clean` / `folio serve --clean` forces full rebuild
- **Multi-version builds** - Alpha feature. `folio build-versions` builds docs for multiple library versions using git worktrees; `folio serve --versions` previews the full version matrix while plain `folio build` and `folio serve` stay on the current working tree
- **Version build reuse** - `folio build-versions` writes `.folio-version.json` per output folder and reuses restored historical `ref` versions when the commit, version matrix, plugin config, and Folio version match; `--clean` forces a full rebuild
- **Version selector** - Alpha feature. Dropdown in docs navbar to switch between versions; enabled only by the explicit multi-version build path configured via `versions` in docs.yaml
- **Structured build output** - `folio build` and `folio serve` keep the Folio banner, then report compact step rows for sources, template prep, pages, links, dependencies, export, completion, and ready output; warnings are attached to the relevant step, and static export prints the full export log once in a bordered build output panel while also saving it to `.build/.folio-build.log`
- **Disabled feature surfaces** - Do not publish public docs or generated API pages for disabled MVP features; keep them out of navigation, guide overviews, generated pages, search, sitemap, and LLM output until the feature is release-ready
- **Custom templates** - Expert `template.path` support for local Next/Nextra-compatible frontend workspaces; Folio copies the template, writes generated content and metadata, relocates `app/docs` via `template.docs_route_base`, exposes project metadata plus template-owned `template.params` as build-time data, emits a versioned MDX component contract, and validates required MDX component names before building custom templates; `template.overlay_path` layers user-owned files on top of the bundled template (user files win, everything else falls back to the bundled template) and is mutually exclusive with `template.path`, which wins with a warning when both are set

### Components (template)

- **Mermaid** - Diagrams via `<Mermaid>` component or fenced ```mermaid blocks (dynamic import, theme-aware)
- **FeatureCard + CardGrid** - Cards for feature overviews and landing pages, with named Hugeicons icon tokens and legacy text-icon fallback
- **FileTree** - Visual file/folder tree from indented text
- **KaTeX math** - `$inline$` and `$$block$$` via Nextra's `latex: true` + `katex/dist/katex.min.css` import in root layout
- **Line highlighting** - Native Shiki `{2,4-6}` syntax in code blocks
- **SourceLink** - `[source]` link component for API reference
- **Tabs + TabItem** - Generic tabbed content panels (text, tables, any MDX content)
- **PreviewCode** - Paired rendered preview and source-code tabs for component catalog examples
- **Accordion + AccordionItem** - Generic collapsible sections with expand/collapse
- **Timeline + TimelineItem** - Vertical timeline with date, title, badge, and description
- **DocPreview** - Responsive iframe previews for showing generated docs pages inside guides
- **BrowserFrame** - Browser window chrome (dots, mono URL bar, optional right-aligned mono status label) for framing live embeds like board miniatures; server-renderable, MDX contract member, docs at `docs/guide/components/browser-frame.md`
- **Compact board variants** - `Roadmap` accepts `compact`/`maxPhases` (18px nodes, excerpt with a "+ N more · full roadmap →" link) and `KanbanBoard` accepts `compact`/`maxCardsPerColumn` (3-column max, toolbar-less, description-less cards, per-column "+N more") for landing-page miniatures framed by `BrowserFrame`
- **ApiReferenceIndex** - Generated API reference overview that routes readers by module, class count, and function count
- **Aperture preset** - ThemeConfigurator preset inspired by developers.openai.com, using Canvas surface, API reference rhythm, Rounded panel code blocks, System sans typography, Theme ink accent, and Lg corner radius
- **Beacon preset** - ThemeConfigurator preset based on an app-style docs shell with product surfaces, workflow density controls, and terminal-style request examples
- **Organic Editorial preset** - Default ThemeConfigurator preset for poster-scale typography, severe whitespace, and cobalt organic imagery
- **Project theme contract** - `docs.yaml` can define a project-owned ThemeConfigurator preset with safe light/dark CSS variable overrides, style overrides, radius defaults, shared control tuning, project variant controls with exact swatches, Geist font-token mapping, docs header branding, and project header actions/search visibility, emitted as `theme/project-theme.ts` during template preparation
- **Theme packages** - `theme.package` points at a trusted local overlay directory copied over the bundled Next/Nextra template before metadata injection; packages can own `app/layout.tsx`, `app/docs/layout.tsx`, `components/theme-configurator.tsx`, `components/project-header-actions.tsx`, `theme/project-theme.ts`, CSS, and any other template file while Folio still supplies generated content and fallback YAML-driven theme modules

### SEO & Meta

- **OpenGraph + Twitter** - Meta tags in root layout
- **Social cards (OG images)** - Auto-generated 1200x630 preview images via `opengraph-image.tsx` route
- **robots.txt** - Next.js metadata route; points at `llms.txt` and `llms-full.txt`
- **sitemap.ts** - Configurable via `project.url` in docs.yaml; lists the per-page Markdown mirrors alongside the HTML routes
- **Markdown mirror discovery** - Every docs page declares its `_folio/markdown/<route>.md` mirror as a `text/markdown` alternate in the page head, so an agent fetching the site finds it without running the client bundle. The mirrors are lossy by construction, but preserve Mermaid source, useful simple-component labels, child prose, and authored code while stripping complex prop-only data; `folio serve` publishes `llms.txt` and `llms-full.txt` from the workspace public root just like a static build
- **Agent guide (`/agent-guide.md`)** - This repository ships one through the project plugin `docs/plugins/agent_guide.py` (registered in `docs.yaml`, emitted from `emit_assets` like `install_script.py`). It briefs a coding agent that a human asked for help with Folio: concept model in teaching order, install and first run with the real prerequisites, diagnosis recipes keyed by symptom, and rules against inventing config keys or CLI flags. Distinct from `board/SKILL.md`, which is the agent *operating* the board. Tests: `tests/test_agent_guide_plugin.py`, including an assertion that `folio mcp` stays absent from the CLI so the guide cannot go stale silently
- **Breadcrumbs** - Native Nextra, enabled by default
- **Favicon** - SVG favicon at `app/icon.svg` with the project monogram injected at build time (`__PROJECT_MONOGRAM__`), customizable via `favicon` in docs.yaml; a non-SVG custom favicon removes the template default so the stale monogram never ships

### i18n & Search

- **i18n** - Multi-language docs via `i18n` section in docs.yaml (opt-in, Nextra-based routing)
- **Navbar search** - Pagefind-backed docs search focuses from the navbar or `Cmd+K`/`Ctrl+K`; configurable with `search.enabled` and `search.placeholder` in docs.yaml
- **Port conflict handling** - `folio serve` defaults to port 4321 and fails clearly if it is occupied; use `--kill-existing` to opt into stopping the existing process
- **Markdown docs underscore aliases** - Hand-written docs routes use kebab-case URLs, but Folio also generates underscore aliases for migrated docs paths such as `/docs/common_errors/`; API reference routes keep Python package/module underscores unchanged

### Landing Page & CLI

- **Landing page configurability** - Released via the first-party landing plugin (see "Landing plugin" above). Hero text, features, CTA, and install commands configurable via `landing` section in docs.yaml, with deep visual personalization still evolving
- **Landing section catalog** - Released via the first-party landing plugin. `landing.sections` composes the generated homepage from reusable sections such as features, routes, output, comparison, pipeline, install, stats, use cases, CTA, and link grids, plus boards (live `BrowserFrame` miniatures of the roadmap/kanban plugins, hidden when neither plugin wrote data), harness (the Folio Docs docs-generator surface beside Folio for Agents as a configurable code-native meta-harness, placing existing coding harnesses and their shared context, rules, board, and artifacts inside one Folio frame without claiming orchestration or remote writes), mechanism (config YAML diff -> pipeline pill rail -> live board, with `+ `/`- ` line tinting and a git-log strip), and statement (accent-highlighted typographic closer with CTAs); the funnel plate draws source inputs narrowing through one `folio build` node into the output surfaces, where each input/output card carries an optional whitelisted `icon` node mark (`config`, `python`, `markdown`, `language`, `folder`, `search`, `agents`, `hash`, `board`; unknown values drop) and the `guarantees` list renders inside the plate as a mono apparatus strip above the FIG. caption; the Folio-branded comparison matrix is opt-in via `landing.comparison: true`. New-section hrefs are scheme-checked via the shared validator but degrade to defaults with a warning instead of failing the build
- **Landing hero variants** - The hero variant catalog is `docs-map | source-pipeline | build-pipeline | heartbeat`; `build-pipeline` is the split hero showing docstring -> `folio build` -> rendered reference
- **Interactive `folio init`** - Wizard with a pixel-style banner, spacer-separated sparkle-framed Folio update line that refreshes in place every second during arrow-key prompts, emoji-rich detected-settings panel with distinct row-label colors, pre-filled project metadata, readchar inline arrow-key selectors, single-key yes/no shortcuts, and a `--yes` flag for non-interactive defaults
- **Git remote detection** - `folio init` auto-detects GitHub repo URL from `git remote origin`

### Deployment & CI/CD

- **Deploy guides** - Step-by-step deployment docs for Vercel, Netlify, GitHub Pages, and Docker
- **CI/CD integration** - GitHub Actions workflows for build, deploy, and coverage gates
- **Branch preview deploys** - `folio init` writes a GitHub Pages preview workflow triggered by trusted `pull_request_target` PR activity; PR code builds in an unprivileged artifact job, the privileged deploy job consumes only the static preview artifact, previews deploy under `/previews/pr-<number>-<branch>/`, the production root is preserved through the internal `folio-pages-state` branch, and successful preview deploys update a sticky PR comment with the latest preview URL
- **Preview index page** - `/previews/` is a real site route (`template/app/previews/layout.tsx` + `page.tsx` + `components/previews-list.tsx`) that reuses the docs shell: the same Nextra Layout/Navbar/Footer, sidebar page map, search, and theme controls as `app/docs/layout.tsx` (injected by `_inject_previews_page` with the same project identity, repo link, and search replacements). It fetches `previews/previews.json` at runtime (written by `write-previews-data` from per-preview `.folio-preview.json` sidecars), so the shell is compiled once and only the data changes per deploy. Cards show PR number, title, branch, last commit (linked to GitHub), author avatar, repo/PR links, and last-updated time, sorted newest first. Metadata is produced by `write-preview-metadata` (enriched with repo, commit URL, and author from the PR event)
- **Branch preview garbage collection** - Every deploy (`pages.yml` on push to `main` and the branch-preview deploy) runs `prune-previews`: it lists open PRs via `gh pr list`, computes their preview ids, and deletes any `/previews/<id>/` directory that does not belong to an open PR. Closed/merged PR previews (and any historically accumulated ones) are removed automatically — there is no separate close-triggered workflow
- **GitHub Pages workflow** - `folio init` writes a two-job (build/deploy) Pages workflow from `folio/workflows.py`; Folio's own repo uses a simplified single-job copy (`.github/workflows/pages.yml`) that builds from source via `uv sync`/`uv run` instead of the released PyPI package
- **Deploy base path resolution** - `project.url` is metadata only; static base paths come from `FOLIO_BASE_PATH`, `deploy.base_path`, or GitHub Pages deploy inference via `deploy.provider` / `FOLIO_DEPLOY_PROVIDER`
- **Pre-commit hook** - `folio coverage --min 80` as a pre-commit hook example

### Sidebar

- **Configured top-level ordering** - `nav` orders real root entries in `_meta.ts`; `Guide` groups authored docs, `API Reference` and `Source Code` name the generated `/api-reference/` tree, and unknown labels are ignored rather than creating dead routes
- **Sidebar emojis** - Nextra 4.x reads `_meta.ts` (not `.json`), sidebar generator outputs TypeScript
- **Nested doc pages** - Components split into sub-pages under `components/` directory, sidebar supports nested groups
- **Sidebar metadata contract** - Generated `_meta.ts` preserves documented ordering and hides nested `index` pages with `{ "display": "hidden" }`
- **Nested section ordering** - `_DOC_PAGE_ORDER` entries carry their own children, so a directory at any depth declares its page order (`("kanban", "Kanban", [("start", "Start a board"), ...])`). `_order_for_dir` walks the path one segment at a time and normalizes every entry to `(slug, title)`, so a child that itself has children never reaches the consumer as a 3-tuple; a path nothing declares returns `[]` and keeps the default order, and a declared page that does not exist yet is skipped rather than emitted
- **Default-collapsed sidebar sections** - generated guide and source-code sidebar groups start collapsed by default, emitting Nextra `open: false` folder entries while leaving leaf pages unchanged; set `sidebar.default_collapsed: false` in docs.yaml to expand them

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
- CI intentionally runs the canonical suite once on Python 3.12; test-running jobs use Node 24 for native TypeScript stripping, while build-only jobs keep Node 20 to cover the supported floor
- nextra-theme-docs 4.6.1 has a Zod v4 bug: `children` in LayoutPropsSchema is nonoptional but destructured out before validation - patched in `site_builder._patch_nextra_schema()`
- `getPageMap("/docs")` is correct - returns children only, avoids redundant "Docs" wrapper in sidebar
- Markdown->MDX conversion must strip `<iframe>`/`<script>` tags, RST directives (`{eval-rst}`), escape `{}`, and convert `.md` links
- Custom template support is a full frontend ownership model: `template.path` selects a trusted local Next/Nextra-compatible workspace, while `template.params` is template-owned JSON data. Do not model this as a broad Folio color-token override layer.

## Writing Style

- **Go easy on the spaced em dash (" — ").** At most one per sentence, and
  never as a comma substitute inside a listing ("any depth — presets,
  packages, overlays — and ship it"). Prefer a colon, a comma, or a full
  stop. Overused, it reads as machine-generated text (owner directive).
  A term–gloss label ("folio mcp — ask the docs from your editor") is fine;
  chains of them are not.
- **Name a field without its colon.** In prose a card field is `parent`, not
  `parent:`. The colon belongs to the line that sets it (`parent: some-id`);
  inside an inline-code chip it reads as a parse error rather than as
  punctuation, which is exactly how it was read. The `roadmap:` and `kanban:`
  blocks in `docs.yaml` and the artifact prefixes `doc:`, `file:`, `pr:`,
  `url:`, `api:` keep theirs — there the colon is part of the token being
  named, not a stray mark after it.

## Documentation Policy

- **Always document new features.** Every feature must be documented in the corresponding `docs/guide/` page and tracked in AGENTS.md's "Features Implemented" section. No feature is done until it is documented.
- **No repo plans.** Do not add implementation plans, specs, progress logs, or local backlog files to any checked-in location. The one exception is the cardfile board in `board/`: it is the project's work surface, validated by `folio kanban check`, and the destination for everything the Roadmap Policy keeps out of `docs.yaml`. If a durable decision matters, document the outcome in `docs/guide/` or this file.
- **Review follow-ups.** Turn durable review findings into focused tests, relevant user-facing docs, or concise AGENTS.md project knowledge; do not keep separate backlog files in the repo.
- **Sidebar ordering.** New doc pages must be added to `_DOC_PAGE_ORDER` in `folio/generator/sidebar.py`, inside the parent entry's children list when the page sits in a subdirectory. No emojis in sidebar titles.

## Roadmap Policy

The `roadmap:` block in `docs.yaml` traces product direction. It says where
Folio is going and what a reader gets when it arrives. It is not a work log, a
release checklist, or a bug list.

- **The test.** Keep a line if it names something Folio does for its users, or
  a stance the product is moving toward. Cut it if it is Folio's own release
  hygiene, the repair of a promise already made, collateral about the product
  rather than the product, or a restatement of the phase title or summary.
  Generating the user's API changelog is direction; keeping Folio's own
  changelog is not.
- **Where the rest goes.** Maintenance, release work, and fixes become cards in
  `board/`, where they carry acceptance criteria and a trail. The protocol is
  `board/SKILL.md`. Cutting a line does not drop the work; it stops selling it.
- **Phases carry status, lines do not.** A phase has one `status`, so every
  line under a `next` phase renders as unshipped. Move shipped work to the
  phase where it shipped, or cut it.
- **Milestones follow the phases.** A card's `milestone` is matched against
  `phase.version` verbatim to build the roadmap's board links, and nothing
  validates the pair. Renumbering a phase means remapping every card that
  pointed at it, in the same change.
- **Register.** Phase summaries are one or two selling sentences. Feature lines
  are short outcome statements, not command lines or file paths.

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
