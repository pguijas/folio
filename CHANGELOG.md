# Changelog

All notable user-facing changes are recorded here. Folio follows semantic
versioning while the public CLI, configuration, and plugin contracts stabilize.

## 0.3.0-a1 — 2026-09-25

### Added

- Folio is one native Rust binary, `folio`, installed by `install.sh` from
  GitHub Releases. It replaces the `folio-docs` Python package and needs no
  Python; `folio build` and `folio serve` still render through the bundled
  Next.js template with Node.js 20.19+ and pnpm 10.
- The commands: `folio init`, `build`, `serve`, `coverage`, `clean` and
  `roadmap`, with the hidden `github-pages` group behind the preview
  workflows.
- Built-in integrations: landing page, roadmap and OpenAPI are compiled in and
  activate through their `docs.yaml` sections (`landing:`, `roadmap:`,
  `openapi:`).
- `public:` lists project-relative files served verbatim from the site root;
  a missing file, or a path outside the project or inside `.build/` or the
  output directory, fails the build.
- The Next.js template ships inside the binary and is materialised once under
  the user cache directory; `FOLIO_TEMPLATE_DIR` overrides it.
- `folio --update` replaces the binary with the latest GitHub release: it
  follows `releases/latest`, downloads the platform archive and `SHA256SUMS`,
  verifies the archive and swaps it in place with the installer's tools,
  `curl` and `tar`. `FOLIO_REPO` is shared with the installer;
  `FOLIO_RELEASES_URL` points it at a mirror.
- JavaScript sources: `source.javascript.paths` reads `.js`, `.mjs` and `.cjs`
  statically, without Node or a bundler. A module is named after its path
  (`utils/index.js` is `utils`), and the ESM and CommonJS exports of each file
  — functions, generators, classes with their getters, setters and static
  members, and constants — are published with their JSDoc under
  `api-reference/javascript/`. A setter beside its getter reads as the
  getter, which takes the setter's JSDoc when it has none of its own, and a
  static member that shares its name with an instance one has its own anchor.
  `node_modules` is never read and `.jsx` is skipped with a warning.
- Rust sources: `source.rust.paths` reads crates statically, without cargo or a
  Rust toolchain. Folio takes the crate name from `Cargo.toml`, follows the
  `pub mod` declarations from `lib.rs` or `main.rs`, and publishes public
  functions, structs, enums, traits, impl blocks and type aliases with their
  signatures, attributes and `///` comments under `api-reference/rust/`.
  `folio serve` watches `.rs` files, and a syntax error fails the build naming
  the file.
- `theme.package` takes a mapping naming a git repository, a revision and a
  `sha256:` digest, so a theme someone else published installs in four lines
  instead of a copied directory. The package is fetched into the user cache
  once, keyed by the digest, and the tree is verified against it before any
  build reads it. A local package still works exactly as before.
- A Troubleshooting guide for the messages a build most often stops or
  warns on — the environment check, `Config file not found`, unknown config
  keys, a stale incremental build, the port, broken links and the export
  log — each with its cause and the page that fixes it. Architecture gained the agent-facing surface it always
  emitted: `llms.txt`, the Markdown mirrors and `_folio/contract.json`.
- Agent-readable output from the same build as the HTML: `llms.txt`,
  `llms-full.txt`, a Markdown mirror per page, declared as a `text/markdown`
  alternate and listed in the sitemap, and the authoring contract at
  `/_folio/contract.json`. `folio serve` publishes the same files as a static
  build.
- Custom components (`components:`), custom templates (`template.path`),
  template overlays (`template.overlay_path`), project themes, Pagefind search,
  GitHub Pages branch previews and the MDX component library.
- `folio init` detects Rust (`Cargo.toml`) and JavaScript (`package.json`)
  projects as well as Python ones and writes their source roots; an existing
  `docs/` without Markdown gets an `index.md`.
- A typo in a top-level `docs.yaml` key or inside a core section is reported
  with the key it most likely meant; the keys inside `landing:`, `roadmap:`
  and `openapi:` are not checked yet, apart from a roadmap phase's. An unknown
  landing section type or hero variant warns.
- `theme.logo` shows in the docs navbar under the base path; a logo file that
  does not exist stops the build.
- A missing page is a themed 404 with a way back, at any depth, and a docs
  root without an index page opens the API reference.

### Changed

- Folio is now licensed under MIT (previously AGPL-3.0-only).
- Release archives ship THIRD-PARTY-NOTICES.md next to LICENSE, with the
  licenses of the bundled shadcn/ui components and of the code adapted from
  docstring_parser (MIT) and CPython (PSF License Version 2).
- Docs pages no longer show an "Edit this page" link, and the feedback link
  opens an issue in `project.repo`. Without a `repo`, neither link is shown;
  both used to point at Nextra's own repository.
- `folio serve` no longer builds the example projects under `docs/examples/`
  on its own: each one is a full nested site, and a cold `serve` of Folio's own
  repository spent minutes on four of them before the dev server came up. The
  `Previews` row says what was skipped, `folio serve --previews` builds them,
  a `DocPreview` whose example is not built says so in its place, and
  `folio build` still builds every example. The nested builds share the
  workspace's `node_modules` through a link instead of installing their own.
- A full build no longer rebuilds every preview example. Each published
  example carries the digest of its sources, the Folio version, the template
  and the base path it is built for; one whose digest still matches is left
  alone, and the `Previews` row reports what was rebuilt, what was unchanged
  and what was swept. An example is a
  whole nested build, so a warm build of Folio's own site stops paying for
  four of them.
- The `Dependencies` row names the phase it is in while it runs, rather than
  reading `checking pnpm` through a `pnpm install` that can take minutes.
- `folio serve` coalesces source events into one batch per save, reuses
  unchanged search-index work, and writes a generated file only when its bytes
  change.
- The repository is flat: the crates, the guides, the template and the theme
  sit at the root, and every crate keeps the tests and the fixtures those tests
  read. The `folio` binary is built by `folio-cli`.
- `Plugin::name` and `Plugin::config_keys` return owned values, and the
  extension-registry types serialize, so an extension can be described as data.
  Nothing loads dynamically yet; this is groundwork for the plugin seam.
- A theme package may no longer ship `package.json`, `pnpm-lock.yaml` or
  `pnpm-workspace.yaml`; a fetched one may not ship `next.config.mjs` either.
  A `components:` entry may no longer point outside the project directory.
- The theme package digest that keys the incremental build context is computed
  with a length-prefixed encoding, so it identifies one tree and only one. The
  first build after upgrading recomputes it once.
- Config keys are typed: string and boolean keys are checked, an explicit
  `null` for a string or boolean key is an error (a `null` `project.name`
  warns and falls back to `Untitled`, and `nav`, `public`, `template.path` and
  `source.docs` read `null` as absent), and each field reports its own
  message. A `plugins:` key warns and is ignored; the authoring contract's
  `configKeys` never lists it.
- `output:` is rejected when it names, or contains, a configured source
  directory or the repository's `.git`, or sits inside `.git`: the build
  removes the output directory before writing to it.
- The `nav` list orders real top-level entries and ignores unknown labels.
- Landing defaults name no `pip install` command and no `.py` kicker; an
  omitted `install:` renders no install block and the third default card reads
  "Built-in Integrations".
- The roadmap groups phases by `project`; the generated `/docs/roadmap/` page
  is a `# Roadmap` heading over the timeline.
- `--version`, the banner and generated metadata read `0.3.0-a1`.
- The landing `funnel` plate draws its sources and outputs as compact tiles —
  an icon and a plain label, in two columns with alternating margins — instead
  of path cards; `guarantees`, `caption` and `command_notes` are retired and
  warn.
- Relative links between pages resolve to their docs route when the page is
  written, a relative link whose `..` climbs out of the docs is reported as
  broken, and the link check reads the `href` props of components too.
- Underscore route aliases name the hyphenated route as their canonical (and
  are `noindex` when no `project.url` is set); they stay out of the search
  index, and so do the page actions.
- A `theme.preset` or `tune` value the configurator does not offer stops the
  build naming the nearest one; `dark_mode: false` keeps the site light with
  no mode controls.
- A roadmap phase the renderer cannot read fails before the build, naming the
  entry: a missing or non-string field, a `status` other than `shipped`,
  `active`, `next` or `later`, a key the phase does not take, or a `features:`
  that is not a list of strings and `text`/`done` mappings. A release links
  nowhere outside the roadmap.
- `folio serve` refuses a busy port before the build starts, `folio build
  --port` without `--open` is a usage error, and `folio clean` on a directory
  that does not exist is an error instead of nothing to clean; an output
  inside `.build/` is cleaned with it.
- `CodeGroup` labels its tabs from each block's language.
- API pages carry more of what the source documents: constants, re-exports,
  class attributes, notes and decorators render on the page and in
  `llms-full.txt`; warning, see also, references, todo and deprecated sections
  read as labelled prose; Sphinx roles such as `:class:` read as code; and
  every cross-reference lands on an id its page writes. The Markdown mirror of
  an API page keeps its class cards and parameter tables.
- A type in a Python or JavaScript signature links in the other ways it is
  commonly written: quoted (`'Config'`), under a dotted generic
  (`typing.Optional[Config]`), and in JSDoc as `Config[]`, `?Config`,
  `Config|null`, `Array<Config>` or `Promise<Config>`. A name defined only in
  another language's modules no longer links.
- Python: private names, undocumented dunders, overload stubs and property
  setters stay out of the reference, and a name defined twice is documented
  once, as its last definition.
- A page's inferred description reads a link as its text, so the page meta and
  `llms.txt` carry no raw Markdown and a broken link in the first paragraph is
  reported once.
- JavaScript: `module.exports` of a function documents the function, local
  declarations exported by name, default or object are documented, `{@link}`
  reads as its text and `options.name` parameters get their own row. A root
  of `.` reads neither `dist/`, `build/` nor the build output, TypeScript files
  are reported instead of skipped in silence, and when two files publish one
  module the first is read and the other is named in a warning.
- Rust: only plain `pub` items are documented, never `#[doc(hidden)]` or an
  impl of a private type or trait, and doc comments read as rustdoc renders
  them: untagged code blocks are Rust, hidden lines are dropped and intra-doc
  links keep their text.

### Removed

- The `folio board` command and the `kanban:` integration are gone: `folio`
  no longer reads `agents.yaml`, a `kanban:` section in `docs.yaml` warns and
  is ignored, and `KanbanBoard` is no longer a page component.
- `PageFeedback`, which no page rendered.
- A roadmap phase no longer takes `milestone`; a phase that still carries it
  fails the build.
- The landing `boards` section, which now warns and renders nothing, and the
  funnel's `board` icon, which is dropped.

### Security

- `folio init` quotes the project metadata it detects, from `pyproject.toml`
  and the git remote, into the generated `docs.yaml`, so a cloned repository
  cannot close the quote and append keys to the config Folio then trusts.
- `folio clean` never deletes a source root or anything that is not a
  directory, and `folio serve --kill-existing` stops only the process
  listening on the port.
- An `openapi.sources[].path` must stay inside the project, and each source's
  `route` is slugged segment by segment with no `.` or `..` segment; a route
  with no segment left takes the default.
- The project name, url and repository are escaped for each template file
  they land in.

### Not available in this release

- TypeScript sources, project plugins, i18n, and multi-version builds. The
  configuration guide and the pages that mention them carry the notice; the
  `i18n:` and `versions:` keys warn and are ignored, and the authoring
  contract does not offer them.
- `folio coverage` reads Python sources only, and refuses a config without
  them.
- MCP and a public IR export remain future work.
