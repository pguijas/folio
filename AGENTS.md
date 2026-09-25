# Folio

Folio is one product: Folio Docs, a documentation engine shipped as the `folio`
binary. It owns the engine, the CLI host, and the public interfaces extensions
use; `folio-cli` carries that host as a library and builds the binary.
Positioning, voice, and direction live in `PRODUCT.md`.

## Source of Truth

- `AGENTS.md` is the canonical guidance for contributors and coding agents.
- `CLAUDE.md` must only redirect here.
- The specification is the fixtures each crate keeps under `crates/<crate>/tests/fixtures/`, the example projects in `docs/examples/` and the Rust tests. A crate is correct when its output fits them. A change to a shape they fix is a deliberate decision, stated in the PR.
- The previous Python implementation is not a target to match. There is no reference build to compare against, no parity job, and no Python in the repository.
- Do not commit implementation plans, specs, progress logs or planning notes; durable knowledge goes into code, tests and `docs/guide/`.
- Treat the code, tests, and user-facing documentation as the source of truth.

## Project Structure

The root `Cargo.toml` is a virtual workspace over the eleven crates under
`crates/`. Every engine crate lives there;
`crates/folio-cli/tests/workspace_boundaries.rs` pins that ownership.

- `crates/*` - the engine: `folio-cli` (CLI host, commands, pipeline and terminal UI; `src/bin/folio.rs` is the `folio` binary and only calls `folio_cli::run`), `folio-config` (`docs.yaml`), `folio-mdx`, `folio-plugins` (plugin interfaces, host and built-ins), `folio-site`, `folio-watch`, `folio-ir`, `folio-lang-python`, `folio-lang-javascript`, `folio-lang-rust`, and `folio-docs` (IR to pages, cross-references and coverage)
- `template/` - the bundled Next.js/Nextra site template, built with pnpm: the one frontend template
- `docs/` - the guides (`guide/`), the sample projects the guides build (`examples/`), site components (`components/`) and the README images (`readme/`)
- `crates/<crate>/tests/fixtures/` - the specification, beside the crate whose tests read it: the config `docs.yaml` that must load without a warning (`folio-config`), the sources each reader must parse with the `golden_ir.json` they parse to (`folio-lang-javascript`, `folio-lang-rust`, and `folio-lang-python` with `rich_package/`, `example_package_ir.json` and `unparse_fixtures.json`), `mdx_contract_baseline.json` (`folio-plugins`) and the `generated_site` golden of the example project (`folio-docs`, compared through the binary by `folio-cli`). `FOLIO_UPDATE_GOLDEN=1` rewrites the goldens whose tests carry the switch; read the diff, never regenerate to make a test pass
- `docs.yaml` - Folio's own site config (landing, roadmap), the integration fixture; `theme/folio-site/` is its theme
- `install.sh` - the binary installer behind the install one-liner
- `.github/workflows/rust.yml` - fmt, clippy, test; `release.yml` - a `v*` tag builds the five release archives (four `install.sh` downloads, plus the Windows zip it points at) and publishes the GitHub Release; `pages.yml` and `branch-previews.yml` - the production deploy from `main` and a preview per same-repository PR
- Repository policy, `.github` automation, legal files, contributor guidance, and agent instructions stay at the repository root. There is one product here, so there is one of each file: one `README.md`, one `PRODUCT.md`, one `rust-toolchain.toml`, one `.gitignore`.

## Development

A Rust toolchain via rustup (`rust-toolchain.toml` pins stable with `clippy` and `rustfmt`), plus Node.js 20.19+ and pnpm 10 for `folio build`, `folio serve` and template work. The checks CI runs (`.github/workflows/rust.yml`), from the repository root:

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo build --release   # target/release/folio
```

While iterating, run the narrowest useful selection (`cargo test -p folio-config`, `cargo test -p folio-cli --test release_surface`), then the checks above once after the implementation is complete. `cargo run --release -p folio-cli -- build --clean` runs the binary without installing it.

The bundled template ships inside the binary (`folio-site`'s `build.rs` embeds every template file) and is materialised once under the user cache dir, `$XDG_CACHE_HOME/folio/template/<version>-<hash>` or the platform equivalent, then copied into `.build/`. `FOLIO_TEMPLATE_DIR` points the build at a template checkout instead, for template development. `FOLIO_FRONTEND_RUNTIME=noop` is the test-only seam that swaps the pnpm/Next runtime for one that installs, builds and serves nothing, so pipeline tests run without Node; it is not a user switch.

Unit tests and test-only helpers live in separate files beside the module they test, declared with `#[cfg(test)] #[path = "foo_tests.rs"] mod tests;` (or the helper module's name): `src/foo.rs` loads `src/foo_tests.rs`, and `lib.rs`, `main.rs` and `mod.rs` load an adjacent `tests.rs`. A directory under `src/` holds submodules, never only tests. Keep private access through the existing module hierarchy. Crate integration tests live under each crate's `tests/` directory. `crates/folio-cli/tests/` holds the docs CLI suites and documentation checks, which run the real binary through `env!("CARGO_BIN_EXE_folio")`, the release surface checks (`release_surface.rs`), dependency rules (`workspace_boundaries.rs`), and the shared support every suite loads with `mod common;` (`common/`). `cargo test -p folio-cli` runs all these targets. A new test must pin a distinct public behavior or failure boundary; extend an existing table when only the inputs differ, and batch cases that share an expensive subprocess, Git repository, or site build.

A behaviour is pinned by a Rust test or a black-box run of the binary; no Python tests exist. A unit test when the behaviour is local to one function; an integration test under the crate's `tests/` when it crosses crates or touches the filesystem; a run of the built binary (`env!("CARGO_BIN_EXE_folio")`) against a project from `docs/examples/`, checked against the checked-in golden, when it is what a user sees.

Template dev server:

```bash
cd template && pnpm install && pnpm run dev
```

## Product behaviour

The behaviour Folio ships, pinned by the fixtures and the tests. When adding behaviour, update this list and the corresponding docs page. For demos and examples in docs pages, prefer `PreviewCode`: the code + rendered preview pair is the house style.

### Engine and extensions

- **Package ownership** - Folio Docs owns the CLI host, documentation engine, HTML, Markdown mirrors, LLM indexes, authoring contract and plugin interfaces. `folio-cli` is the library that carries them and the package that builds `folio`, the only executable.
- **Python source integrity** - Invalid Python fails the build with the source filename instead of silently publishing an empty API module; `source.python.exclude` accepts the documented glob patterns and exact file/directory paths without prefix overmatching; a conventional `src/` source root publishes its top-level modules and packages under their import names rather than a synthetic `src.*` namespace. Folio reads the code; it never runs it.
- **Language seam** - Every parsed module is a `ModuleIR` (`folio-ir`; golden `crates/folio-lang-rust/tests/fixtures/golden_ir.json`) whose `language` names the producing parser; `FunctionIR.signature`/`visibility` and `TypeIR` (`struct|enum|trait|interface|type_alias|union|impl`, rendered after functions with a signature block, a fields/variants table and its methods) carry what non-Python parsers produce. Python routes are `api-reference/<name with . as />`; other languages route under `api-reference/<language>/...`, key cross-reference symbols as `<language>:<module>.<symbol>`, and the sidebar groups `Source Code` by language only when more than one is present. Parsers run Python-first for the build and the watcher (roots watched and hashed, files re-parsed by the owning parser in its discovery order, removed on delete; manifest entries carry `language`). `source.<language>` keys share the `paths` + `exclude` shape and one exclude rule (exact path, subtree, glob) implemented once in `folio-ir::excludes`, with a flat, deterministic discovery order and `node_modules`/`target` always skipped. Every language Folio recognises (`python`, `javascript`, `rust`) has a reader in the binary. Languages are parsers, not toolchains: a parser must never require the language's SDK.
- **Rust sources** - The module tree from `lib.rs`/`main.rs` following `pub mod x;`, over the crates under `source.rust.paths` (a crate directory, a workspace above them, or a crate's `src/`; the crate name comes from `Cargo.toml`, hyphens as underscores). `pub` items only: functions, structs, enums, traits, impl blocks, type aliases, consts and statics, with `///`, `//!` and `#[doc]` comments, signatures sliced from the source onto one line and attributes as written; `pub use` as text, `cfg` shown not evaluated, macros skipped, inline `mod {}` items on the page of the file that declares them. A syntax error names the file and fails the build, and the watcher keeps the last valid page. Fixture and specification: `crates/folio-lang-rust/tests/fixtures/` with `golden_ir.json`; guide: `docs/guide/languages.md`.
- **JavaScript sources** - Every `.js`/`.mjs`/`.cjs` file under `source.javascript.paths`, parsed with tree-sitter, one module per file named after its path (`utils/index.js` is `utils`, a root-level `index.js` its root directory). Exports only: ESM named and default exports, `export const/let/var`, arrow functions bound to an exported name, CommonJS `exports.x` and the names in `module.exports = { ... }` (listed as re-exports on the module page), with JSDoc `@param`/`@returns`/`@throws`/`@deprecated`/`@example` and signatures sliced from the source onto one line. Every method is a `FunctionKind::Method` whatever its flavour, getters, setters and statics included, so no Python decorator marker reaches a JavaScript page; a `#private` member is not documented. `node_modules` is never read, `.jsx` is skipped with a warning, `.ts`/`.tsx` are not read. A syntax error names the file and fails the build. Fixture and specification: `crates/folio-lang-javascript/tests/fixtures/` with `golden_ir.json`; guide: `docs/guide/languages.md`.
- **Config validation** - `docs.yaml` is validated by `folio-config`, one error message per field: `project`, `source`, `theme`, and `llm` must be mappings; source path lists, `nav` and `public` must be lists of strings; `output` is a non-empty relative path inside the project; `public` entries are project-relative files contained in the project (outside, `.build/` or the output dir fail the build); malformed values fail with field-specific errors instead of leaking internal errors; unknown top-level keys warn; string and boolean keys are type-checked; an explicit `null` on a typed key is an error.
- **View source links** - `[source]` links on API objects -> GitHub file+line
- **Cross-references** - Types in param tables, returns, and base classes link to their docs
- **Docstring styles** - `source.python.docstring_style: "auto" | "google" | "numpy"` in docs.yaml; `auto` (the default) detects the style per docstring
- **Link validation** - Broken internal links reported as warnings during build
- **`folio coverage`** - Per-module docstring coverage with a `--min` threshold; it reads Python sources only in this release and refuses a config without `source.python` paths
- **Built-in integrations** - Landing, roadmap and openapi are compiled in and inert until their section (`landing:`, `roadmap:`, `openapi:`) appears in `docs.yaml`; each owns its section's normalization, and they dispatch in that fixed order. There is no `plugins:` key. Project plugins (`./path` plugins, module plugins, a hook API in the host process): Not available in this release; they return as sidecars over NDJSON JSON-RPC on stdio through `folio-plugins`. Say so plainly wherever plugin authoring or the plugins key is documented.
- **Shaping the plugin interface for a process boundary** - The extension seam is being made expressible as data, ahead of a sidecar protocol. `Plugin::name` and `Plugin::config_keys` return owned values rather than `&'static` references, because a plugin that arrives from outside the binary learns both at runtime, and the five extension-registry types (`ComponentDefinition`, `LayoutDefinition`, `DataModuleDefinition`, `ViewBlock`, `ViewDefinition`) round-trip through JSON with their `IndexMap` key order intact, because declaration order is part of what a registration means. Still compiled in, still no dynamic loading: `configure` taking `&mut DocsConfig` and `register_extensions` mutating the registry are the two prerequisites left.
- **Plugin interface** - Config and plugin components may shadow a builtin name (warning, builtin replaced) while non-builtin duplicates fail; MDX contract membership is an explicit flag on a component definition, not inferred from props; documents a plugin collects enter the normal documentation pipeline before generation (route collisions fail before writes; search, sitemap, Markdown mirrors, LLM output, local assets, link validation and incremental cleanup are inherited).
- **Roadmap** - Activated by `roadmap:`: registers the `Roadmap` component, writes typed `lib/roadmap-data.ts`, publishes `/docs/roadmap/` (`routes.docs`, default on) and the optional standalone `/roadmap/` (`routes.public`), and provides the `folio roadmap` CLI table preview. The grouping key is `project` end to end (config, data module, component), so one site can carry independent release sequences; Folio's own phases are all `docs`.
- **Landing** - Sole owner of `landing:`: bool shorthand, hero variants, CTAs, install/features/sections, opt-in comparison. `landing.comparison` takes the project's own `{caption, tools, rows}` table (the `CompareMatrix` prop contract); the legacy `comparison: true` still selects Folio's bundled matrix and warns, because that table names Folio's own competitors. Malformed rows drop with a warning; without the key the site root serves the docs index. The rendered page is template-bundled (`template/app/page.tsx`).
- **Custom components (`components:`)** - Entries are a directory path (every top-level `.tsx`/`.jsx` registers a component named after its PascalCased file stem, which must match a named export) or a `{name, from, export, expose.mdx}` spec; relative paths anchor to the project directory, files are copied into `components/__folio_components/` with import-stem dedup, a missing directory or source file fails the build, an empty directory warns, name collisions with builtins shadow with a warning while config/plugin duplicates fail.
- **Generated-page refresh** - Generated docs pages (openapi, and the documents a plugin collects) are write-if-changed refreshes on warm builds; user-authored pages are never touched, and a generated page that collides with a user route fails the build before any write.

### Build System

- **Authoring contract (`/_folio/contract.json`)** - Every build writes one static JSON file into `build_dir/public/_folio/`, carried through the static export like the Markdown mirrors: the MDX component contract (builtins plus every config/plugin component registered for the contract), `configKeys` (core keys plus the sections built-ins claim), and `routes` (emitted docs URLs), under a `folioVersion`/`mdxContractVersion`/`generatedAt` envelope with one instruction to tolerate unknown fields. `mdxContractVersion` versions the components list only. `lib/folio-mdx-contract.ts` is rewritten from the live registry before the frontend build. Baseline: `crates/folio-plugins/tests/fixtures/mdx_contract_baseline.json`.
- **Incremental page rebuilds** - A SHA-256 manifest (`.build/.folio-manifest.json`) tracks source file hashes, the symbol-index digest and the build context; unchanged pages are skipped during `folio build`. Skipped pages still register their route, so the published contract's `routes` never shrinks on a warm build. Rules: a source's `hash` is the SHA-256 of its raw bytes; `symbols` is the SHA-256 of the canonical JSON (sorted keys, compact) of the project-wide symbol index; the `build` context (config, template tree, theme package, docs route base, generator, source ref, experimental features, backend) is compared wholesale; a page regenerates when any of the three changed. There is no structural hash of `ModuleIR`.
- **Skip pnpm install** - SHA-256 check on `pnpm-lock.yaml`, skipped when unchanged
- **File watching** - `folio serve` coalesces source events into one batch, retains the parsed IR, invalidates API consumers when the symbol index changes, and refreshes guides, collected plugin docs, metadata, search, mirrors, contract, and LLM outputs before saving the manifest. Pending source edits survive failed batches; plugin callbacks stay serial. Preview examples only rebuild on example changes, on a full build as much as in the watcher: each published example carries the digest of its sources, the Folio version and the template (the version, not the hash of the executable, which would invalidate every example on every `cargo build`), and one whose digest still matches is left alone. The `Previews` row says how many were rebuilt, how many were unchanged and how many were swept because their example is gone. Configuration, themes, and undeclared inputs still require a restart. One republish per save; `FOLIO_TRACE` records JSONL batch events.
- **Stable generated writes** - Text outputs are written only when the bytes change, atomically per file with preserved modes. Contract `generatedAt` (the one volatile field) advances only on semantic contract changes; missing mirrors are repaired. A batch is not a whole-site filesystem transaction.
- **Live Markdown assets and search reuse** - Documentation-directory asset events enter source batches. The manifest tracks copied local images, preserves identical copies, and removes obsolete assets only after all pages release their destination; asset paths stay within their page directory and cannot overwrite MDX or sidebar metadata. Search extraction reuses unchanged generated pages within one build and invalidates replacements, removals, and URL-base changes.
- **Build/watch route consistency** - Build and watch share the source parser and route derivation, including root/nested README-to-index routes. Edits and deletions update the canonical page and its Markdown mirror; generator fingerprints include the real output converters.
- **`--clean` flag** - `folio build --clean` / `folio serve --clean` forces a full rebuild
- **Multi-version builds** - Not available in this release: `versions:` warns and is ignored, and the hidden `folio build-versions` and `folio serve --versions` run only under `FOLIO_EXPERIMENTAL`. There, `folio build-versions` builds docs for multiple library versions using git worktrees and `folio serve --versions` previews the version matrix while plain `folio build` and `folio serve` stay on the working tree. Each output folder carries `.folio-version.json`; restored historical `ref` versions are reused when commit, version matrix, plugin config, and Folio version match; `--clean` forces a full rebuild. The navbar version selector is enabled only by `versions` in docs.yaml.
- **Structured build output** - `folio build` and `folio serve` keep the Folio banner, then report compact step rows for sources, template prep, pages, links, dependencies, export, completion, and ready output; warnings attach to their step; static export prints the full export log once in a bordered panel and saves it to `.build/.folio-build.log`
- **Disabled feature surfaces** - No public docs or generated API pages for disabled features; keep them out of navigation, guide overviews, generated pages, search, sitemap, and LLM output until release-ready. A gated page carries the notice "Not available in this release" in a Callout right under its H1.
- **Theme packages from elsewhere** - `theme.package` takes a directory string as before, or a mapping of `git`, `rev`, `digest` and an optional `path`. A remote package is fetched with `git` into the theme cache (`<user cache>/folio/themes/<the digest's first 16 hex characters>`, or `FOLIO_THEME_CACHE_DIR`), its tree is hashed with the same digest the build context uses, and a mismatch fails the build naming both digests; the cache entry is the unit of reuse, so a second build makes no network call and a hand-edited entry is refetched rather than trusted. `package.json`, `pnpm-lock.yaml` and `pnpm-workspace.yaml` are reserved for every package because the frontend installs against Folio's pinned lockfile, and `next.config.mjs` is reserved for fetched ones: provenance decides who may own the build config. `components:` entries must stay inside the project directory like every other path. The fetch drops the ambient git environment and pins the checkout filters off, so the tree is a function of the commit rather than of the machine; the digest is length-prefixed so it identifies one tree only.
- **Custom templates** - Expert `template.path` support for local Next/Nextra-compatible frontend workspaces: Folio copies the template, writes generated content and metadata, relocates `app/docs` via `template.docs_route_base`, exposes project metadata plus template-owned `template.params` as build-time data, emits a versioned MDX component contract, and validates required MDX component names before building; `template.overlay_path` layers user-owned files on top of the bundled template (user files win) and is mutually exclusive with `template.path`, which wins with a warning when both are set

### Components (template)

- **Mermaid** - Diagrams via `<Mermaid>` or fenced ```mermaid blocks (dynamic import, theme-aware)
- **FeatureCard + CardGrid** - Cards for feature overviews and landing pages, with named Hugeicons icon tokens and legacy text-icon fallback
- **FileTree** - Visual file/folder tree from indented text
- **KaTeX math** - `$inline$` and `$$block$$` via Nextra's `latex: true` + `katex/dist/katex.min.css` import in root layout
- **Line highlighting** - Native Shiki `{2,4-6}` syntax in code blocks
- **SourceLink** - `[source]` link component for API reference
- **Tabs + TabItem**, **Accordion + AccordionItem**, **Timeline + TimelineItem** - Generic tabbed panels, collapsible sections, and a vertical timeline with date, title, badge, and description
- **PreviewCode** - Paired rendered preview and source-code tabs for component catalog examples
- **DocPreview** - Responsive iframe previews of generated docs pages inside guides
- **BrowserFrame** - Browser window chrome (dots, mono URL bar, optional right-aligned mono status label) for framing live embeds like the roadmap miniature; server-renderable, MDX contract member, docs at `docs/guide/components/browser-frame.md`
- **Compact roadmap** - `Roadmap` accepts `compact`/`maxPhases` for landing-page miniatures framed by `BrowserFrame`
- **ApiReferenceIndex** - Generated API reference overview that routes readers by module, class count, and function count
- **ThemeConfigurator presets** - Organic Editorial (default: poster-scale typography, severe whitespace, cobalt organic imagery), Aperture (Canvas surface, API reference rhythm, rounded panel code blocks, system sans, theme ink accent, Lg radius) and Beacon (app-style docs shell with product surfaces, density controls, terminal-style request examples)
- **Project theme contract** - `docs.yaml` can define a project-owned ThemeConfigurator preset with safe light/dark CSS variable overrides, style overrides, radius defaults, shared control tuning, project variant controls with exact swatches, Geist font-token mapping, docs header branding, and project header actions/search visibility, emitted as `theme/project-theme.ts` during template preparation
- **Theme packages** - `theme.package` points at a trusted overlay directory, local or fetched (see Theme packages from elsewhere), copied over the bundled template before metadata injection; packages can own `app/layout.tsx`, `app/docs/layout.tsx`, `components/theme-configurator.tsx`, `components/project-header-actions.tsx`, `theme/project-theme.ts`, CSS, and any other template file while Folio still supplies generated content and fallback YAML-driven theme modules

### SEO & Meta

- **OpenGraph + Twitter** - Meta tags in root layout; auto-generated 1200x630 social cards via the `opengraph-image.tsx` route
- **robots.txt** - Next.js metadata route; points at `llms.txt` and `llms-full.txt` through `# llms.txt: <url>` comment lines appended after the Next export; an LLM file switched off is deleted from the export
- **sitemap.ts** - Configurable via `project.url`; lists the per-page Markdown mirrors alongside the HTML routes
- **Markdown mirror discovery** - Every docs page declares its `_folio/markdown/<route>.md` mirror as a `text/markdown` alternate in the page head. The mirrors are lossy by construction, but preserve Mermaid source, useful simple-component labels, child prose, and authored code while stripping complex prop-only data; `folio serve` publishes `llms.txt` and `llms-full.txt` from the workspace public root just like a static build
- **Breadcrumbs** - Native Nextra, enabled by default
- **Favicon** - SVG favicon at `app/icon.svg` with the project monogram injected at build time (`__PROJECT_MONOGRAM__`), customizable via `favicon` in docs.yaml; a non-SVG custom favicon removes the template default

### i18n & Search

- **i18n** - Not available in this release: `i18n:` warns and is ignored
- **Navbar search** - Pagefind-backed docs search focuses from the navbar or `Cmd+K`/`Ctrl+K`; configurable with `search.enabled` and `search.placeholder`
- **Port conflict handling** - `folio serve` defaults to port 4321 and refuses an occupied port before it builds; `--kill-existing` stops only the process listening on the port, never its connected clients
- **Markdown docs underscore aliases** - Hand-written docs routes use kebab-case URLs, with underscore aliases generated for migrated paths such as `/docs/common_errors/`; API reference routes keep Python package/module underscores unchanged

### Landing Page & CLI

- **Landing section catalog** - `landing.sections` composes the homepage from reusable sections: features, routes, output, comparison, pipeline, install, stats, use cases, CTA, link grids, cells, mechanism (config YAML diff -> pipeline pill rail -> git-log strip, with `+ `/`- ` line tinting), and statement (accent-highlighted closer with CTAs). The funnel plate draws source tiles narrowing through one `folio build` node into the output tiles, each side a two-column block with alternating margins; a tile is a plain label plus an optional `icon` from the whitelist in `crates/folio-plugins/src/landing.rs` (unknown values drop), inputs may be `ghost` with a `chip`, and the retired `guarantees`, `caption` and `command_notes` keys warn and drop. Section hrefs are scheme-checked and degrade to defaults with a warning; an unknown section type or hero variant warns and lists the valid values.
- **Landing hero variants** - `docs-map | source-pipeline | build-pipeline | heartbeat`; `build-pipeline` is the split hero showing docstring -> `folio build` -> rendered reference
- **Interactive `folio init`** - Detects Python (`pyproject.toml`, `setup.py`, packages), Rust (`Cargo.toml`) and JavaScript (`package.json`) sources and reads the project name and version from their manifests. Wizard with a pixel-style banner, a rotating tips line refreshing in place during arrow-key prompts, a detected-settings panel with distinct row-label colors, pre-filled project metadata, inline arrow-key selectors, and `--yes` for non-interactive defaults; auto-detects the GitHub repo URL from `git remote origin`
- **Self-update** - `folio --update` is a root flag that runs alone (a subcommand next to it is a usage error): it follows `releases/latest` of `FOLIO_REPO` (default `pguijas/folio`; `FOLIO_RELEASES_URL` overrides the base for mirrors and tests) to the newest tag, compares it with the compiled version as a Cargo version and, when newer, downloads `folio-<triple>.tar.gz` (`.zip` on Windows) and `SHA256SUMS` with `curl`, verifies the digest, unpacks with `tar` in a staging directory beside the binary, runs the new binary's `--version` and renames it over the old one (Windows moves the old one aside as `.exe.old` and puts it back if the swap fails). A binary that is up to date or ahead of the latest release changes nothing; every failure before the swap leaves it untouched and removes the staging directory. Pinned by `crates/folio-cli/tests/update.rs` against a loopback release server whose downloads redirect like GitHub's.

### Deployment & CI/CD

- **Deploy guides** - Vercel, Netlify, GitHub Pages, and Docker (`docs/guide/deployment/`), with GitHub Actions workflows for build, deploy, and coverage gates
- **Branch preview deploys** - `folio init` writes a GitHub Pages preview workflow triggered by trusted `pull_request_target` PR activity; PR code builds in an unprivileged artifact job, the privileged deploy job consumes only the static preview artifact, previews deploy under `/previews/pr-<number>-<branch>/`, the production root is preserved through the internal `folio-pages-state` branch, and successful deploys update a sticky PR comment with the preview URL. The hidden `folio github-pages` group carries the steps (`compute-preview-path`, `prepare-artifact`, `copy-branch-preview`, `write-preview-metadata`, `write-previews-data`, `preserve-previews`, `prune-previews`, `save-state`, `verify-url`, `comment-preview`).
- **Preview index page** - `/previews/` is a real site route (`template/app/previews/`) reusing the docs shell (Nextra Layout/Navbar/Footer, sidebar page map, search, theme controls). It fetches `previews/previews.json` at runtime, written from per-preview `.folio-preview.json` sidecars, so the shell compiles once and only the data changes per deploy. Cards show PR number, title, branch, last commit, author avatar, repo/PR links, and last-updated time, newest first.
- **Branch preview garbage collection** - Every deploy prunes previews: it lists open PRs via `gh pr list`, computes their preview ids, and deletes any `/previews/<id>/` directory that does not belong to an open PR. No separate close-triggered workflow.
- **Deploy base path resolution** - `project.url` is metadata only; static base paths come from `FOLIO_BASE_PATH`, `deploy.base_path`, or GitHub Pages inference via `deploy.provider` / `FOLIO_DEPLOY_PROVIDER`
- **Pre-commit hook** - `folio coverage --min 80` as a pre-commit hook example

### Sidebar

- **Configured top-level ordering** - `nav` orders real root entries in `_meta.ts`; `Guide` groups authored docs, `API Reference` and `Source Code` name the generated `/api-reference/` tree, and unknown labels are ignored rather than creating dead routes
- **Sidebar metadata contract** - Nextra 4.x reads `_meta.ts` (not `.json`); the generated file preserves documented ordering and hides nested `index` pages with `{ "display": "hidden" }`; components split into sub-pages under `components/` with nested groups
- **Declared page order at any depth** - A directory at any depth declares its page order together with its children; a path nothing declares keeps the default order, and a declared page that does not exist yet is skipped rather than emitted.
- **Default-collapsed sidebar sections** - Generated guide and source-code groups start collapsed (`open: false` folder entries, leaf pages unchanged); `sidebar.default_collapsed: false` in docs.yaml expands them

### Known Issues

_None currently._

## Key Decisions

- Folio is one product. Folio Docs owns the engine and the extension interfaces; the virtual workspace coordinates its eleven crates, and `folio-cli` builds the `folio` binary.
- No Python anywhere in the product. Python is a documented language, read by a parser crate; no interpreter, bindings, or hybrid backend. The previous Python implementation is not a target to match.
- The specification is the fixtures and the Rust tests. A change to a shape they fix is a deliberate decision, stated in the PR, not a side effect of an implementation.
- Built-in integrations (landing, roadmap, openapi) are compiled in and activate through their own `docs.yaml` section. Project plugins return as sidecars in any language over NDJSON JSON-RPC on stdio; until then they are "Not available in this release".
- Distribution is `install.sh` from GitHub Releases, one archive per platform (PowerShell later); no PyPI, npm, or Homebrew for the binary.
- The frontend stays TypeScript: the Next.js/Nextra template needs Node.js 20.19+ and pnpm 10 for `folio build` and `folio serve`; the deployed site needs neither.
- Languages are parsers, not toolchains: a parser reads a grammar, never the language's SDK; `source.<language>` keys share the `paths` + `exclude` shape (`source.python.paths` + `source.python.exclude`, not a mixed list/mapping)
- Google-style and NumPy-style docstrings supported, auto-detected per docstring by default and forced with `source.python.docstring_style`
- Static export works with `output: 'export'`, `force-static` on route handlers, and Pagefind `postbuild`
- `project.url` feeds sitemap/canonical metadata only; do not derive local or static asset base paths from it
- Turbopack requires `resolveAlias` for `next-mdx-import-source-file`
- nextra-theme-docs 4.6.1 has a Zod v4 bug: `children` in LayoutPropsSchema is nonoptional but destructured out before validation; the schema is patched during template preparation
- `getPageMap("/docs")` is correct: returns children only, avoids a redundant "Docs" wrapper in the sidebar
- Markdown->MDX conversion must strip `<iframe>`/`<script>` tags, RST directives (`{eval-rst}`), escape `{}`, and convert `.md` links
- Custom template support is a full frontend ownership model: `template.path` selects a trusted local Next/Nextra-compatible workspace, while `template.params` is template-owned JSON data. Do not model this as a broad Folio color-token override layer.

## UI Design Style

- **Never use the mono face for labels.** JetBrains Mono (`font-mono`) is for version numerals and literal command text. Eyebrows, status words, section labels, layer strings, list ordinals and back-links all take the sans (Sora) at a small size, with weight, colour and letter-spacing doing the work. The uppercase `tracking-[0.14em]` treatment is separable from the face — keep the tracking, drop the mono. Count `font-mono` before shipping a component; more than two or three distinct roles means it is being abused.
- **A page names itself once.** No header rule repeating a name the body heading already carries. No `ViewHeaderRule` mono micro-label above a page that titles itself.
- **One background.** A page header sits on the page, not on its own `bg-card` slab behind a border — that split reads as two colours stacked. No decorative backdrops, and never an ornamental diagram above a real one.
- **Get presence from hierarchy, not size.** Plugin pages take the landing's register (`text-3xl sm:text-4xl font-bold`, up to `text-5xl`/`6xl` for one hero), never docs-body 15px and never `clamp()` display type. Make the in-progress thing dominant, compress what is settled, fade what is far off.
- **Reserve the accent** (`text-primary`) for what is happening now.
- **No UI that narrates itself** — no legends, no keyboard hints, no captions restating the drawing, no N-of-M ratios. Implement the keyboard, do not advertise it. If four states need a legend, fix the states.

## Working Style

- **Build in small steps, one part at a time.** Settle the header, then the skeleton, then the rows. Do not redesign a whole page in one pass.
- **Prototype inside the built site**, at a real route, never as standalone HTML: a mock rendered outside the site does not prove its type scale.
- **The bar is the page it replaces.** Keep the incumbent reachable at a second route while a redesign is open, and retire that route once the replacement lands.

## Writing Style

- **Go easy on the spaced em dash (" — ").** At most one per sentence, and never as a comma substitute inside a listing ("any depth — presets, packages, overlays — and ship it"). Prefer a colon, a comma, or a full stop. Overused, it reads as machine-generated text. A term–gloss label ("folio mcp — ask the docs from your editor") is fine; chains of them are not.
- **Undefined work gets few words.** Anything not yet defined, or not really iterated on, is stated simply and briefly. Detail is earned by the work actually done. Writing at length about an undecided piece presents it as more settled than it is, so say the little that is true and stop there.
- **Name a field without its colon.** In prose a config field is `output`, not `output:`. The colon belongs to the line that sets it (`output: "_site"`); inside an inline-code chip it reads as a parse error rather than as punctuation. A section named as a block keeps its colon (`roadmap:`, `landing:` in `docs.yaml`): there the colon is part of the token being named, not a stray mark after it.
- **User docs carry no work status.** They never say "skeleton", "stub" or "in progress"; a gated feature says exactly "Not available in this release" and nothing more about its state.

## Documentation Policy

- **Always document new features.** Every feature must be documented in the corresponding `docs/guide/` page and tracked in this file's "Product behaviour" section. No feature is done until it is documented.
- **No repo plans.** Do not commit implementation plans, specs, progress logs or planning notes; durable knowledge goes into code, tests and `docs/guide/`. If a durable decision matters, document the outcome in the product's guides or this file.
- **Review follow-ups.** Turn durable review findings into focused tests, relevant user-facing docs, or concise AGENTS.md project knowledge; do not keep separate backlog files in the repo.
- **Sidebar ordering.** New doc pages take their place in the declared sidebar order, which `folio-site` owns, inside the parent entry's children when the page sits in a subdirectory. No emojis in sidebar titles.

## Roadmap Policy

The `roadmap:` block in `docs.yaml` traces product direction. It says where
Folio is going and what a reader gets when it arrives. It is not a work log, a
release checklist, or a bug list.

- **The test.** Keep a line if it names something Folio does for its users, or a stance the product is moving toward. Cut it if it is Folio's own release hygiene, the repair of a promise already made, collateral about the product rather than the product, or a restatement of the phase title or summary. Generating the user's API changelog is direction; keeping Folio's own changelog is not.
- **Where the rest goes.** Maintenance, release work, and fixes are tracked in issues. Cutting a line does not drop the work; it stops selling it.
- **A phase sets the default; a line may correct it.** A phase's `status` is the done state of every line under it, which is right for a shipped phase and for one nobody has started. A release in progress is the exception: some of its work is finished and rendering all of it as pending understates what exists. Such a line is written as `- text: "…"` with `done: true` beside it, and that wins over the phase. Only mark a line done when it is actually built and you have checked; a mark nobody verified is worse than no mark. Work that shipped in an earlier release still belongs to that release — move it or cut it rather than marking it done under a later phase.
- **One release registry.** Every phase describes Folio Docs and carries `project: "docs"`.
- **A phase that is only a name stays a name.** Feature lines belong to a phase whose work is defined. A phase that has only been named gets a title, a layer, one summary sentence, and an explicit `features: []`. Write the empty list out: phases pass through unnormalized and the renderer reads `phase.features.length`, so omitting the key throws.
- **Register.** Phase summaries are one or two selling sentences. Feature lines are short outcome statements, not command lines or file paths.

## Git Policy

- **No AI attribution.** No `Co-Authored-By` or other AI co-author trailers in commit messages or PR bodies.
- **One change, one PR.** Branch from `develop` and open a PR against it, small enough to read in one sitting.

## Validation Policy

- **Always validate changes.** After implementing a feature or fix, verify it actually works:
  1. Run `cargo fmt --all --check`, `cargo clippy --workspace --all-targets -- -D warnings` and `cargo test --workspace`: all must pass
  2. Run `cargo run --release -p folio-cli -- serve --verbose` from the repository root: the unified build must complete without errors and the server must start without crashes
  3. Verify the feature works by curling key pages (`curl -s -o /dev/null -w "%{http_code}" http://localhost:4321/docs/...`)
  4. Check for regressions: existing pages still load (components, landing page, roadmap)
- **Never report a feature as done without validation.** Run the relevant tests and verify the behavior directly.

## Development & Testing

- **Primary**: Always develop and test against Folio's OWN docs (`docs/guide/` and the root `docs.yaml`). The Folio documentation site IS the product showcase; it must be the best presentation.
- **Template dev server**: `cd template && pnpm install && pnpm run dev` for UI/component work.
- **Full pipeline test**: `cargo run --release -p folio-cli -- serve --verbose` from the repository root builds Folio's own site from this repository.
- **Secondary test project**: p2pfl (https://github.com/p2pfl/p2pfl) is a real-world Sphinx project for migration checks. Folio's own docs come first.
