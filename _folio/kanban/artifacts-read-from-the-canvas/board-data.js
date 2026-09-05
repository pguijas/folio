// board-data.js - snapshot of the real board, converted from the build's
// generated lib/kanban-data.ts. Loaded with a plain <script src>; these
// prototypes open over file:// where fetch() is blocked.
window.BOARD = {
  "title": "Development board",
  "columns": [
    {
      "id": "backlog",
      "title": "Backlog",
      "limit": null,
      "cards": [
        {
          "id": "pypi-parity-and-release-cadence",
          "title": "PyPI parity and release cadence",
          "description": "PyPI still has only 0.1.0 while the repo says 0.2.1, and no git tags exist, so what users install is not what the repo describes. Publish the current version, tag releases going forward, add a CHANGELOG, and document the release cadence so the published package and the repo stay in step.",
          "tags": [
            "release"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "high",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "",
          "artifacts": [],
          "criteria": [
            {
              "text": "current version published to PyPI",
              "done": false
            },
            {
              "text": "git tag created for each released version",
              "done": false
            },
            {
              "text": "CHANGELOG added and kept per release",
              "done": false
            },
            {
              "text": "release cadence documented",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "",
          "phaseTitle": "",
          "file": "board/cards/pypi-parity-and-release-cadence.md"
        },
        {
          "id": "serve-watches-docs-yaml-and-the-board",
          "title": "Serve watches docs.yaml and the board",
          "description": "The serve watcher only covers `python_sources` and `doc_sources`, so edits to\n`docs.yaml` or files under `board/` need a manual restart before they show up.\n\nWhy it is still open, stated so the next reader does not rediscover it: the\nwatcher is built on **one source file, one page**. Every handler recomputes\nexactly one route — a `.py` becomes its API page, a `.md` becomes its doc page.\n`watch_dirs` is literally `python_sources + doc_sources` and the filter admits\nonly those two suffixes under those two roots.\n\nA board card does not fit that shape. Forty-three cards collapse into one\nemitted module, `lib/kanban-data.ts`, and that module feeds the `/kanban` page,\nthe docs kanban page, the roadmap's milestone join, and the landing's board\nminiatures. There is no single route to recompute, so there was no obvious\nplace to put the handler. `docs.yaml` is further still: it can change the nav,\nthe sources, and which plugins load at all.\n\nAgreed shape (owner chose the general answer over a kanban special case):\n\n**A plugin declares what it watches.** A new hook: a plugin returns the paths\nit reads and the entry point that re-emits what it owns. The watcher asks the\nregistry instead of knowing what a kanban is. The kanban plugin returns its\nresolved board directory; the roadmap and landing plugins get the same\ntreatment for free, and the watcher stops growing one branch per plugin.\n\n**The board path comes from the plugin, not from a constant.** The board\ndirectory is whatever `kanban.source:` resolved to, which is not always\n`board/`. Hardcoding the name would work on this repository and quietly fail on\nevery other one.\n\n**`docs.yaml` is a full rebuild, and says so.** A config change can invalidate\nanything, so it does not pretend to be incremental. It debounces and rebuilds,\nand prints that it is doing so. A warm full rebuild measured 37s on this\nrepository, which is tolerable for a config edit and would not be tolerable per\nkeystroke — hence the targeted path above for cards.\n\n**Failure is visible and non-fatal.** A card that fails validation mid-edit\nmust print the error and leave the last good board served, not kill the\nwatcher thread. Editing a cardfile in an editor produces transient invalid\nstates on nearly every save.\n\nThis blocks nothing outright, but it is the difference between building\n`the-board-reads-as-a-tree` in an afternoon and building it 37 seconds at a\ntime: decomposing the board means editing `parent` across many cards and\nchecking the shape after each one.",
          "tags": [
            "dx"
          ],
          "assignee": [],
          "type": "feature",
          "size": "L",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "high",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "A plugin can declare the paths it reads and how to re-emit.",
              "done": false
            },
            {
              "text": "The watcher consults the plugin registry and holds no plugin-specific branch.",
              "done": false
            },
            {
              "text": "The watched board path is the one `kanban.source:` resolved, not a constant.",
              "done": false
            },
            {
              "text": "Editing a card under `board/` updates the served board without a restart.",
              "done": false
            },
            {
              "text": "Editing `docs.yaml` triggers a debounced full rebuild, announced in the output.",
              "done": false
            },
            {
              "text": "A card that fails validation prints the error and keeps the last good board served.",
              "done": false
            },
            {
              "text": "The watcher thread survives every failure above.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            },
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "given a shape — plugins declare what they watch; owner chose the general hook over a kanban special case",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/serve-watches-docs-yaml-and-the-board.md"
        },
        {
          "id": "theme-contract-for-plugin-surfaces",
          "title": "Theme contract for plugin surfaces",
          "description": "Presets, tokens, and theme packages must restyle plugin pages (landing, boards) the same way they restyle docs pages. Today plugin surfaces can drift from the active theme; this card defines the token contract plugin pages may rely on so a theme change propagates everywhere without plugin-specific overrides.",
          "tags": [
            "theming",
            "plugins"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "high",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "preset switch restyles landing, roadmap, and kanban with no plugin-specific overrides",
              "done": false
            },
            {
              "text": "contract documents the token set plugin pages may rely on",
              "done": false
            },
            {
              "text": "theme packages apply without forking templates",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/theme-contract-for-plugin-surfaces.md"
        },
        {
          "id": "agent-surfaces-technical-plan",
          "title": "Agent surfaces technical plan",
          "description": "The read path for agents, in three layers: formats (Markdown mirrors and llms.txt variants that any crawler or agent can consume), typed export (a versioned intermediate representation that tools can build on), and live surface (MCP and skills served from the static artifacts). The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.",
          "tags": [
            "spec"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "spec-correct llms.txt / lossless llms-full.txt",
              "done": false
            },
            {
              "text": "lossless per-page .md mirrors (today's mirrors strip component tags)",
              "done": false
            },
            {
              "text": "frontmatter descriptions feeding llms.txt",
              "done": false
            },
            {
              "text": "Accept: text/markdown content negotiation + rel=alternate links",
              "done": false
            },
            {
              "text": ".well-known discovery (skills, MCP card)",
              "done": false
            },
            {
              "text": "install.md aggregation",
              "done": false
            },
            {
              "text": "contextual menu (copy page as Markdown, open in agent tools) as static config",
              "done": false
            },
            {
              "text": "JSON-LD structured data + SEO/GEO meta controls",
              "done": false
            },
            {
              "text": "Content-Signal directives in robots.txt",
              "done": false
            },
            {
              "text": "folio-ir.json versioned language-aware schema",
              "done": false
            },
            {
              "text": "per-version IR sidecars",
              "done": false
            },
            {
              "text": "process_ir / emit_llm hookspecs",
              "done": false
            },
            {
              "text": "folio mcp (stdio, over static artifacts)",
              "done": false
            },
            {
              "text": "skill.md at the site root",
              "done": false
            },
            {
              "text": "charter plugin serving project contracts (PRODUCT.md, DESIGN.md, AGENTS.md; generic boilerplate excluded from auto-detection)",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/agent-surfaces-technical-plan.md"
        },
        {
          "id": "agpl-license-position",
          "title": "AGPL license position",
          "description": "Write and publish the license position: what AGPL means for generated sites, stated plainly so adopters do not have to guess. The core point is that the output of the generator belongs to its users — their generated site is theirs, and the position document says so explicitly.",
          "tags": [
            "release"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "",
          "artifacts": [],
          "criteria": [
            {
              "text": "position document written covering AGPL implications for generated sites",
              "done": false
            },
            {
              "text": "document states that generated output belongs to the user",
              "done": false
            },
            {
              "text": "position published where adopters can find it",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "",
          "phaseTitle": "",
          "file": "board/cards/agpl-license-position.md"
        },
        {
          "id": "api-portal-technical-plan",
          "title": "API portal technical plan",
          "description": "Technical plan for the API portal phase. The roadmap promises reference docs that stay truthful to the spec and legible to agents; this card holds the engineering work behind that promise, from the OpenAPI-derived page components through the diff engine that powers changelogs and CI gates, to the playground and doctest tooling that keep examples executable and current.",
          "tags": [
            "spec"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.8",
          "artifacts": [],
          "criteria": [
            {
              "text": "ParamField / ResponseField / Expandable component family",
              "done": false
            },
            {
              "text": "per-endpoint OpenAPI pages with pinned examples",
              "done": false
            },
            {
              "text": "IR-diff engine + api-diff.json",
              "done": false
            },
            {
              "text": "generated API changelog + release notes",
              "done": false
            },
            {
              "text": "breaking-change CI gate",
              "done": false
            },
            {
              "text": "OpenAPI playground",
              "done": false
            },
            {
              "text": "SDK snippets cross-linked to parsed symbols",
              "done": false
            },
            {
              "text": "folio check --examples doctest gate",
              "done": false
            },
            {
              "text": "Visibility + Prompt components",
              "done": false
            },
            {
              "text": "RSS feeds on changelog pages",
              "done": false
            },
            {
              "text": "AsyncAPI support",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "api-portal-diff",
          "phaseTitle": "API Portal",
          "file": "board/cards/api-portal-technical-plan.md"
        },
        {
          "id": "broken-links-and-a11y-checks",
          "title": "Broken links and a11y checks",
          "description": "folio check gains internal link and anchor checking, optional external link checking, and an accessibility audit covering image alt text and contrast. The checks are wired in as a build gate so a broken link or a missing alt attribute fails the build instead of shipping.",
          "tags": [
            "quality"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "internal link and anchor checking in folio check",
              "done": false
            },
            {
              "text": "optional external link checking",
              "done": false
            },
            {
              "text": "image alt and contrast audit",
              "done": false
            },
            {
              "text": "checks wired as a build gate",
              "done": false
            },
            {
              "text": "docs quality gates GitHub Action (links, coverage, style linting)",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/broken-links-and-a11y-checks.md"
        },
        {
          "id": "comparison-pages",
          "title": "Comparison pages",
          "description": "Criteria-first honest comparison pages, shipped on the docs site. This is the one context where competitor names are allowed; everywhere else the copy stands on its own. The comparison leads with the criteria, not the verdict, and every claim made about a competitor or about Folio is verifiable, linked to documentation, a spec, or a reproducible check, so the pages survive scrutiny from the compared parties.",
          "tags": [
            "launch"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.7",
          "artifacts": [],
          "criteria": [
            {
              "text": "Comparison pages published on the docs site",
              "done": false
            },
            {
              "text": "Criteria are stated first and applied uniformly to Folio and competitors",
              "done": false
            },
            {
              "text": "Every claim is verifiable via a link to documentation, a spec, or a reproducible check",
              "done": false
            },
            {
              "text": "Competitor names appear only on these pages, nowhere else in the site copy",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "launch",
          "phaseTitle": "Public Beta",
          "file": "board/cards/comparison-pages.md"
        },
        {
          "id": "demo-and-readme",
          "title": "Demo and README revamp",
          "description": "A short demo that builds a real repository's docs and board live, with no staged fixtures, plus a README revamp that carries the docs-and-boards story. The demo shows the end-to-end path from a plain repository to a published docs site and board in one build; the README leads with that same story so the first thirty seconds on the repository page and the first thirty seconds of the demo tell the same thing.",
          "tags": [
            "launch"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.7",
          "artifacts": [],
          "criteria": [
            {
              "text": "Demo builds docs and board from a real repository, recorded end to end",
              "done": false
            },
            {
              "text": "Demo is short enough to watch in one sitting without cuts that hide steps",
              "done": false
            },
            {
              "text": "README rewritten to lead with the docs-and-boards story",
              "done": false
            },
            {
              "text": "README and demo tell the same story with no divergence in claims",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "launch",
          "phaseTitle": "Public Beta",
          "file": "board/cards/demo-and-readme.md"
        },
        {
          "id": "ecosystem-technical-plan",
          "title": "Plugin catalog technical plan",
          "description": "Technical plan for the Public Beta catalog work. The roadmap promises a plugin catalog outsiders can publish into; this card holds the engineering work behind that promise, covering the plugin catalog and hookspecs that let outsiders extend the system, the eval tooling that keeps docs honest at scale, and the git sync that connects the board to the rest of a team's infrastructure.",
          "tags": [
            "spec"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.7",
          "artifacts": [],
          "criteria": [
            {
              "text": "plugin catalog + scaffold + three flagship external plugins",
              "done": false
            },
            {
              "text": "register_language hookspec",
              "done": false
            },
            {
              "text": "agent-docs eval benchmark (folio eval)",
              "done": false
            },
            {
              "text": "git sync",
              "done": false
            },
            {
              "text": "i18n plugin for localized sites",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "launch",
          "phaseTitle": "Public Beta",
          "file": "board/cards/ecosystem-technical-plan.md"
        },
        {
          "id": "folio-score-cli",
          "title": "Folio score CLI",
          "description": "An open agent-readiness audit runnable against any docs site, whether given a URL or a local directory. It checks llms.txt presence and spec-correctness, .md mirrors, well-known discovery paths, sitemap, and metadata, and produces an honest score against published criteria — no grading on a curve toward Folio-built sites. Exit codes make it usable in CI. It doubles as the migration hook: score your current site, see what is missing, then migrate.",
          "tags": [
            "launch"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.7",
          "artifacts": [],
          "criteria": [
            {
              "text": "Runs against both a URL and a local directory",
              "done": false
            },
            {
              "text": "Checks llms.txt presence and correctness against the spec",
              "done": false
            },
            {
              "text": "Checks .md mirrors, well-known discovery paths, sitemap, and metadata",
              "done": false
            },
            {
              "text": "Scoring criteria are published and the score is reproducible from them",
              "done": false
            },
            {
              "text": "Non-zero exit code on failing score so it works as a CI gate",
              "done": false
            },
            {
              "text": "Works against docs sites not built with Folio",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "launch",
          "phaseTitle": "Public Beta",
          "file": "board/cards/folio-score-cli.md"
        },
        {
          "id": "hidden-pages-and-ignore-rules",
          "title": "Hidden pages and ignore rules",
          "description": "Two levels of page visibility: a hidden: frontmatter flag that keeps a page out of nav and search while leaving it reachable by URL, and an ignore file that excludes content from the build entirely. Visibility is decided at build time, never client-side, so hidden content is not merely styled away.",
          "tags": [
            "core"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "hidden: frontmatter removes a page from nav and search but keeps it reachable by URL",
              "done": false
            },
            {
              "text": "ignore file excludes matched content from the build entirely",
              "done": false
            },
            {
              "text": "visibility decided at build time, never client-side",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/hidden-pages-and-ignore-rules.md"
        },
        {
          "id": "languageprofile-parser-seam",
          "title": "LanguageProfile parser seam",
          "description": "Introduce a LanguageProfile abstraction and a parser registry in core, with Python as the only profile for now. The IR carries language identity, and registering a second profile touches only the registry — nothing else in the pipeline changes. The docs state the contract plainly: new languages are parsers, not toolchains.\n\nThat contract is the constraint, and it rules out the obvious route for every language after TypeScript. Reading Rust through `rustdoc --output-format json` needs a Rust toolchain, Go through `go/doc` needs Go, Java through `javadoc` needs a JDK — each one turns \"add a language\" into \"install an ecosystem\", which is the objection Folio exists to answer for Sphinx-era maintainers. TypeScript is the exception: its compiler is reachable through the Node runtime Folio already requires.\n\nSo the profile for everything else reads a grammar, not an SDK. That keeps the same posture Python already has: `ast` reads annotations as written and infers nothing, and a grammar-based profile behaves identically. The cost is honest and should be written down rather than discovered — a grammar gives syntax, not semantics, so a type that is only knowable by inference will not appear. For reference pages built from signatures and doc comments, that is the same trade Python already makes.",
          "tags": [
            "core",
            "languages"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.5",
          "artifacts": [],
          "criteria": [
            {
              "text": "LanguageProfile and parser registry exist in core with Python as the only profile",
              "done": false
            },
            {
              "text": "IR carries language identity",
              "done": false
            },
            {
              "text": "registering a second profile touches only the registry",
              "done": false
            },
            {
              "text": "docs state the contract: new languages are parsers, not toolchains",
              "done": false
            },
            {
              "text": "the grammar-versus-SDK decision is recorded, with the syntax-not-semantics limit stated",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            },
            {
              "date": "2026-07-29",
              "actor": "claude",
              "ref": "",
              "note": "roadmap 0.5 now names Rust, Go, then the JVM and C#. Recorded why each one's own doc tooling is off the table under the no-toolchain contract, and that the profile reads a grammar instead.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "more-languages",
          "phaseTitle": "More Languages",
          "file": "board/cards/languageprofile-parser-seam.md"
        },
        {
          "id": "migrations-technical-plan",
          "title": "Migrations technical plan",
          "description": "One-command imports with honest reports: importers for the major documentation ecosystems that convert what they can, report what they could not, and leave the user with a working site rather than a half-migration. The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.",
          "tags": [
            "spec"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.6",
          "artifacts": [],
          "criteria": [
            {
              "text": "mkdocs.yml importer",
              "done": false
            },
            {
              "text": "Mintlify docs.json importer",
              "done": false
            },
            {
              "text": "Sphinx conf.py reader",
              "done": false
            },
            {
              "text": "intersphinx objects.inv consume + emit",
              "done": false
            },
            {
              "text": "Read the Docs recipe",
              "done": false
            },
            {
              "text": "parser trust parity (inherited members, __all__, overloads)",
              "done": false
            },
            {
              "text": "Material-familiar theme preset",
              "done": false
            },
            {
              "text": "redirects config, generated by importers",
              "done": false
            },
            {
              "text": "published migration case study",
              "done": false
            },
            {
              "text": "multi-product navigation",
              "done": false
            },
            {
              "text": "multi-repo sites",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "migrations",
          "phaseTitle": "Migrations",
          "file": "board/cards/migrations-technical-plan.md"
        },
        {
          "id": "preflight-environment-checks",
          "title": "Preflight environment checks",
          "description": "Check node, npm, network access, and paths before starting a build, and fail with instructions rather than tracebacks. A missing or wrong-version dependency should produce a message that names the problem and the fix, not a raw stack trace from deep inside the build.",
          "tags": [
            "dx"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "",
          "artifacts": [],
          "criteria": [
            {
              "text": "node, npm, network, and path checks run before the build starts",
              "done": false
            },
            {
              "text": "each failed check prints what is wrong and how to fix it",
              "done": false
            },
            {
              "text": "no traceback shown for a failed preflight check",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "",
          "phaseTitle": "",
          "file": "board/cards/preflight-environment-checks.md"
        },
        {
          "id": "project-os-technical-plan",
          "title": "Project OS technical plan",
          "description": "The write path for agents plus board maturity: agents move from reading the site to acting on it through a write-MCP and a generated authoring contract, while the board grows the metadata, views, and generated-roadmap machinery it needs to serve as the project's operating layer. The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.",
          "tags": [
            "spec"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "write-MCP for boards (move_card / update_phase via PR)",
              "done": false
            },
            {
              "text": "Folio skill for Claude Code / Hermes / OpenClaw",
              "done": false
            },
            {
              "text": "generated authoring contract per project",
              "done": false
            },
            {
              "text": "card pages",
              "done": false
            },
            {
              "text": "session artifacts render as site pages, attached to the card they moved, in search and llms.txt",
              "done": false
            },
            {
              "text": "board drag and drop persists as a commit to the board's branch",
              "done": false
            },
            {
              "text": "board webhooks / CI sync (issues to cards and back)",
              "done": false
            },
            {
              "text": "metadata + filtering contract (unknown references fail the build, unknown values warn)",
              "done": false
            },
            {
              "text": "saved views",
              "done": false
            },
            {
              "text": "roadmap generated from the cards",
              "done": false
            },
            {
              "text": "folio artifact single-page mode",
              "done": false
            },
            {
              "text": "ADR plugin",
              "done": false
            },
            {
              "text": "reusable snippets with variables",
              "done": false
            },
            {
              "text": "automation recipes running the user's own agent in CI",
              "done": false
            },
            {
              "text": "edit-this-page + file-an-issue links",
              "done": false
            },
            {
              "text": "agents report doc issues through the MCP",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/project-os-technical-plan.md"
        },
        {
          "id": "public-launch-plan",
          "title": "Public launch plan",
          "description": "Coordinate the public launch around the first tagged PyPI release: an announcement post, a Hacker News submission, and posts to Python community channels (real names, no abbreviations). The launch carries a single one-sentence story (docs and boards from one build, open source, agent-ready) and every channel repeats it verbatim. Nothing ships to any channel before the tagged release is live and installable.",
          "tags": [
            "launch"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.7",
          "artifacts": [],
          "criteria": [
            {
              "text": "The one-sentence story is written down and used verbatim across all launch materials",
              "done": false
            },
            {
              "text": "Announcement post drafted, reviewed, and published",
              "done": false
            },
            {
              "text": "Hacker News submission prepared and submitted on launch day",
              "done": false
            },
            {
              "text": "Python community posts published with real community names spelled out, no abbreviations",
              "done": false
            },
            {
              "text": "All launch materials go out coordinated with the first tagged PyPI release, not before",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "launch",
          "phaseTitle": "Public Beta",
          "file": "board/cards/public-launch-plan.md"
        },
        {
          "id": "readable-build-failures",
          "title": "Readable build failures",
          "description": "Every build failure caused by user input should name the file or config key at fault and state the fix. Raw stack traces are reserved for genuine internal errors; a typo in docs.yaml or a bad frontmatter field must never surface as a traceback.",
          "tags": [
            "dx"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "",
          "artifacts": [],
          "criteria": [
            {
              "text": "user-error failures name the file or config key and the fix",
              "done": false
            },
            {
              "text": "no raw stack traces for user errors",
              "done": false
            },
            {
              "text": "internal errors remain distinguishable from user errors",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "",
          "phaseTitle": "",
          "file": "board/cards/readable-build-failures.md"
        },
        {
          "id": "starter-templates",
          "title": "Starter templates",
          "description": "folio init scaffolds a new project from a small set of maintained templates: library, CLI tool, and API service. Each template is kept deliberately small, is maintained alongside the core, and builds green out of the box — a fresh init followed by a build must succeed with no edits.",
          "tags": [
            "launch"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.7",
          "artifacts": [],
          "criteria": [
            {
              "text": "folio init offers the library, CLI tool, and API service templates",
              "done": false
            },
            {
              "text": "Each template builds green immediately after init with no edits",
              "done": false
            },
            {
              "text": "Templates are maintained in-repo so core changes that break them fail CI",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "launch",
          "phaseTitle": "Public Beta",
          "file": "board/cards/starter-templates.md"
        },
        {
          "id": "typescript-technical-plan",
          "title": "TypeScript technical plan",
          "description": "Technical plan for TypeScript, the first language of the More Languages phase. The roadmap promises that new languages arrive as parsers, not new toolchains; this card holds the engineering work behind that promise, extending the IR contract with language-aware fields, wiring a pinned typedoc extractor into the same pipeline the Python path uses, and keeping the feature gated until the contract has survived real public exposure.",
          "tags": [
            "spec"
          ],
          "assignee": [],
          "type": "plan",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.5",
          "artifacts": [],
          "criteria": [
            {
              "text": "typedoc --json extractor (pinned, versioned contract)",
              "done": false
            },
            {
              "text": "ModuleIR.language / ClassIR.kind fields",
              "done": false
            },
            {
              "text": "per-language cross-references + route namespacing",
              "done": false
            },
            {
              "text": "cross-language llms.txt / ir.json",
              "done": false
            },
            {
              "text": "Twoslash inline type info",
              "done": false
            },
            {
              "text": "golden-fixture TypeScript test suite",
              "done": false
            },
            {
              "text": "gated experimental until the IR contract survives public exposure",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "more-languages",
          "phaseTitle": "More Languages",
          "file": "board/cards/typescript-technical-plan.md"
        },
        {
          "id": "versioned-docs-graduation",
          "title": "Versioned docs graduation",
          "description": "The versions: config references tags v0.2.0, v0.1.0, and v0.0.1 that do not exist in git, so versioned builds rest on references that cannot resolve. Create the real tags and graduate versioned builds out of experimental once they build against tags that actually exist.",
          "tags": [
            "release"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.5",
          "artifacts": [],
          "criteria": [
            {
              "text": "git tags exist for every version referenced in versions: config",
              "done": false
            },
            {
              "text": "versioned builds resolve against real tags",
              "done": false
            },
            {
              "text": "versioned docs graduated out of experimental",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "more-languages",
          "phaseTitle": "More Languages",
          "file": "board/cards/versioned-docs-graduation.md"
        },
        {
          "id": "rust-fast-path-for-source-reading",
          "title": "Rust fast path for source reading",
          "description": "Move the hot parsing passes to a native implementation for a large build-time speedup. Before any of it is written, the premise needs a measurement, because on this repository it does not hold: a full parse of Folio's own 45 modules takes 0.105s, while a cold `folio serve` takes about four minutes to reach a served page. The template phase accounts for nearly all of that, so a native parser would save a tenth of a second.\n\nThe idea stays open because the premise may hold on inputs Folio has not been pointed at yet: a repository with thousands of modules, or the Markdown and MDX passes, or the link resolution and search index passes. Profile a large repository first and publish per-phase numbers. Build native code only for a phase the numbers convict.",
          "tags": [
            "dx",
            "core"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-27",
          "milestone": "0.5",
          "artifacts": [],
          "criteria": [
            {
              "text": "per-phase build timings published for a large repository, not just this one",
              "done": false
            },
            {
              "text": "the dominant phase named with a number behind it",
              "done": false
            },
            {
              "text": "a recorded decision on which phase, if any, justifies a native implementation",
              "done": false
            },
            {
              "text": "if none does, the card closes and the numbers are the reason",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-27",
              "actor": "claude",
              "ref": "",
              "note": "carded on request. Measured `parse_python_directory` at 0.105s for 45 modules against a roughly four-minute cold serve, so the current bottleneck is the template phase rather than source reading.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "more-languages",
          "phaseTitle": "More Languages",
          "file": "board/cards/rust-fast-path-for-source-reading.md"
        },
        {
          "id": "a-parent-cycle-fails-the-build",
          "title": "A parent cycle fails the build",
          "description": "`_validate_relations` checks two things about `parent`: that it names a card on\nthis board, and that it is not the card itself. It does not check that following\nthe chain ends. Two cards that name each other, or any longer ring, pass\nvalidation and ship.\n\nThis has been harmless because nothing walks the chain. The moment a view\nrenders the tree, a ring is an infinite descent: the page hangs, and the build\nthat produced it reported success. The bug has to be fixed before anything\nreads `parent` recursively, not after a board bricks itself.\n\nAgreed shape:\n\n**The rule.** Following `parent` from any card must terminate. A ring of any\nlength raises the same way a dangling parent does — a build error naming the\ncards in the cycle, in the order they point, so the reader can see which link to\ncut. Consistent with the rest of the topology checks, which fail the build\nrather than warn: an unresolvable board is not a board.\n\n**Where.** `_validate_relations` in `kanban_board.py`, beside the checks it\nalready makes. One pass over the cards, following each chain with a visited set;\na board of a few thousand cards is not worth an algorithm.\n\n**The self-parent case folds in.** A card naming itself is a cycle of length\none. Keep its message, which is clearer than the general one, and let the\ngeneral check catch everything longer.\n\n`blocked_by` is a list and can also form a ring. It is not walked recursively by\nanything and is out of scope here; say so in the code rather than leaving the\nasymmetry unexplained.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "bug",
          "size": "S",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "`a → b → a` fails the build with an error naming both cards.",
              "done": false
            },
            {
              "text": "A longer ring fails the same way, naming every card in it.",
              "done": false
            },
            {
              "text": "A card naming itself keeps its existing, more specific message.",
              "done": false
            },
            {
              "text": "A deep but acyclic chain still builds.",
              "done": false
            },
            {
              "text": "`folio kanban check` surfaces the failure as a red gate, not a warning.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created; gap found while designing the tree view",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/a-parent-cycle-fails-the-build.md"
        },
        {
          "id": "a-parent-says-what-it-breaks-into",
          "title": "A parent says what it breaks into",
          "description": "A tree that only indents is an outline. What makes decomposition useful is the\nparent answering two questions without being opened: how much of this is done,\nand does any of it disagree with where the parent sits.\n\nAgreed shape:\n\n**The rollup.** A parent carries how many cards sit beneath it — the whole\nsubtree, not just direct children, because a parent of two epics of five is not\na parent of two — and how far they have got. The measure is which columns the\ndescendants are in, and it must be legible when they are all in the same one:\nthe prototype's bar was full and its fraction read `0/10`, which is truthful and\nreads as a contradiction. Whatever form this takes, state what the number counts\nin the row itself rather than in a tooltip.\n\n**The disagreement, named.** A child whose column differs from its parent's is\nmarked on its row, and the count of such rows appears in the toolbar. Today the\nboard has exactly one: `theme-contract-for-plugin-surfaces` sits in Backlog\nunder a parent in In review. That is not an error and must never be styled as\none. It is the ordinary case of a plan that has started in parts, and the\nreason the table earns its place next to the columns is that it can show it at\nall.\n\n**The card knows both directions.** In both views, a card links to its parent\nand lists its children. A child says what it is part of; a parent says what it\nbreaks into. Following either is one press.\n\n**Inherited values are marked as inherited.** When a collapsed row shows\nsomething drawn from below it, the register differs from a value the card owns,\nand hovering says where it came from. This was the real defect the prototype's\nverification pass found and it is the easiest one to reintroduce.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [
            "the-table-draws-one-row-per-card"
          ],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "A parent shows its whole-subtree count, not just direct children.",
              "done": false
            },
            {
              "text": "The progress measure is legible when every descendant is in one column.",
              "done": false
            },
            {
              "text": "What the number counts is stated in the row, not only on hover.",
              "done": false
            },
            {
              "text": "A child in a different column than its parent is marked, and the total is",
              "done": false
            },
            {
              "text": "The marker does not read as an error.",
              "done": false
            },
            {
              "text": "A card links to its parent and to its children in both views.",
              "done": false
            },
            {
              "text": "A derived value never renders in the same register as an own value.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/a-parent-says-what-it-breaks-into.md"
        },
        {
          "id": "the-board-component-splits-into-modules",
          "title": "The board component splits into modules",
          "description": "`kanban-board.tsx` is 4312 lines and holds one view. It carries the card\ncontract, the staging overlay and its YAML writer, the whole filter language\n(tokenizer, parser, matcher), the composer rail and its four control types, the\ncard face, the dialog, and the board itself. Adding a second view to that file\ndoes not add a view, it doubles a file that is already the largest thing in the\ntemplate.\n\nSplit it before the table lands, not after. A refactor that follows a feature\nships the feature twice.\n\nAgreed shape:\n\n**The seams are already drawn.** The file's own section comments name them. The\nsplit follows those lines rather than inventing new ones:\n\n- the card contract and the board identity helpers;\n- the filter language: tokenize, parse, match, count — it has no React in it at\n  all and is the obvious first module out;\n- the staging overlay: clone, diff, apply, and the YAML and move-command\n  writers;\n- the composer rail and its controls;\n- the card face and the dialog;\n- the board view itself.\n\n**No behaviour changes in this card.** Pure moves plus the imports they force.\nThe test suites that cover the filter language and the YAML writer must pass\nuntouched — if a test has to change, the move was not pure and the change\nbelongs in its own card.\n\n**One incidental fix.** `kanban-board.tsx:1431` writes a cache-key separator as\na literal NUL byte inside a template string. It works, and it makes the file\nbinary to `grep`, `diff`, and anything else that sniffs content — every search\nof this file needs `grep -a` today. Write it `\\0`.\n\nThe point of the split is not tidiness. It is that the next three cards each\ntouch one of these seams, and they should be able to touch one without holding\nthe other five in view.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "chore",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "No module exceeds roughly 800 lines.",
              "done": false
            },
            {
              "text": "The filter language module imports no React.",
              "done": false
            },
            {
              "text": "Every existing kanban test passes without modification.",
              "done": false
            },
            {
              "text": "The board renders identically before and after: same markup, same",
              "done": false
            },
            {
              "text": "`grep` reads the sources without `-a`.",
              "done": true
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created; NUL byte found while grepping the file for the tree work",
              "href": ""
            },
            {
              "date": "2026-08-23",
              "actor": "codex",
              "ref": "feat/artifact-board-poc",
              "note": "replaced the raw NUL with an escaped separator; the component is UTF-8 text again, while the larger module split remains open",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/the-board-component-splits-into-modules.md"
        },
        {
          "id": "the-cli-prints-the-tree",
          "title": "folio kanban show prints the tree",
          "description": "`folio kanban show` prints a flat table. If the site nests and the CLI does not,\nthe decomposition is visible to people and invisible to agents — and the CLI is\nthe surface agents actually operate this board through. The board's whole claim\nis that humans and agents work the same files through the same commands; a\nstructure only one of them can see breaks it.\n\nAgreed shape:\n\n**`show` nests by default.** Children indent under their parent, roots in the\nexisting order. The columns the table already prints stay as they are; only the\nid column gains indentation. A board where no card sets `parent` prints exactly\nwhat it prints today, so this changes nothing until decomposition is used.\n\n**A flat reading stays available.** `--flat` prints the current output, because\npiping into `grep` and `awk` wants one card per line with no leading structure,\nand a tool that only offers the pretty form is a tool you fight.\n\n**One subtree.** `folio kanban show --under <id>` prints that card and\neverything beneath it. This is the command an agent runs when it picks up an\nepic, and the reason to have it is that `parent:<id>` as a filter gives only\ndirect children, not the subtree.\n\n**Cycles do not hang the CLI.** The build already refuses a ring once\n`a-parent-cycle-fails-the-build` lands, but `show` reads boards it did not\nbuild. It carries its own visited set and prints a legible complaint rather\nthan spinning.\n\n**The skill file teaches the gesture.** `board/SKILL.md` documents the card\nschema and the session protocol; `parent` is listed there as a field with no\nworked example of decomposing anything. Add the example, and say plainly when a\ncard should become a parent instead of growing a longer criteria list.",
          "tags": [
            "plugins",
            "kanban",
            "cli"
          ],
          "assignee": [],
          "type": "feature",
          "size": "S",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "`show` indents children under parents by default.",
              "done": false
            },
            {
              "text": "`--flat` reproduces today's output byte for byte.",
              "done": false
            },
            {
              "text": "`--under <id>` prints the full subtree of that card.",
              "done": false
            },
            {
              "text": "`--under` with an unknown id fails with a message naming the id.",
              "done": false
            },
            {
              "text": "A board with a parent ring prints a complaint and exits, and does not hang.",
              "done": false
            },
            {
              "text": "A board where no card sets `parent` prints what it prints today.",
              "done": false
            },
            {
              "text": "`SKILL.md` shows a worked decomposition.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/the-cli-prints-the-tree.md"
        },
        {
          "id": "the-table-draws-one-row-per-card",
          "title": "The table draws one row per card",
          "description": "The table itself: the row grammar, the tree column, and the columns you read\ndown. This is the card the whole view is made of.\n\nAgreed shape:\n\n**One row per card, always.** No summarized rows, no \"and 4 more\". 35 cards is\n35 rows. A reading whose row count does not match the card count is a reading\nyou cannot trust.\n\n**The first column is the tree.** Indentation carries depth; a disclosure\ntriangle sits on any card with children and nothing sits where a card has none,\nso a leaf is not a parent with an empty box. The card id renders beside the\ntitle in mono, right-aligned in the column, because the id is what every CLI\ncommand takes and copying it out of the view is the common gesture.\n\n**The other columns are fields.** Status, milestone, type, size, assignee. Each\none read straight down as a single scannable column, which is the whole reason\nthis view exists and the one thing the column board cannot do. Absent values\nrender as nothing, not as a dash: 32 of 35 cards have no priority today and a\ncolumn of dashes is noise pretending to be data.\n\n**Status is the control.** The status cell is where a move is staged, using the\nsame overlay and the same `folio kanban move` output as the columns. No second\nmechanism.\n\n**Sorting keeps the tree intact.** Sorting by a column sorts siblings within\ntheir parent; a child never leaves its parent. A sort that flattens the tree is\na different view, and if that is ever wanted it is a different card.\n\n**Collapse is cheap and total.** A row collapses, and expand-all and\ncollapse-all are one press each. Collapse state survives filtering.\n\n**Keyboard.** Up and down move between rows, left and right collapse and\nexpand, and focus is visible. A table of 35 rows that needs a mouse is a table\nthat failed.\n\nWatch for, found in the prototype: when a collapsed parent shows a value\nderived from its hidden children, that value must not be drawn in the same\nregister as a value the card owns. The prototype rendered an inherited size as\nif the card carried it, which is a lie the reader has no way to detect.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "L",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [
            "the-table-is-a-second-view",
            "a-parent-cycle-fails-the-build"
          ],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "Row count equals card count, at every filter and collapse state.",
              "done": false
            },
            {
              "text": "Depth renders correctly at three levels.",
              "done": false
            },
            {
              "text": "A card with no children draws no disclosure control.",
              "done": false
            },
            {
              "text": "Empty fields render as empty, not as a placeholder glyph.",
              "done": false
            },
            {
              "text": "Staging a move from a status cell produces the same command as the board.",
              "done": false
            },
            {
              "text": "Sorting any column leaves every child under its parent.",
              "done": false
            },
            {
              "text": "Full keyboard navigation with visible focus.",
              "done": false
            },
            {
              "text": "A derived value is visually distinct from an own value.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/the-table-draws-one-row-per-card.md"
        },
        {
          "id": "the-table-is-a-second-view",
          "title": "The table is a second view, not a second page",
          "description": "The board has one view and no concept of having more than one. Before the table\ncan be drawn, the page has to be able to hold two readings of the same data and\nlet you change which one you are looking at without losing your place.\n\nTwo pages was the alternative and it loses the thing that makes this worth\nbuilding: you narrow the board to a filter, you want the same set as a tree, and\na second route means retyping the filter. One page, two renderings, one filter.\n\nAgreed shape:\n\n**The switch.** A two-position control in the filter bar, beside the filter\nglyph that already opens the composer. Board and Table, the current one marked.\nIt is a control on the bar because the bar is what both views share.\n\n**The URL carries it.** `?view=table` alongside the existing `?q=`, written the\nsame way the query already writes itself — on a pause, not on every keystroke.\nA link to a filtered tree is then just a link, which is what the board's own\nprotocol asks for: every report ends in something the reader can click.\n`?view=board` and an absent parameter both mean the columns.\n\n**What crosses the switch.** The filter and its results, the staged moves and\ntheir count, and the selected card. Changing the view must never discard staged\nwork: the overlay is keyed by the column set and knows nothing about views, and\nit stays that way.\n\n**What does not cross.** Collapse state belongs to the tree and does not exist\nin the columns. Scroll position is per view.\n\n**The board is untouched.** This card adds the switch, the URL parameter, and\nthe seam a second view plugs into. It does not change a pixel of the columns.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [
            "the-board-component-splits-into-modules"
          ],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "A control in the filter bar switches between board and table.",
              "done": false
            },
            {
              "text": "`?view=table` restores the table on load; an absent or unknown value",
              "done": false
            },
            {
              "text": "Filter text survives the switch in both directions.",
              "done": false
            },
            {
              "text": "Staged moves and their count survive the switch in both directions.",
              "done": false
            },
            {
              "text": "The columns render identically to before this card.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/the-table-is-a-second-view.md"
        },
        {
          "id": "the-tree-filters-without-re-rooting",
          "title": "The tree filters without re-rooting",
          "description": "Filtering a flat list hides rows. Filtering a tree has a decision in it that a\nflat list never poses: when a child matches and its parent does not, what\nhappens to the parent?\n\nThree answers exist. Drop the parent and the child rises to the root, which is\nfast to implement and changes what the card means — a card lifted out of its\nparent is a card without its context. Hide the child with its parent, which\nloses matches. Or keep the parent as context.\n\nAgreed shape:\n\n**The parent stays as context.** A non-matching ancestor of a match renders,\ndimmed, not counted as a match, and never re-rooted. Depth is invariant: a row\nthat silently changes indentation while you type is a row you cannot trust, and\nthe tree's shape is the one thing this view exists to show.\n\n**Ancestors of a match open automatically.** A match inside a collapsed branch\nis a match you cannot see. Opening for a filter does not overwrite the collapse\nstate you set by hand: clear the filter and the tree returns to how you left it.\n\n**Two counts, both stated.** How many cards matched, and how many rows are on\nscreen. They differ by exactly the context ancestors, and stating one without\nthe other is how a filtered tree lies about its size.\n\n**Matched text is marked** in the accent, in the title and in the id, since the\nfilter language matches on both.\n\n**The filter language is unchanged.** The same expression that filters the\ncolumns filters the tree; no view-specific syntax, no second parser. `parent`\nis already a filter field, so `parent:some-id` narrows to one card's children\nin either view, and that keeps working.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "the-board-reads-as-a-tree",
          "blocked_by": [
            "the-table-draws-one-row-per-card"
          ],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "A matching child renders under its non-matching parent, at its real depth.",
              "done": false
            },
            {
              "text": "A context ancestor is visually distinct from a match and is not counted",
              "done": false
            },
            {
              "text": "Matches inside collapsed branches become visible while filtering.",
              "done": false
            },
            {
              "text": "Clearing the filter restores the hand-set collapse state.",
              "done": false
            },
            {
              "text": "Both counts are shown: cards matched, rows displayed.",
              "done": false
            },
            {
              "text": "The same filter expression yields the same card set in both views.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/the-tree-filters-without-re-rooting.md"
        }
      ]
    },
    {
      "id": "in-progress",
      "title": "In progress",
      "limit": 3,
      "cards": [
        {
          "id": "artifacts-live-beside-their-card",
          "title": "Artifacts live beside their card",
          "description": "A card can name what it produced, and now it can open it — for one kind of\ntarget, in one place.\n\nTwo halves were broken. The link-out went first: `_resolve_repo_hrefs` was\ndeleted, so a `doc:` or `file:` target renders as the path it was written as\nand nothing 404s. The second half was that a validated path is still only a\npath — printing where a file is is not reaching it. That is closed for a card's\nown directory: `board/cards/<id>/` is published verbatim at\n`/_folio/kanban/<id>/`, and an artifact pointing into it is a link. The epic\n`the-board-reads-as-a-tree` runs on it, six artifacts, all opening.\n\nWhat remains is everything else the shape implies. `artifacts:` is still a\nhand-maintained list of paths rather than a reading of the directory, and each\nentry repeats the directory it is already in. A `doc:` pointing at a real\ndocumentation page — `docs/guide/plugins/kanban/index.md` is attached to a card\ntoday — stays unlinked even though the site publishes exactly that page. And\none card carries a `doc:` into `design/research/`, which no source publishes at\nall, so the promise \"a `doc:` artifact renders as a site page\" is still not\ntrue in general.\n\nThe docs side already solved this and the board never adopted it. A\ndocumentation page keeps its assets as siblings and writes\n`![alt](./kanban-card.png)`; `copy_page_asset` carries the file into the\ncontent tree at the same relative path the author wrote. The comment on that\nfunction states the stakes: without it the build does not lose the image, it\nfails. The result is that one string works in the repository, in an editor, and\non the site.\n\nAgreed shape:\n\n**A card is a file until it needs to be a directory.** Two shapes could carry\nthat; B is what shipped:\n\n```\nA: the card moves in            B: the card stays put\nboard/cards/                    board/cards/\n  agpl-license-position.md        agpl-license-position.md\n  the-board-reads-as-a-tree/      the-board-reads-as-a-tree.md\n    card.md                       the-board-reads-as-a-tree/\n    prototypes-compared.md          prototypes-compared.md\n    tree-table.html                 tree-table.html\n```\n\nA is one directory per card, unambiguous, and the entry point is `card.md` —\nchosen over `index.md`/`README.md`, the docs convention, because a card\ndirectory's entry is a card and not the index of a section, and because\n`cards/*/card.md` is a trivial glob beside `cards/*.md`. B is the page-bundle\nshape: the id names a file and a sibling directory, `cards/*.md` keeps finding\nevery card, and the loader needs no change at all.\n\nB won on what it does not disturb. Every card on the board keeps its path, the\nloader keeps its `cards/*.md` glob, and nothing that reads a card — the CLI's\nline surgery, the editor's rollback, every existing test — has to learn a\nsecond layout. A would have been a migration of 44 files to gain one property:\nthe directory and the card cannot drift apart. B pays for that property with a\ncheck instead, and until that check exists the drift is real — nothing notices\na directory whose card was renamed or deleted. That is the open criterion\nbelow, not a reason to have chosen A.\n\nThe id is the name on disk either way. Under B that is the existing rule\nunchanged: the filename stem is the card id, and the directory borrows it.\n\n**References are relative, and identical everywhere.** The body writes\n`[the comparison](./prototypes-compared.md)`, and `artifacts:` writes\n`tree-table.html`, not the project-relative path to it. The six entries on\n`the-board-reads-as-a-tree` today repeat\n`board/cards/the-board-reads-as-a-tree/` six times, and the tile prints all of\nit: a card's own directory is the one place a target never needs to say where\nit is. Validation resolves a sibling against the card, everything else against\nthe project, exactly as a markdown link already behaves.\n\n**`.md` publishes through Folio.** Plugin API 1.1 adds `collect_docs`: a plugin\ncontributes a source path and route before page generation, then Folio treats\nit exactly like a file under `source.docs`. A card's Markdown and MDX siblings\nuse that hook. They render at `<docs route>/kanban/<id>/<stem>/`, enter search,\nthe sitemap and `llms.txt`, get Markdown mirrors and local-image copying, and\nparticipate in link validation and incremental cleanup. A leading `_` opts out\nthe way `_TEMPLATE.md` already means \"not a card\". Raw files still publish at\n`/_folio/kanban/<id>/`, including the Markdown source needed by a bundle.\n\n**`artifacts:` stops being a hand-maintained path list.** What sits in the\ndirectory is that card's artifacts, derived rather than declared. The\nfrontmatter block survives for the things that are not files — `pr:`, `url:`,\n`api:` — and for putting a label on a sibling.\n\n**The layer over a plain bundle.** This is the shape a skill directory already\nuses: a named entry point and siblings on relative paths, read on demand. The\naddition is that ours is typed, validated, and published — a sibling is not\njust a file an agent might open, it is a page in the site, a row in the search\nindex, and a line in `llms.txt`. That is the first bet in PRODUCT.md stated as\na file layout: what a session produces becomes a page instead of staying\nscratch.\n\n**Session scratch is not an artifact, and the line is drawn by hand.** The five\nprototypes are attached, and the headless-browser scripts and screenshots that\nverified them are not: those stayed in `.artifacts/`, outside the board,\nuncommitted. The rule is whether a later reader would open it, and no\nheuristic decides that — the session does, when it attaches. What the board\nowes is that attaching is cheap and that nothing is attached by accident, which\nis why a derived `artifacts:` reads one directory and not the tree below it.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "L",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "high",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [],
          "criteria": [
            {
              "text": "Shape A or B is chosen and written down, with the reason.",
              "done": true
            },
            {
              "text": "Every existing card still loads unchanged.",
              "done": true
            },
            {
              "text": "A card's sibling directory is published, whole, with dotfiles and",
              "done": true
            },
            {
              "text": "No repository URL is generated for a target that lives beside the card.",
              "done": true
            },
            {
              "text": "A non-markdown sibling is carried so relative links resolve, and is not",
              "done": true
            },
            {
              "text": "`SKILL.md` and the board guide describe the form, and stop promising a",
              "done": true
            },
            {
              "text": "A card directory whose card is missing is reported, not ignored.",
              "done": false
            },
            {
              "text": "An artifact target may be written relative to the card, and the tile",
              "done": false
            },
            {
              "text": "A relative link from a card body to a sibling resolves in the repository",
              "done": false
            },
            {
              "text": "A `.md` sibling renders as a page rather than being served as source, in",
              "done": true
            },
            {
              "text": "`artifacts:` is derived from the directory; the block remains for",
              "done": false
            },
            {
              "text": "A `doc:` target that names a published documentation page links to that",
              "done": false
            },
            {
              "text": "A `doc:`/`file:` target that resolves to no reachable page warns at build,",
              "done": false
            },
            {
              "text": "`folio kanban` can turn a file card into a directory card.",
              "done": false
            },
            {
              "text": "The card pointing at `design/research/` is correct afterwards, and the",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "found while attaching prototypes — every artifact resolved to a 404; owner directed the docs asset model, one abstraction level up",
              "href": ""
            },
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "repo links removed board-wide, so the 404 is gone and only reachability is left; shape B placed by hand on the epic, A vs B still open",
              "href": ""
            },
            {
              "date": "2026-08-21",
              "actor": "claude",
              "ref": "",
              "note": "shape B shipped — card directories publish at /_folio/kanban/<id>/ and card-local artifacts open; markdown still served as source, artifacts: still hand-listed",
              "href": ""
            },
            {
              "date": "2026-08-23",
              "actor": "codex",
              "ref": "feat/artifact-board-poc",
              "note": "card Markdown and MDX now enter Folio's normal document pipeline; raw bundles remain intact, and ownership, symlink, collision, base-path, and warm-cleanup cases are pinned by tests",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/artifacts-live-beside-their-card.md"
        },
        {
          "id": "the-board-reads-as-a-tree",
          "title": "The board reads as a tree",
          "description": "`parent` has been a real field since the cardfile format shipped: one card id,\nvalidated against the board, settable from the CLI, and already a filter field.\nNothing renders it. The docs admit the gap in as many words — \"`parent` is a\nvalidated pointer, not a workflow\" — and when this card was written, not one of\nthe board's 36 cards set it. The pointer existed and the shape it pointed at was\ninvisible, so nobody reached for it. The seven cards below are the first to use\nit, and they exist so this view has real work to show.\n\nThe owner's call, after five prototypes built side by side: **the column board\nstays exactly as it is** and a second view joins it. Columns are the right\nreading for \"what is in flight\"; they are the wrong reading for \"what does this\nbreak into\". Two readings of one set of files, not two products.\n\nThe five prototypes and the comparison they produced are attached, and they sit\nin this card's own directory, which the build now publishes: each tile opens\nthe layout it argues for, on the board's own site rather than somebody else's.\nRead `prototypes-compared.md` for why the tree table won and what the other\nfour were better at.\n\nAgreed shape:\n\n**The view is a table.** One row per card, no exceptions. The first column is\nthe tree: indentation carries depth, a disclosure triangle sits on any card\nwith children. Every other column is one field read straight down — status,\nmilestone, type, size, assignee — the way a spreadsheet is read and a column\nboard cannot be.\n\n**Status and parent are allowed to disagree.** A child in Backlog under a\nparent in In review is not a contradiction to hide: a kanban orders by column,\na tree orders by parent, and the two orders are independent by design. The\ntable keeps the child under its parent, marks the row, and counts how many such\nrows exist. The disagreement is a number, not a surprise.\n\n**A parent says what it breaks into.** Children count, how far they have got,\nand what a collapsed row is hiding. A derived value never reads as an own\nvalue.\n\n**Nothing new in the format.** No `children` key, no ordering key, no epic\ntype. The tree is `parent` read backwards, and that is the whole data model.\n\nRejected while deciding, so it stays rejected: swimlanes by epic (resolves the\ncross-column child for free, but encodes exactly one level of decomposition and\nleaves half the grid empty); expanding children inside the existing cards (no\nnew view to learn, but a deep tree stretches a column without end); the board\nas one nested document (reads beautifully, scans worse than a grid on any\nsingle field).\n\nOut of scope, deliberately: reparenting from the interface. Changing a card's\nparent stays a cardfile edit or a CLI call, like every other structural change.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "XL",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-20",
          "milestone": "0.4",
          "artifacts": [
            {
              "kind": "doc",
              "target": "board/cards/the-board-reads-as-a-tree/prototypes-compared.md",
              "label": "Five layouts compared",
              "href": "/docs/kanban/the-board-reads-as-a-tree/prototypes-compared/"
            },
            {
              "kind": "file",
              "target": "board/cards/the-board-reads-as-a-tree/tree-table.html",
              "label": "Tree table (chosen)",
              "href": "/_folio/kanban/the-board-reads-as-a-tree/tree-table.html"
            },
            {
              "kind": "file",
              "target": "board/cards/the-board-reads-as-a-tree/epic-swimlanes.html",
              "label": "Epic swimlanes (rejected)",
              "href": "/_folio/kanban/the-board-reads-as-a-tree/epic-swimlanes.html"
            },
            {
              "kind": "file",
              "target": "board/cards/the-board-reads-as-a-tree/board-inline-expansion.html",
              "label": "Inline expansion (rejected)",
              "href": "/_folio/kanban/the-board-reads-as-a-tree/board-inline-expansion.html"
            },
            {
              "kind": "file",
              "target": "board/cards/the-board-reads-as-a-tree/document-outline.html",
              "label": "Document outline (rejected)",
              "href": "/_folio/kanban/the-board-reads-as-a-tree/document-outline.html"
            },
            {
              "kind": "file",
              "target": "board/cards/the-board-reads-as-a-tree/tree-rail-detail.html",
              "label": "Tree rail and detail (rejected)",
              "href": "/_folio/kanban/the-board-reads-as-a-tree/tree-rail-detail.html"
            }
          ],
          "criteria": [
            {
              "text": "The column board is unchanged by this work.",
              "done": false
            },
            {
              "text": "A second view renders the board as a table, one row per card.",
              "done": false
            },
            {
              "text": "A card's children are reachable from it in both views.",
              "done": false
            },
            {
              "text": "The board's own cards use `parent`, so the view has real work to show.",
              "done": true
            },
            {
              "text": "No new frontmatter key.",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "card created after five prototypes; tree table chosen, swimlanes and outline rejected",
              "href": ""
            },
            {
              "date": "2026-08-20",
              "actor": "pguijas",
              "ref": "",
              "note": "five layouts prototyped against the real board and verified adversarially; tree table chosen, columns kept; all five rollups read zero, so what counts as done is still open",
              "href": ""
            },
            {
              "date": "2026-08-20",
              "actor": "claude",
              "ref": "",
              "note": "prototypes and the comparison moved into the card's own directory and attached; six artifacts, all local paths",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "agent-project-os",
          "phaseTitle": "Project OS",
          "file": "board/cards/the-board-reads-as-a-tree.md"
        }
      ]
    },
    {
      "id": "in-review",
      "title": "In review",
      "limit": 3,
      "cards": [
        {
          "id": "landing-as-product-surface",
          "title": "Landing as product surface",
          "description": "A top-to-bottom copy round applied in July 2026 treats the landing page as a product surface rather than a brochure. Each claim has exactly one owning section, and PRODUCT.md holds the register of claims so the page and the product story cannot drift apart.",
          "tags": [
            "landing",
            "copy"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "hero description at most two sentences",
              "done": true
            },
            {
              "text": "no meta-copy",
              "done": true
            },
            {
              "text": "one owning section per claim",
              "done": true
            },
            {
              "text": "owner review of the rendered page",
              "done": true
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            },
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "c894ec7fb",
              "note": "owner reviewed the rendered landing and approved. Final pass in the same session: funnel caption removed, closing statement removed — four sections, the boards close the page.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/landing-as-product-surface.md"
        },
        {
          "id": "plugin-system-unification",
          "title": "Plugin system unification",
          "description": "One plugin platform behind every surface. The registry becomes the single source of truth, the default plugins (landing, roadmap, kanban, openapi) are loaded through the same path as project plugins, and the dedicated-page contract is shared so any plugin can claim a page the same way the built-ins do.",
          "tags": [
            "plugins",
            "platform"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-07-16",
          "milestone": "0.3",
          "artifacts": [
            {
              "kind": "pr",
              "target": "23",
              "label": "",
              "href": ""
            }
          ],
          "criteria": [
            {
              "text": "one loading path for default and project plugins",
              "done": true
            },
            {
              "text": "dedicated-page contract on /roadmap and /kanban",
              "done": true
            },
            {
              "text": "PR #23 merged to main",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/plugin-system-unification.md"
        },
        {
          "id": "band-descriptions-never-render",
          "title": "Band descriptions never render",
          "description": "The `description` authored under `roadmap:` and `kanban:` in docs.yaml never\nreaches the public pages. `configure()` stores the output of\n`normalize_roadmap()` / `normalize_kanban()` into `config.extra`, and both\nnormalizers drop the `description` key; `register_extensions()` then reads\n`description` back from the normalized dict and always gets nothing, so\n/roadmap/ and /kanban/ render a bare heading.",
          "tags": [
            "bug",
            "plugins"
          ],
          "assignee": [],
          "type": "bug",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-03",
          "milestone": "",
          "artifacts": [],
          "criteria": [
            {
              "text": "normalize_roadmap() preserves description",
              "done": true
            },
            {
              "text": "normalize_kanban() preserves description",
              "done": true
            },
            {
              "text": "/roadmap/ and /kanban/ render the docs.yaml descriptions",
              "done": true
            },
            {
              "text": "regression tests cover the configure to register_extensions round trip",
              "done": true
            }
          ],
          "trail": [
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "",
              "note": "carded from the roadmap and kanban audit; the fix starts in this session.",
              "href": ""
            },
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "dbd563f22",
              "note": "both normalizers preserve the key, round-trip and public-page tests added; moved in-progress -> in-review. The rendered-page criterion closes on the next build.",
              "href": ""
            },
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "8d6dfd98b",
              "note": "verified on the rebuilt serve — both bands render their descriptions; last criterion closed.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "",
          "phaseTitle": "",
          "file": "board/cards/band-descriptions-never-render.md"
        },
        {
          "id": "kanban-single-board-with-filters",
          "title": "Kanban is one board with flexible filters",
          "description": "The public board renders every card in one instance, but the only filter is\na mount-time URL parameter with no visible control: a visitor who lands on a\nmilestone deep link cannot see the filter, change it, or clear it. Cards also\ncarry their full body on the board, which buries the column story. The board\nbecomes: one instance with all cards, an in-page filter system (milestone,\ntag, text) that stays in the URL for deep links, cards that show the title\nonly, and a full card view that opens on click.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-04",
          "milestone": "0.3",
          "artifacts": [
            {
              "kind": "doc",
              "target": "design/research/kanban-references-teardown.md",
              "label": "Reference teardown: SVAR and ReUI",
              "href": ""
            }
          ],
          "criteria": [
            {
              "text": "one board instance renders all cards; filters never produce a second board",
              "done": true
            },
            {
              "text": "in-page filter controls for milestone, tag, and text, visible and clearable",
              "done": true
            },
            {
              "text": "active filters are reflected in the URL so deep links keep working",
              "done": true
            },
            {
              "text": "board cards render the title only",
              "done": true
            },
            {
              "text": "clicking a card opens the complete card: description, criteria, trail, artifacts, metadata",
              "done": true
            },
            {
              "text": "keyboard and reduced-motion behavior preserved",
              "done": true
            }
          ],
          "trail": [
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction; work starts in this session.",
              "href": ""
            },
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "bb7e54254",
              "note": "filter rail (milestone, tag, text, URL-synced), title-only cards, card dialog with Escape and focus return; component tests pin the new contract, plugin docs updated. Verified on the rebuilt serve; moved in-progress -> in-review.",
              "href": ""
            },
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "",
              "note": "owner rejected the visual execution. Four redesign mockups produced for review under design/mockups/kanban/ (folio-editorial, gh-projects, jira, linear + index), all on the real board data and theme tokens, each with working filters and card overlay. Card stays in-review pending the owner's pick.",
              "href": ""
            },
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "",
              "note": "owner review of the four: the card-as-popup is the keeper across all of them; the folio-editorial direction (technical plate, rule lines, mono apparatus) is rejected outright for the board UI. Synthesis in design/mockups/kanban/proposal.html — jira lanes and raised cards with a centered popup and metadata sidebar, gh token filters, linear keyboard affordances, folio theme tokens.",
              "href": ""
            },
            {
              "date": "2026-08-05",
              "actor": "claude",
              "ref": "5fb689361",
              "note": "SVAR React Kanban and ReUI Kanban read at the source; verdict is to take neither as a dependency and write the techniques ourselves. Teardown attached as a doc artifact.",
              "href": ""
            },
            {
              "date": "2026-08-05",
              "actor": "claude",
              "ref": "a86d10ba1",
              "note": "shipped. Cards carry a stable uid and every mutation takes it, so the filter gate on drag is gone — a filtered board is operable. Overlay became uid -> {from, to} with a per-entry staleness check; drop placeholder, undo, facet record, aria-live, focus trap, coarse-pointer move buttons, data-slot seams, and the approved skin. 1027 tests green, tsc clean.",
              "href": ""
            },
            {
              "date": "2026-08-05",
              "actor": "claude",
              "ref": "f5fc1b818",
              "note": "adversarial review of the rewrite, 28 findings, 18 refuted, 9 fixed — the facet token parser committed mid-word, the drag payload typed card ids into the filter field, the filter input had no visible focus, repeated announcements were silent, \"/\" was bound page-wide, the focus trap leaked forward, and touch move buttons covered card titles in the miniatures.",
              "href": ""
            },
            {
              "date": "2026-08-10",
              "actor": "claude",
              "ref": "",
              "note": "the board takes the landing's voice. Ten app-like studies were rejected as gaudy; the owner asked for editorial and pointed at the landing, and measuring it showed the board was already speaking the same language with the colour drained out — the column names were the landing's eyebrow at 12px/0.08em in grey instead of 11px/0.14em in the accent. Shipped: a masthead (mono blue eyebrow over a 36px sentence-case headline) replacing the 14px label, no lane fills or lane borders, cards opening with the roadmap step their milestone names, and the type scale cut to the landing's own. Home and Roadmap left the toolbar. Measured at 1440: 10 cards above the fold against 9 before, because dropping the card description the popup already carries paid for the masthead. Studies under design/mockups/board-minimal/.",
              "href": ""
            },
            {
              "date": "2026-08-07",
              "actor": "claude",
              "ref": "",
              "note": "technical audit of the shipped board, then every finding fixed. Measured, not guessed: the sticky toolbar ran 83px at desktop but 183px at 360px, so it now holds two rows at every width (facets collapse below md, actions below xl). The live region spoke once per keystroke (six for six characters) and now speaks once the typing settles. The dialog's scrolling body was not a tab stop, so a long trail was unreachable without a mouse. The board behind the open card is inert. `role=\"list\"` no longer holds the empty-state paragraph, which some tools dropped outright. Contrast: the card count sat at 2.3:1 and the milestone label at 4.2:1 in dark. The coarse-pointer pin is gone — it hid every milestone on every phone to serve a control the dialog already carries — and the milestone now steps aside on the same condition that paints the move buttons, which is the keyboard overlap the audit found. Seven font sizes became two on the board surface; the column names moved to the label register so the board's h1 is finally its only heading, at zero added height. Six unicode characters used as icons became drawn marks on ColumnGlyph's 16-unit grid. The hard-coded amber became a real `--warning` token, which no single value could serve in both modes.",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/kanban-single-board-with-filters.md"
        },
        {
          "id": "filter-composer-full-height-rail",
          "title": "The composer is a full-height rail beside the board",
          "description": "The composer opens as a popup under the filter bar, five columns wide. With\none control per field the grid lost its balance: a tall status list beside a\nlone priority checkbox beside three floating selects, and Created wrapped\nunderneath. The owner's direction: the composer becomes a toggleable panel\noccupying the full height of the board's left side, and the popup dies.\n\nAgreed shape:\n\n**Structure.** Below the filter bar the board area becomes a two-column\ngrid: a ~17rem composer rail and the board. Open, the board narrows;\nclosed, the rail's column is gone and the board takes the full width. The\nfilter bar stays above, spanning everything; the existing filter glyph at\nits left edge is the toggle (`aria-expanded`/`aria-controls`). The rail is\nsticky below the bar with its own scroll. Sections stack in one column —\nstatus, priority, type, milestone, assignee, tag, created — with the\n\"Also\" chips and \"Clear the filter\" at the foot. The controls themselves\n(`PanelRow`, `PanelSelect`, `PanelTagInput`) do not change; the popup's\npositioning (`absolute top-full`, the 52vh cap, the five-column grid) dies.\n\n**Behavior.** Closed by default, no persistence. Escape inside the rail\ncloses it and returns focus to the toggle, as the popup did. Below `lg`\nthere is no room to push: the same panel renders as a fixed left drawer\n(same width, shadow); click outside or Escape closes it. `/` keeps\nfocusing the expression field. This is layout only — the language, the\nrewrite helpers, and the no-second-store invariant are untouched.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-16",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "below the filter bar, an open rail (~17rem) and the board share a two-column grid; closed, the board takes the full width",
              "done": false
            },
            {
              "text": "the filter glyph in the bar toggles the rail, with aria-expanded and aria-controls",
              "done": false
            },
            {
              "text": "the rail is sticky below the bar and scrolls its own overflow",
              "done": false
            },
            {
              "text": "sections stack in one column, Also chips and Clear at the foot; every control unchanged",
              "done": false
            },
            {
              "text": "closed by default, no persisted state; Escape inside closes and returns focus to the toggle",
              "done": false
            },
            {
              "text": "below lg the rail is a fixed left drawer; click outside or Escape closes it",
              "done": false
            },
            {
              "text": "\"/\" still focuses the expression field; typed text and controls stay one expression",
              "done": false
            },
            {
              "text": "the popup positioning and its five-column grid are gone from the component",
              "done": false
            },
            {
              "text": "compact board miniatures render exactly as before",
              "done": false
            },
            {
              "text": "the composer paragraph in docs/guide/plugins/kanban/index.md describes the rail",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — full-height left rail replacing the popup; filter bar stays above; closed by default; drawer below lg.",
              "href": ""
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "b1f9ff595",
              "note": "rail shipped: two-column grid on lg, fixed drawer below, popup positioning gone; controls untouched; suite green",
              "href": ""
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "7a2d34273",
              "note": "final review fixes: rail clears the sticky navbar via --nextra-navbar-height calc, Escape no longer tears down the rail with the card dialog, rem breakpoint, conditional aria-controls, honest test names",
              "href": ""
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "3283521fe",
              "note": "owner review: the rail now spans the full height — the filter bar narrows into the grid's right column; staging banner stays full-width above",
              "href": ""
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "ca7daff27",
              "note": "owner review: the rail surface stretches to the board's foot; the controls follow the scroll inside it",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "a0d490b80",
              "note": "review fix: the bar's render gate returns to compact-only, so the static page keeps the bar and its h1; stale docstring rewritten",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "a28e88878",
              "note": "owner found the rail overflowing: the public view never defined --nextra-navbar-height, so the rail computed against 0px under a fixed 64px navbar; the view layout now declares 4rem beside its pt-16",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "ba3eaae45",
              "note": "owner redirected after the sticky rounds: the public board is now an app workspace — viewport-height section under the navbar, rail as a fixed-height floating panel with its own scroll, canvas scrolls both axes; docs embeds keep the in-flow layout",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "ad58b1dc3",
              "note": "owner: left margin asymmetric — the workspace now runs full-bleed, the rail truly touches the edge it was drawn for, and the canvas keeps 24px on both sides",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/filter-composer-full-height-rail.md"
        },
        {
          "id": "filter-composer-one-control-per-field",
          "title": "The composer draws one control per field, and cards carry type and assignee",
          "description": "The filter composer draws every field the same way: a column of tri-state\ncheckboxes. That shape is right for the two fields you scan (status,\npriority) and wrong for everything else — a single-value field wants a\ndropdown, an open list wants an input. And two facts a team board runs on,\nwho owns a card and what kind of work it is, barely exist: `assignee` is in\nthe format but invisible on the board, and type has no field at all.\n\nThe change, agreed with the owner (simple and plain as the rule; menu plus\ndata model, no browser write path):\n\n**Data model.** `type: <value>` joins the card frontmatter — single value,\nfree vocabulary, the types that exist are the types cards use, exactly like\n`milestone`. The loader carries it, the plugin emits it into\n`lib/kanban-data.ts`, `folio kanban show` prints it, the cardfile docs\ndescribe it. No vocabulary validation.\n\n**The card.** The face's metadata line gains the type, and `@assignee`\nshows when set; cards without them render unchanged. The dialog gains a\nType row beside the existing metadata.\n\n**The composer.** One control per field, all derived from the parsed\nexpression and writing back through it — typed text and clicked controls\ncannot disagree, because there is no second store. Status and priority stay\ntri-state checkbox lists with predictive counts. Type, milestone, and\nassignee become native selects: the board's values with counts, plus \"any\"\nto clear the term. Tag becomes an input with the board's tags as\nsuggestions and removable chips; adding ORs into the tag term. Created\nkeeps its comparator and date. Whatever a control cannot draw (multi-value\nin a select, negations, free text) stays listed as removable \"Also\" chips.\nFields with no values on the board do not render.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [],
          "type": "feature",
          "size": "",
          "source": "",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-16",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "`type:` in frontmatter flows loader -> `lib/kanban-data.ts` -> board, prints in `folio kanban show`, and is documented in the cardfile section",
              "done": false
            },
            {
              "text": "the card face shows type in its metadata line and `@assignee` when set; cards without them render unchanged",
              "done": false
            },
            {
              "text": "the card dialog lists Type with the other metadata rows",
              "done": false
            },
            {
              "text": "status and priority stay tri-state checkbox lists with predictive counts",
              "done": false
            },
            {
              "text": "type, milestone, and assignee are single-select dropdowns of the board's values with counts, plus \"any\" to clear",
              "done": false
            },
            {
              "text": "tag is an input with suggestions and removable chips; adding a tag ORs into the tag term",
              "done": false
            },
            {
              "text": "every control derives from the parsed expression and rewrites it; no control holds state of its own",
              "done": false
            },
            {
              "text": "terms no control can draw stay as removable \"Also\" chips; valueless fields do not render",
              "done": false
            },
            {
              "text": "`type:x` filters through the expression language and the `?` reference lists it without a separate edit",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — design agreed in session: menu + data model, `type` as a free single-value field, one control per field in the composer, simplicity as the rule.",
              "href": ""
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "ccdc7ea07",
              "note": "type field end to end (loader, data module, CLI, card, composer); composer redrawn one control per field; docs and template updated; suite green",
              "href": ""
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "f202d4832",
              "note": "final whole-branch review: 0 critical; docs field list + composer semantics fixed, tag chips from term alternatives, dateTerm double-draw gone, rewrite helpers now executed by the language tests",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/filter-composer-one-control-per-field.md"
        },
        {
          "id": "cards-carry-assignees-source-and-size",
          "title": "Cards carry assignees, a source, and a size",
          "description": "A card can name one assignee, and nothing says where the work lives or how\nbig it is. The owner wants three more dimensions: several people on one\ncard, a source (the repo or branch the work belongs to — one branch per\nproject, for example), and a size. Assignee and tags already exist; this\ncard completes the set.\n\nAgreed shape:\n\n**`assignee` accepts a list.** The same key, two forms: `assignee: ana`\nstill works, `assignee: [ana, bo]` joins it. The loader normalizes both to\na list — trimmed strings, duplicates dropped, order preserved — and the\nemitted TypeScript changes `assignee: string` to `assignee: string[]`. No\nnew `assignees` key.\n\n**`size` is a closed scale.** `size: M`, case-insensitive, normalized to\nuppercase. Anything outside S / M / L / XL is a hard loader error — the\nsame treatment as an unknown status: `folio build` stops and\n`folio kanban check` goes red naming the file and the allowed values. The\none closed field in the model, by the owner's explicit choice.\n\n**`source` is free text.** `source: folio#feat/x`, a URL, a repo name —\na free scalar with the same treatment as `type` (non-scalars warned and\nignored).\n\n**The card.** The face's bottom line shows every assignee (`@ana @bo`) and\nthe size as a small bordered chip (`M`, `XL`). Source stays off the face —\nthe metadata line already carries type · phase · milestone. The dialog\ngains Size and Source rows (a source starting with `http(s)://` renders as\na link) and the Assignee row joins the list. Cards without the new fields\nrender exactly as before.\n\n**The composer.** `size` joins `CHECK_FIELDS` — tri-state checkboxes like\nstatus and priority, only the values in use, in scale order S→XL, with\ncounts. `source` joins `SELECT_FIELDS`. Assignee keeps its select; a card\nwith two assignees counts for both values. The filter language does not\nchange — `size:m,l` and `-source:none` fall out of `FILTER_FIELDS`; URLs\nwith colons take quotes, which the language already has.\n\n**The CLI.** `update --set` accepts `size` (validated against the scale),\n`source`, and `assignee=ana,bo` (comma split, as `add --tags` already\ndoes). The `show` table gains a Size column; source is not a column.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "peter",
            "claude"
          ],
          "type": "feature",
          "size": "L",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-17",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "`assignee: ana` and `assignee: [ana, bo]` both load; the emitted interface says `assignee: string[]`; duplicates dropped, order preserved",
              "done": false
            },
            {
              "text": "a size outside S/M/L/XL fails the loader naming the file and the allowed values; check goes red; lowercase input normalizes to uppercase",
              "done": false
            },
            {
              "text": "`source` is carried as a free scalar; non-scalar warned and ignored",
              "done": false
            },
            {
              "text": "the card face shows `@ana @bo` and a size chip; cards without the fields render unchanged",
              "done": false
            },
            {
              "text": "the dialog shows Size and Source rows; an `http(s)://` source is a link; Assignee joins the list",
              "done": false
            },
            {
              "text": "size filters as tri-state checkboxes in scale order S→XL with counts; source is a select with counts plus \"any\"",
              "done": false
            },
            {
              "text": "a card with two assignees matches a filter on either one and counts for both in the composer",
              "done": false
            },
            {
              "text": "`update --set size=xxl` is rejected; `--set source=…` and `--set assignee=ana,bo` work; the show table has a Size column",
              "done": false
            },
            {
              "text": "docs cover the three fields: formats.md field list, the composer paragraph in index.md, cli.md, and the commented lines in _TEMPLATE.md",
              "done": false
            },
            {
              "text": "existing pins move from `assignee: string` to `assignee: string[]`; the filter-language tests execute multi-assignee values and the S→XL order",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — several assignees per card, a free source field, and a closed S/M/L/XL size; design approved in session.",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "a3859e2b6",
              "note": "shipped: assignee lists, free source, and the closed size scale — loader to composer to CLI, docs and skill updated, v1 export byte-identity pinned by an executed test",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/cards-carry-assignees-source-and-size.md"
        },
        {
          "id": "filter-composer-searchable-combobox",
          "title": "The composer selects become searchable comboboxes",
          "description": "The composer's four value pickers (type, milestone, assignee, source) are\nnative selects. The owner doesn't like them: no search when a field has\nmany values, and the OS look sits oddly in the rail. They become one custom\ncombobox — no new dependency, ARIA listbox pattern, search appearing only\nwhen it earns its row.\n\nAgreed shape:\n\n**The control.** A `PanelCombobox` beside the other Panel* controls in\n`kanban-board.tsx`; `PanelSelect` dies. Trigger button styled like the\nselect it replaces (h-7, border, current value or \"any\", chevron),\n`aria-haspopup=\"listbox\"` and `aria-expanded`. Open: an absolute panel\nunder the trigger — full width, border, shadow, max-height with its own\nscroll, scrolled into view so it never hides under the rail's fold.\nOptions: **any** first (clears), then the board's values with\n`value — count` in board order, and a typed value the board does not have\nstill drawn as an extra option. The active option is highlighted and\n`aria-selected`.\n\n**The search.** At 8+ options, an input at the top of the panel filters by\ncase-insensitive substring; ArrowDown moves from the input into the list.\nUnder 8, the list is direct — no input row.\n\n**Keyboard and dismissal.** Enter/Space/ArrowDown open. Arrows move,\nEnter picks, Escape closes and returns focus to the trigger WITHOUT\nclosing the rail (the handler stops propagation before the rail's own\nEscape listener — fixing the parked \"rail selects lack the Escape guard\"\nfollow-up). Click outside closes. Picking closes and rewrites the\nexpression exactly as today: the `onSelect(value | null)` contract and the\ncomposer invariant (the expression is the only filter state) do not change.\n\n**What stays native.** The Created comparison select (3 fixed options) and\nthe dialog's Move-to select (focus must survive the card reparenting). The\n\"now the only menu on the board\" comment at the Move-to select is updated,\nbecause it stops being true.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "claude"
          ],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-17",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "type, milestone, assignee, and source render as the custom combobox; `PanelSelect` is gone from the component",
              "done": false
            },
            {
              "text": "options: \"any\" first, then `value — count` in board order; an off-board typed value still appears; picking rewrites the expression exactly as the select did",
              "done": false
            },
            {
              "text": "the search input appears only at 8+ options, filters by case-insensitive substring, and ArrowDown enters the list",
              "done": false
            },
            {
              "text": "keyboard: Enter/Space/ArrowDown open; arrows navigate; Enter picks; Escape closes, refocuses the trigger, and does not close the rail",
              "done": false
            },
            {
              "text": "click outside closes; the open panel has max-height, its own scroll, and scrolls into view on open",
              "done": false
            },
            {
              "text": "ARIA: `aria-haspopup=\"listbox\"`, `aria-expanded`, `aria-selected` on the active option, the field label announced",
              "done": false
            },
            {
              "text": "the Created and Move-to selects stay native; the \"only menu on the board\" comment is rewritten",
              "done": false
            },
            {
              "text": "a pure `filterOptions(values, query)` helper is executed by the node harness; structure/ARIA string pins cover the rest",
              "done": false
            },
            {
              "text": "compact miniatures and the SSR export render exactly as before",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — the native selects don't please; custom combobox with search at 8+ options; design approved in session.",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "9ff993995",
              "note": "shipped: the four pickers are one custom combobox — search at 8+ values, opens on the current value, Escape and focus caged properly after the final review caught the delegation trap",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/filter-composer-searchable-combobox.md"
        },
        {
          "id": "the-roadmap-is-the-milestone-registry",
          "title": "The roadmap is the milestone registry",
          "description": "`milestone` is free text and formats.md admits the debt: \"a full registry\nwith validation is planned, not shipped\". The registry already exists —\nthe roadmap's phases carry `version` — and `_resolve_roadmap_phases`\nalready joins the two halves. What's missing is the complaint when the\njoin fails.\n\nAgreed shape (owner chose warning severity):\n\n**The rule.** When the config declares a roadmap with at least one\nversioned phase, a card whose `milestone` matches no phase version gets a\nwarning naming the card and the known versions — surfaced yellow by\n`folio kanban check`, never breaking the build. The \"future milestone the\nroadmap has not reached yet\" case stays legal, loudly. Boards without a\nroadmap section (or with no versioned phases) stay exactly as free as\ntoday: no warning, no coupling.\n\n**The seams.** The check lives beside `_resolve_roadmap_phases`, which\nalready computes `by_version` — one loop, one `warnings.warn` per\nunclaimed milestone. The `v`/`V` prefix stripping it already does applies.\nformats.md's milestone row drops the \"planned, not shipped\" confession and\nstates the shipped rule.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "claude"
          ],
          "type": "feature",
          "size": "S",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-17",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "with a versioned roadmap, a card milestone no phase claims warns naming the card and the known versions; `folio kanban check` shows it yellow and still exits green",
              "done": false
            },
            {
              "text": "a claimed milestone, a board without roadmap, and a roadmap without versions all stay silent",
              "done": false
            },
            {
              "text": "the build never breaks over a milestone",
              "done": false
            },
            {
              "text": "formats.md's milestone row documents the shipped rule instead of the \"planned, not shipped\" note",
              "done": false
            },
            {
              "text": "tests cover: unclaimed warns, claimed silent, no-roadmap silent, v-prefix versions still match",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — standardize milestone against the roadmap's versions, warning severity; queued behind the combobox card.",
              "href": ""
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "982eebe24",
              "note": "shipped: unclaimed milestones warn grouped against the roadmap's versions; check replays the resolution and shows them yellow; docs drop the planned-not-shipped note",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/the-roadmap-is-the-milestone-registry.md"
        },
        {
          "id": "cards-carry-comments",
          "title": "Cards carry comments",
          "description": "The trail records what happened; nothing on a card holds a conversation.\nThe owner wants comments — and, correcting the first mockup, wants them\n**as their own separated section, like the artifacts**: a full-width band\nof the dialog, not prose squeezed between criteria and trail.\n\nAgreed shape:\n\n**The section.** `## Comments` in the card markdown, one line per\ncomment: `- YYYY-MM-DD @actor: text`. The trail's grammar family minus\nthe ref — a comment argues, it does not point at a commit. Strict\nwriter, tolerant reader: a bullet that misses the grammar warns at build\nand still renders as prose, exactly like a malformed trail line.\n\n**The band.** Between the body grid and the artifacts band: bubble glyph,\n`Comments · N`, one row per comment — mono date, bold `@actor`, the text\nwith its inline markdown rendered. Same scroll cap and keyboard stop as\nthe artifacts band. No comments, no band: a mail without replies shows\nno empty thread.\n\n**The pipeline.** Loader parses the section; normalizer carries\n`comments: {date, actor, text}[]`; the emitted interface grows\n`KanbanComment`; `boardToYaml` exports `comments:` only when present so\nv1 exports stay byte-identical. CLI: `folio kanban comment <id> \"text\"\n[--by NAME] [--commit]` — `--by` defaults to git user.name, the writer\nvalidates date/actor/single-line text, and the line appends at the\nsection's tail through the same surgery as trail.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "claude"
          ],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-18",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "`## Comments` parses to `comments: [{date, actor, text}]`; a malformed line warns and the build survives",
              "done": false
            },
            {
              "text": "the dialog shows the comments band between body and artifacts — date, `@actor`, markdown-rendered text — and no band when empty",
              "done": false
            },
            {
              "text": "`folio kanban comment <id> \"text\"` appends the canonical line, creates the section when missing, defaults `--by` to git user.name, collapses whitespace like the trail writer, and refuses empty text",
              "done": false
            },
            {
              "text": "`boardToYaml` writes `comments:` only when present; the v1 byte-identity pin still holds",
              "done": false
            },
            {
              "text": "docs cover the section grammar, the CLI verb, and the band; SKILL.md and the agents table teach the gesture",
              "done": false
            },
            {
              "text": "tests: loader parse + malformed warn, CLI append/create/refuse, component pins for band order and `<MdInline text={comment.text} />`",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — comments as their own separated section like the artifacts; conversation distinct from the trail's record.",
              "href": ""
            },
            {
              "date": "2026-08-19",
              "actor": "claude",
              "ref": "bb05cf990",
              "note": "shipped: ## Comments parsed/normalized/exported, the thread band above the artifacts, folio kanban comment with git-user default; review reproduced the Rich-markup crash and the case-blind heading hole, both fixed with the trail sharing the cure",
              "href": ""
            }
          ],
          "comments": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "text": "dogfood: this very thread renders in the band this card ships"
            }
          ],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/cards-carry-comments.md"
        },
        {
          "id": "the-card-dialog-reads-like-a-mail",
          "title": "The card dialog reads like a mail",
          "description": "The dialog opens on `board/cards/<id>.md` — a mono file path presiding\nover the strip that should identify the card — while the artifacts, the\none thing a card produces, sit as grey chips at the bottom of the rail.\nThe owner wants the hierarchy inverted, designed over HTML mockups in\nsession: the card reads like a mail, attachments at the foot.\n\nAgreed shape:\n\n**The header.** The title presides, `Esc` / a pen icon-button (edit) /\nthe close button at the right edge, all three 28px tall. The path leaves\nthe header and becomes the `Card` field in the rail — still the link,\nnow with the file glyph, sitting with the other facts.\n\n**The attachments band.** A full-width strip under the body grid, above\nthe footer: `Artifacts · N` with a paperclip, then one tile per artifact\n— a kind-tinted icon square (doc blue, pr green, url warm, api gold,\nfile ink), the label, and the full target in mono. A dashed ghost tile\nteaches the gesture: `folio kanban attach <id> --doc <path>`, shown\nwhenever moves are live; with no artifacts the band is the ghost alone.\n`ArtifactChip` dies.\n\n**Colour and marks.** Section labels get their small glyphs (check for\ncriteria, clock for trail, paperclip for artifacts), tags take a soft\naccent tint, and the status value carries a column dot. Priority keeps\nits existing ends-of-the-scale treatment. The footer keeps only the\nstaged-move export line; editing lives in the header now.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "claude"
          ],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-18",
          "milestone": "0.3",
          "artifacts": [
            {
              "kind": "doc",
              "target": "docs/guide/plugins/kanban/index.md",
              "label": "Board guide — the dialog section",
              "href": ""
            }
          ],
          "criteria": [
            {
              "text": "the dialog header carries the title with Esc, edit pen, and close at one height; the path renders as the linked `Card` field in the rail",
              "done": false
            },
            {
              "text": "artifacts render as a full-width band at the dialog's foot: kind-tinted icon tiles with label and mono target; `ArtifactChip` is gone",
              "done": false
            },
            {
              "text": "the band teaches `folio kanban attach <id> --doc <path>` when moves are live, and renders the ghost alone when the card has no artifacts",
              "done": false
            },
            {
              "text": "the footer carries only the staged-move export line; static exports keep the edit pen in the header",
              "done": false
            },
            {
              "text": "docs stop claiming the header shows the path and describe the attachment band",
              "done": false
            },
            {
              "text": "component pins cover: title in header, Card field link, ArtifactTile, the attach hint, and the footer condition",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — dialog oriented to attaching artifacts, designed over HTML mockups iterated in session (title presides, mail-style attachment band, kind colours).",
              "href": ""
            },
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "1895a736c",
              "note": "shipped: title presides the header with Esc/pen/close, the path is the rail's linked Card field, artifacts close the dialog as a mail-style band (kind-tinted tiles + attach ghost on cardfile boards); review wave fixed labelled-PR numbers, band scroll, and the missing pins; docs + screenshot regenerated",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/the-card-dialog-reads-like-a-mail.md"
        },
        {
          "id": "the-dialog-renders-markdown",
          "title": "The dialog renders its markdown",
          "description": "Cards are markdown files, and the dialog prints their prose raw: a\ndescription authored as `**The header.**` shows its asterisks, backticked\ncommands show their backticks. The owner hit it on the board today. The\nbody is the one place a card talks, and it talks in the format the file\nalready is.\n\nAgreed shape:\n\n**The subset, from usage.** A scan of this board's own cards: bold and\ninline code everywhere, multi-paragraph descriptions common, zero em,\nlinks, or lists. Rendered: `` `code` ``, `**bold**`, `[text](https://…)`\nwith the scheme guard the repo already applies everywhere (anything not\nhttp(s) stays literal text), and paragraphs split on blank lines. No raw\nHTML ever — tokens become React nodes, never `dangerouslySetInnerHTML`.\nUnmatched marks stay literal: a stray asterisk is prose, not a crash.\n\n**The seams.** A pure `parseInlineMd(text) → MdToken[]` tokenizer beside\nthe other extracted-and-executed helpers, exercised by the node harness\nlike the filter language; a small renderer maps tokens to `<code>`,\n`<strong>`, `<a>`. Applied to the dialog description (paragraphs), each\nacceptance criterion, and each trail note. Faces stay title-only; raw\nstrings stay raw in data, export, and filters.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "claude"
          ],
          "type": "feature",
          "size": "M",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-18",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "`**bold**`, `` `code` ``, and `[text](https://…)` render in the dialog's description, criteria, and trail notes; blank lines split description paragraphs",
              "done": false
            },
            {
              "text": "a non-http(s) link target stays literal text; no `dangerouslySetInnerHTML` exists in the component",
              "done": false
            },
            {
              "text": "unmatched `*`/`` ` `` marks render as the literal characters",
              "done": false
            },
            {
              "text": "`parseInlineMd` is executed by the node harness: code, bold, link, literal-fallback, and scheme-guard cases",
              "done": false
            },
            {
              "text": "raw markdown stays raw in kanban-data, boardToYaml, and filter matching",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — the dialog must render the markdown the cards are written in; subset drawn from the board's real usage.",
              "href": ""
            },
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "269d5eb22",
              "note": "shipped: parseInlineMd tokenizes code/bold/http-links with paragraphs on blank lines, tokens become React nodes (no innerHTML path); review reproduced the double-backtick mangle on this very card and it now parses as CommonMark quoting; adversarial ReDoS claim refuted at card scale",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/the-dialog-renders-markdown.md"
        },
        {
          "id": "the-move-to-is-a-custom-dropdown",
          "title": "The Move-to is a custom dropdown",
          "description": "The dialog's one control is the board's last native select. Owner call:\nit becomes a custom dropdown like the composer's comboboxes — the OS\nmenu sits oddly in the redesigned dialog, and the parked \"Move-to Escape\nguard is theater\" follow-up dies with the select that carried it.\n\nAgreed shape:\n\n**The trigger.** The drawn 40px box stays byte-for-byte the reading it\nis today — dot, column title, chevron — but it is a real button now\n(`role=\"combobox\"`, APG select-only pattern), no transparent select on\ntop.\n\n**The panel.** Absolute under the trigger, `role=\"listbox\"`: one row per\ncolumn — title left, `n/limit` count right, over-limit count in warning\nink. Open seeds the active row to the current column. No search row:\ncolumns are a handful by construction.\n\n**Keyboard and dismissal.** The composer combobox's exact cage: arrows\nmove, Home/End jump, Enter/Space pick, Escape closes the panel — not the\ndialog — via preventDefault + stopImmediatePropagation, with the\ndialog's own document listener early-returning on `defaultPrevented`.\nTrigger and rows preventDefault on mousedown; focusout closes; the panel\nscrolls into view. Picking calls the same `onMove(index)` and refocuses\nthe trigger, which survives the card's reparenting because the dialog\nnever unmounts it.",
          "tags": [
            "plugins",
            "kanban"
          ],
          "assignee": [
            "claude"
          ],
          "type": "feature",
          "size": "S",
          "source": "folio#feat/artifact-board-poc",
          "link": "",
          "priority": "",
          "parent": "",
          "blocked_by": [],
          "created": "2026-08-18",
          "milestone": "0.3",
          "artifacts": [],
          "criteria": [
            {
              "text": "the Move-to renders as a button-combobox with a listbox panel; no `<select>` remains in `StatusField`",
              "done": false
            },
            {
              "text": "rows show `title` and `n/limit`, over-limit in warning ink; open lands the active row on the current column",
              "done": false
            },
            {
              "text": "Escape closes the panel and leaves the dialog open; the dialog's document listener early-returns on `defaultPrevented`",
              "done": false
            },
            {
              "text": "picking moves the card, closes the panel, keeps focus on the trigger, and the sr-only announcement still fires",
              "done": false
            },
            {
              "text": "the Created comparison select in the composer stays native; docs stop calling the status field a native picker",
              "done": false
            },
            {
              "text": "pins: combobox trigger in the aside, listbox rows, the Escape cage, the dialog's defaultPrevented return",
              "done": false
            }
          ],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — the dialog's native select joins the custom-dropdown family; supersedes the parked Move-to Escape-guard follow-up.",
              "href": ""
            },
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "f54481e81",
              "note": "shipped: the drawn 40px box is a real combobox with a listbox of columns and their WIP counts; Escape caged with the dialog belted on defaultPrevented; live probe caught the mouse-open focus hole, fixed in both dropdown families; re-review hardened the pins",
              "href": ""
            }
          ],
          "comments": [],
          "phase": "extension",
          "phaseTitle": "Plugin Platform",
          "file": "board/cards/the-move-to-is-a-custom-dropdown.md"
        }
      ]
    },
    {
      "id": "released",
      "title": "Released",
      "limit": null,
      "cards": []
    }
  ]
}
