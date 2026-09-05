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
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "",
          "type": "",
          "size": "",
          "priority": "high",
          "assignee": [],
          "tags": [
            "release"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "serve-watches-docs-yaml-and-the-board",
          "title": "Serve watches docs.yaml and the board",
          "description": "The serve watcher only covers python_sources and doc_sources, so edits to docs.yaml or files under board/ require a manual restart before they show up. Extend the watcher to cover both so every input to the build triggers a rebuild during serve.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "",
          "type": "",
          "size": "",
          "priority": "high",
          "assignee": [],
          "tags": [
            "dx"
          ],
          "created": "2026-07-16",
          "criteria": [
            {
              "text": "changes to docs.yaml trigger a rebuild under serve",
              "done": false
            },
            {
              "text": "changes under board/ trigger a rebuild under serve",
              "done": false
            },
            {
              "text": "no manual restart needed for any build input",
              "done": false
            }
          ],
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "theme-contract-for-plugin-surfaces",
          "title": "Theme contract for plugin surfaces",
          "description": "Presets, tokens, and theme packages must restyle plugin pages (landing, boards) the same way they restyle docs pages. Today plugin surfaces can drift from the active theme; this card defines the token contract plugin pages may rely on so a theme change propagates everywhere without plugin-specific overrides.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "plugin-system-unification",
          "milestone": "0.3",
          "type": "",
          "size": "",
          "priority": "high",
          "assignee": [],
          "tags": [
            "theming",
            "plugins"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "agent-surfaces-technical-plan",
          "title": "Agent surfaces technical plan",
          "description": "The read path for agents, in three layers: formats (Markdown mirrors and llms.txt variants that any crawler or agent can consume), typed export (a versioned intermediate representation that tools can build on), and live surface (MCP and skills served from the static artifacts). The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "project-os-technical-plan",
          "milestone": "0.4",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "spec"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "agpl-license-position",
          "title": "AGPL license position",
          "description": "Write and publish the license position: what AGPL means for generated sites, stated plainly so adopters do not have to guess. The core point is that the output of the generator belongs to its users — their generated site is theirs, and the position document says so explicitly.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "release"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "api-portal-technical-plan",
          "title": "API portal technical plan",
          "description": "Technical plan for the API portal phase. The roadmap promises reference docs that stay truthful to the spec and legible to agents; this card holds the engineering work behind that promise, from the OpenAPI-derived page components through the diff engine that powers changelogs and CI gates, to the playground and doctest tooling that keep examples executable and current.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.8",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "spec"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "broken-links-and-a11y-checks",
          "title": "Broken links and a11y checks",
          "description": "folio check gains internal link and anchor checking, optional external link checking, and an accessibility audit covering image alt text and contrast. The checks are wired in as a build gate so a broken link or a missing alt attribute fails the build instead of shipping.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "project-os-technical-plan",
          "milestone": "0.4",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "quality"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "comparison-pages",
          "title": "Comparison pages",
          "description": "Criteria-first honest comparison pages, shipped on the docs site. This is the one context where competitor names are allowed; everywhere else the copy stands on its own. The comparison leads with the criteria, not the verdict, and every claim made about a competitor or about Folio is verifiable, linked to documentation, a spec, or a reproducible check, so the pages survive scrutiny from the compared parties.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "public-launch-plan",
          "milestone": "0.7",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "launch"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "demo-and-readme",
          "title": "Demo and README revamp",
          "description": "A short demo that builds a real repository's docs and board live, with no staged fixtures, plus a README revamp that carries the docs-and-boards story. The demo shows the end-to-end path from a plain repository to a published docs site and board in one build; the README leads with that same story so the first thirty seconds on the repository page and the first thirty seconds of the demo tell the same thing.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "public-launch-plan",
          "milestone": "0.7",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "launch"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "ecosystem-technical-plan",
          "title": "Plugin catalog technical plan",
          "description": "Technical plan for the Public Beta catalog work. The roadmap promises a plugin catalog outsiders can publish into; this card holds the engineering work behind that promise, covering the plugin catalog and hookspecs that let outsiders extend the system, the eval tooling that keeps docs honest at scale, and the git sync that connects the board to the rest of a team's infrastructure.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.7",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "spec"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "folio-score-cli",
          "title": "Folio score CLI",
          "description": "An open agent-readiness audit runnable against any docs site, whether given a URL or a local directory. It checks llms.txt presence and spec-correctness, .md mirrors, well-known discovery paths, sitemap, and metadata, and produces an honest score against published criteria — no grading on a curve toward Folio-built sites. Exit codes make it usable in CI. It doubles as the migration hook: score your current site, see what is missing, then migrate.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "public-launch-plan",
          "milestone": "0.7",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "launch"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "hidden-pages-and-ignore-rules",
          "title": "Hidden pages and ignore rules",
          "description": "Two levels of page visibility: a hidden: frontmatter flag that keeps a page out of nav and search while leaving it reachable by URL, and an ignore file that excludes content from the build entirely. Visibility is decided at build time, never client-side, so hidden content is not merely styled away.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "project-os-technical-plan",
          "milestone": "0.4",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "core"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "languageprofile-parser-seam",
          "title": "LanguageProfile parser seam",
          "description": "Introduce a LanguageProfile abstraction and a parser registry in core, with Python as the only profile for now. The IR carries language identity, and registering a second profile touches only the registry — nothing else in the pipeline changes. The docs state the contract plainly: new languages are parsers, not toolchains.\n\nThat contract is the constraint, and it rules out the obvious route for every language after TypeScript. Reading Rust through `rustdoc --output-format json` needs a Rust toolchain, Go through `go/doc` needs Go, Java through `javadoc` needs a JDK — each one turns \"add a language\" into \"install an ecosystem\", which is the objection Folio exists to answer for Sphinx-era maintainers. TypeScript is the exception: its compiler is reachable through the Node runtime Folio already requires.\n\nSo the profile for everything else reads a grammar, not an SDK. That keeps the same posture Python already has: `ast` reads annotations as written and infers nothing, and a grammar-based profile behaves identically. The cost is honest and should be written down rather than discovered — a grammar gives syntax, not semantics, so a type that is only knowable by inference will not appear. For reference pages built from signatures and doc comments, that is the same trade Python already makes.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "typescript-technical-plan",
          "milestone": "0.5",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "core",
            "languages"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            },
            {
              "date": "2026-07-29",
              "actor": "claude",
              "ref": "",
              "note": "roadmap 0.5 now names Rust, Go, then the JVM and C#. Recorded why each one's own doc tooling is off the table under the no-toolchain contract, and that the profile reads a grammar instead."
            }
          ]
        },
        {
          "id": "migrations-technical-plan",
          "title": "Migrations technical plan",
          "description": "One-command imports with honest reports: importers for the major documentation ecosystems that convert what they can, report what they could not, and leave the user with a working site rather than a half-migration. The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.6",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "spec"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "preflight-environment-checks",
          "title": "Preflight environment checks",
          "description": "Check node, npm, network access, and paths before starting a build, and fail with instructions rather than tracebacks. A missing or wrong-version dependency should produce a message that names the problem and the fix, not a raw stack trace from deep inside the build.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "dx"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "project-os-technical-plan",
          "title": "Project OS technical plan",
          "description": "The write path for agents plus board maturity: agents move from reading the site to acting on it through a write-MCP and a generated authoring contract, while the board grows the metadata, views, and generated-roadmap machinery it needs to serve as the project's operating layer. The roadmap sells the promise; this card holds the engineering list so the phase can be executed and verified item by item.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.4",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "spec"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "public-launch-plan",
          "title": "Public launch plan",
          "description": "Coordinate the public launch around the first tagged PyPI release: an announcement post, a Hacker News submission, and posts to Python community channels (real names, no abbreviations). The launch carries a single one-sentence story (docs and boards from one build, open source, agent-ready) and every channel repeats it verbatim. Nothing ships to any channel before the tagged release is live and installable.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.7",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "launch"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "readable-build-failures",
          "title": "Readable build failures",
          "description": "Every build failure caused by user input should name the file or config key at fault and state the fix. Raw stack traces are reserved for genuine internal errors; a typo in docs.yaml or a bad frontmatter field must never surface as a traceback.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "dx"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "starter-templates",
          "title": "Starter templates",
          "description": "folio init scaffolds a new project from a small set of maintained templates: library, CLI tool, and API service. Each template is kept deliberately small, is maintained alongside the core, and builds green out of the box — a fresh init followed by a build must succeed with no edits.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "public-launch-plan",
          "milestone": "0.7",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "launch"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "typescript-technical-plan",
          "title": "TypeScript technical plan",
          "description": "Technical plan for TypeScript, the first language of the More Languages phase. The roadmap promises that new languages arrive as parsers, not new toolchains; this card holds the engineering work behind that promise, extending the IR contract with language-aware fields, wiring a pinned typedoc extractor into the same pipeline the Python path uses, and keeping the feature gated until the contract has survived real public exposure.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.5",
          "type": "plan",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "spec"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "versioned-docs-graduation",
          "title": "Versioned docs graduation",
          "description": "The versions: config references tags v0.2.0, v0.1.0, and v0.0.1 that do not exist in git, so versioned builds rest on references that cannot resolve. Create the real tags and graduate versioned builds out of experimental once they build against tags that actually exist.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "",
          "milestone": "0.5",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "release"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "rust-fast-path-for-source-reading",
          "title": "Rust fast path for source reading",
          "description": "Move the hot parsing passes to a native implementation for a large build-time speedup. Before any of it is written, the premise needs a measurement, because on this repository it does not hold: a full parse of Folio's own 45 modules takes 0.105s, while a cold `folio serve` takes about four minutes to reach a served page. The template phase accounts for nearly all of that, so a native parser would save a tenth of a second.\n\nThe idea stays open because the premise may hold on inputs Folio has not been pointed at yet: a repository with thousands of modules, or the Markdown and MDX passes, or the link resolution and search index passes. Profile a large repository first and publish per-phase numbers. Build native code only for a phase the numbers convict.",
          "status": "backlog",
          "statusTitle": "Backlog",
          "parent": "typescript-technical-plan",
          "milestone": "0.5",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "dx",
            "core"
          ],
          "created": "2026-07-27",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-27",
              "actor": "claude",
              "ref": "",
              "note": "carded on request. Measured `parse_python_directory` at 0.105s for 45 modules against a roughly four-minute cold serve, so the current bottleneck is the template phase rather than source reading."
            }
          ]
        }
      ]
    },
    {
      "id": "in-progress",
      "title": "In progress",
      "limit": 3,
      "cards": []
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
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "",
          "milestone": "0.3",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "landing",
            "copy"
          ],
          "created": "2026-07-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            },
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "c894ec7fb",
              "note": "owner reviewed the rendered landing and approved. Final pass in the same session: funnel caption removed, closing statement removed — four sections, the boards close the page."
            }
          ]
        },
        {
          "id": "plugin-system-unification",
          "title": "Plugin system unification",
          "description": "One plugin platform behind every surface. The registry becomes the single source of truth, the default plugins (landing, roadmap, kanban, openapi) are loaded through the same path as project plugins, and the dedicated-page contract is shared so any plugin can claim a page the same way the built-ins do.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "",
          "milestone": "0.3",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "plugins",
            "platform"
          ],
          "created": "2026-07-16",
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
          "artifacts": [
            {
              "pr": 23
            }
          ],
          "comments": [],
          "trail": [
            {
              "date": "2026-07-16",
              "actor": "claude",
              "ref": "",
              "note": "carded in the roadmap de-teching round — technical detail moved off the roadmap."
            }
          ]
        },
        {
          "id": "band-descriptions-never-render",
          "title": "Band descriptions never render",
          "description": "The `description` authored under `roadmap:` and `kanban:` in docs.yaml never\nreaches the public pages. `configure()` stores the output of\n`normalize_roadmap()` / `normalize_kanban()` into `config.extra`, and both\nnormalizers drop the `description` key; `register_extensions()` then reads\n`description` back from the normalized dict and always gets nothing, so\n/roadmap/ and /kanban/ render a bare heading.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "",
          "type": "bug",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "bug",
            "plugins"
          ],
          "created": "2026-08-03",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "",
              "note": "carded from the roadmap and kanban audit; the fix starts in this session."
            },
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "dbd563f22",
              "note": "both normalizers preserve the key, round-trip and public-page tests added; moved in-progress -> in-review. The rendered-page criterion closes on the next build."
            },
            {
              "date": "2026-08-03",
              "actor": "claude",
              "ref": "8d6dfd98b",
              "note": "verified on the rebuilt serve — both bands render their descriptions; last criterion closed."
            }
          ]
        },
        {
          "id": "kanban-single-board-with-filters",
          "title": "Kanban is one board with flexible filters",
          "description": "The public board renders every card in one instance, but the only filter is\na mount-time URL parameter with no visible control: a visitor who lands on a\nmilestone deep link cannot see the filter, change it, or clear it. Cards also\ncarry their full body on the board, which buries the column story. The board\nbecomes: one instance with all cards, an in-page filter system (milestone,\ntag, text) that stays in the URL for deep links, cards that show the title\nonly, and a full card view that opens on click.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "",
          "milestone": "0.3",
          "type": "",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-04",
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
          "artifacts": [
            {
              "doc": "design/research/kanban-references-teardown.md",
              "label": "Reference teardown: SVAR and ReUI"
            }
          ],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction; work starts in this session."
            },
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "bb7e54254",
              "note": "filter rail (milestone, tag, text, URL-synced), title-only cards, card dialog with Escape and focus return; component tests pin the new contract, plugin docs updated. Verified on the rebuilt serve; moved in-progress -> in-review."
            },
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "",
              "note": "owner rejected the visual execution. Four redesign mockups produced for review under design/mockups/kanban/ (folio-editorial, gh-projects, jira, linear + index), all on the real board data and theme tokens, each with working filters and card overlay. Card stays in-review pending the owner's pick."
            },
            {
              "date": "2026-08-04",
              "actor": "claude",
              "ref": "",
              "note": "owner review of the four: the card-as-popup is the keeper across all of them; the folio-editorial direction (technical plate, rule lines, mono apparatus) is rejected outright for the board UI. Synthesis in design/mockups/kanban/proposal.html — jira lanes and raised cards with a centered popup and metadata sidebar, gh token filters, linear keyboard affordances, folio theme tokens."
            },
            {
              "date": "2026-08-05",
              "actor": "claude",
              "ref": "5fb689361",
              "note": "SVAR React Kanban and ReUI Kanban read at the source; verdict is to take neither as a dependency and write the techniques ourselves. Teardown attached as a doc artifact."
            },
            {
              "date": "2026-08-05",
              "actor": "claude",
              "ref": "a86d10ba1",
              "note": "shipped. Cards carry a stable uid and every mutation takes it, so the filter gate on drag is gone — a filtered board is operable. Overlay became uid -> {from, to} with a per-entry staleness check; drop placeholder, undo, facet record, aria-live, focus trap, coarse-pointer move buttons, data-slot seams, and the approved skin. 1027 tests green, tsc clean."
            },
            {
              "date": "2026-08-05",
              "actor": "claude",
              "ref": "f5fc1b818",
              "note": "adversarial review of the rewrite, 28 findings, 18 refuted, 9 fixed — the facet token parser committed mid-word, the drag payload typed card ids into the filter field, the filter input had no visible focus, repeated announcements were silent, \"/\" was bound page-wide, the focus trap leaked forward, and touch move buttons covered card titles in the miniatures."
            },
            {
              "date": "2026-08-10",
              "actor": "claude",
              "ref": "",
              "note": "the board takes the landing's voice. Ten app-like studies were rejected as gaudy; the owner asked for editorial and pointed at the landing, and measuring it showed the board was already speaking the same language with the colour drained out — the column names were the landing's eyebrow at 12px/0.08em in grey instead of 11px/0.14em in the accent. Shipped: a masthead (mono blue eyebrow over a 36px sentence-case headline) replacing the 14px label, no lane fills or lane borders, cards opening with the roadmap step their milestone names, and the type scale cut to the landing's own. Home and Roadmap left the toolbar. Measured at 1440: 10 cards above the fold against 9 before, because dropping the card description the popup already carries paid for the masthead. Studies under design/mockups/board-minimal/."
            },
            {
              "date": "2026-08-07",
              "actor": "claude",
              "ref": "",
              "note": "technical audit of the shipped board, then every finding fixed. Measured, not guessed: the sticky toolbar ran 83px at desktop but 183px at 360px, so it now holds two rows at every width (facets collapse below md, actions below xl). The live region spoke once per keystroke (six for six characters) and now speaks once the typing settles. The dialog's scrolling body was not a tab stop, so a long trail was unreachable without a mouse. The board behind the open card is inert. `role=\"list\"` no longer holds the empty-state paragraph, which some tools dropped outright. Contrast: the card count sat at 2.3:1 and the milestone label at 4.2:1 in dark. The coarse-pointer pin is gone — it hid every milestone on every phone to serve a control the dialog already carries — and the milestone now steps aside on the same condition that paints the move buttons, which is the keyboard overlap the audit found. Seven font sizes became two on the board surface; the column names moved to the label register so the board's h1 is finally its only heading, at zero added height. Six unicode characters used as icons became drawn marks on ColumnGlyph's 16-unit grid. The hard-coded amber became a real `--warning` token, which no single value could serve in both modes."
            }
          ]
        },
        {
          "id": "filter-composer-full-height-rail",
          "title": "The composer is a full-height rail beside the board",
          "description": "The composer opens as a popup under the filter bar, five columns wide. With\none control per field the grid lost its balance: a tall status list beside a\nlone priority checkbox beside three floating selects, and Created wrapped\nunderneath. The owner's direction: the composer becomes a toggleable panel\noccupying the full height of the board's left side, and the popup dies.\n\nAgreed shape:\n\n**Structure.** Below the filter bar the board area becomes a two-column\ngrid: a ~17rem composer rail and the board. Open, the board narrows;\nclosed, the rail's column is gone and the board takes the full width. The\nfilter bar stays above, spanning everything; the existing filter glyph at\nits left edge is the toggle (`aria-expanded`/`aria-controls`). The rail is\nsticky below the bar with its own scroll. Sections stack in one column —\nstatus, priority, type, milestone, assignee, tag, created — with the\n\"Also\" chips and \"Clear the filter\" at the foot. The controls themselves\n(`PanelRow`, `PanelSelect`, `PanelTagInput`) do not change; the popup's\npositioning (`absolute top-full`, the 52vh cap, the five-column grid) dies.\n\n**Behavior.** Closed by default, no persistence. Escape inside the rail\ncloses it and returns focus to the toggle, as the popup did. Below `lg`\nthere is no room to push: the same panel renders as a fixed left drawer\n(same width, shadow); click outside or Escape closes it. `/` keeps\nfocusing the expression field. This is layout only — the language, the\nrewrite helpers, and the no-second-store invariant are untouched.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "0.3",
          "type": "feature",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — full-height left rail replacing the popup; filter bar stays above; closed by default; drawer below lg."
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "b1f9ff595",
              "note": "rail shipped: two-column grid on lg, fixed drawer below, popup positioning gone; controls untouched; suite green"
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "7a2d34273",
              "note": "final review fixes: rail clears the sticky navbar via --nextra-navbar-height calc, Escape no longer tears down the rail with the card dialog, rem breakpoint, conditional aria-controls, honest test names"
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "3283521fe",
              "note": "owner review: the rail now spans the full height — the filter bar narrows into the grid's right column; staging banner stays full-width above"
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "ca7daff27",
              "note": "owner review: the rail surface stretches to the board's foot; the controls follow the scroll inside it"
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "a0d490b80",
              "note": "review fix: the bar's render gate returns to compact-only, so the static page keeps the bar and its h1; stale docstring rewritten"
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "a28e88878",
              "note": "owner found the rail overflowing: the public view never defined --nextra-navbar-height, so the rail computed against 0px under a fixed 64px navbar; the view layout now declares 4rem beside its pt-16"
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "ba3eaae45",
              "note": "owner redirected after the sticky rounds: the public board is now an app workspace — viewport-height section under the navbar, rail as a fixed-height floating panel with its own scroll, canvas scrolls both axes; docs embeds keep the in-flow layout"
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "ad58b1dc3",
              "note": "owner: left margin asymmetric — the workspace now runs full-bleed, the rail truly touches the edge it was drawn for, and the canvas keeps 24px on both sides"
            }
          ]
        },
        {
          "id": "filter-composer-one-control-per-field",
          "title": "The composer draws one control per field, and cards carry type and assignee",
          "description": "The filter composer draws every field the same way: a column of tri-state\ncheckboxes. That shape is right for the two fields you scan (status,\npriority) and wrong for everything else — a single-value field wants a\ndropdown, an open list wants an input. And two facts a team board runs on,\nwho owns a card and what kind of work it is, barely exist: `assignee` is in\nthe format but invisible on the board, and type has no field at all.\n\nThe change, agreed with the owner (simple and plain as the rule; menu plus\ndata model, no browser write path):\n\n**Data model.** `type: <value>` joins the card frontmatter — single value,\nfree vocabulary, the types that exist are the types cards use, exactly like\n`milestone`. The loader carries it, the plugin emits it into\n`lib/kanban-data.ts`, `folio kanban show` prints it, the cardfile docs\ndescribe it. No vocabulary validation.\n\n**The card.** The face's metadata line gains the type, and `@assignee`\nshows when set; cards without them render unchanged. The dialog gains a\nType row beside the existing metadata.\n\n**The composer.** One control per field, all derived from the parsed\nexpression and writing back through it — typed text and clicked controls\ncannot disagree, because there is no second store. Status and priority stay\ntri-state checkbox lists with predictive counts. Type, milestone, and\nassignee become native selects: the board's values with counts, plus \"any\"\nto clear the term. Tag becomes an input with the board's tags as\nsuggestions and removable chips; adding ORs into the tag term. Created\nkeeps its comparator and date. Whatever a control cannot draw (multi-value\nin a select, negations, free text) stays listed as removable \"Also\" chips.\nFields with no values on the board do not render.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "0.3",
          "type": "feature",
          "size": "",
          "priority": "",
          "assignee": [],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-16",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — design agreed in session: menu + data model, `type` as a free single-value field, one control per field in the composer, simplicity as the rule."
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "ccdc7ea07",
              "note": "type field end to end (loader, data module, CLI, card, composer); composer redrawn one control per field; docs and template updated; suite green"
            },
            {
              "date": "2026-08-16",
              "actor": "claude",
              "ref": "f202d4832",
              "note": "final whole-branch review: 0 critical; docs field list + composer semantics fixed, tag chips from term alternatives, dateTerm double-draw gone, rewrite helpers now executed by the language tests"
            }
          ]
        },
        {
          "id": "cards-carry-assignees-source-and-size",
          "title": "Cards carry assignees, a source, and a size",
          "description": "A card can name one assignee, and nothing says where the work lives or how\nbig it is. The owner wants three more dimensions: several people on one\ncard, a source (the repo or branch the work belongs to — one branch per\nproject, for example), and a size. Assignee and tags already exist; this\ncard completes the set.\n\nAgreed shape:\n\n**`assignee` accepts a list.** The same key, two forms: `assignee: ana`\nstill works, `assignee: [ana, bo]` joins it. The loader normalizes both to\na list — trimmed strings, duplicates dropped, order preserved — and the\nemitted TypeScript changes `assignee: string` to `assignee: string[]`. No\nnew `assignees` key.\n\n**`size` is a closed scale.** `size: M`, case-insensitive, normalized to\nuppercase. Anything outside S / M / L / XL is a hard loader error — the\nsame treatment as an unknown status: `folio build` stops and\n`folio kanban check` goes red naming the file and the allowed values. The\none closed field in the model, by the owner's explicit choice.\n\n**`source` is free text.** `source: folio#feat/x`, a URL, a repo name —\na free scalar with the same treatment as `type` (non-scalars warned and\nignored).\n\n**The card.** The face's bottom line shows every assignee (`@ana @bo`) and\nthe size as a small bordered chip (`M`, `XL`). Source stays off the face —\nthe metadata line already carries type · phase · milestone. The dialog\ngains Size and Source rows (a source starting with `http(s)://` renders as\na link) and the Assignee row joins the list. Cards without the new fields\nrender exactly as before.\n\n**The composer.** `size` joins `CHECK_FIELDS` — tri-state checkboxes like\nstatus and priority, only the values in use, in scale order S→XL, with\ncounts. `source` joins `SELECT_FIELDS`. Assignee keeps its select; a card\nwith two assignees counts for both values. The filter language does not\nchange — `size:m,l` and `-source:none` fall out of `FILTER_FIELDS`; URLs\nwith colons take quotes, which the language already has.\n\n**The CLI.** `update --set` accepts `size` (validated against the scale),\n`source`, and `assignee=ana,bo` (comma split, as `add --tags` already\ndoes). The `show` table gains a Size column; source is not a column.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "0.3",
          "type": "feature",
          "size": "L",
          "priority": "",
          "assignee": [
            "peter",
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-17",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — several assignees per card, a free source field, and a closed S/M/L/XL size; design approved in session."
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "a3859e2b6",
              "note": "shipped: assignee lists, free source, and the closed size scale — loader to composer to CLI, docs and skill updated, v1 export byte-identity pinned by an executed test"
            }
          ]
        },
        {
          "id": "filter-composer-searchable-combobox",
          "title": "The composer selects become searchable comboboxes",
          "description": "The composer's four value pickers (type, milestone, assignee, source) are\nnative selects. The owner doesn't like them: no search when a field has\nmany values, and the OS look sits oddly in the rail. They become one custom\ncombobox — no new dependency, ARIA listbox pattern, search appearing only\nwhen it earns its row.\n\nAgreed shape:\n\n**The control.** A `PanelCombobox` beside the other Panel* controls in\n`kanban-board.tsx`; `PanelSelect` dies. Trigger button styled like the\nselect it replaces (h-7, border, current value or \"any\", chevron),\n`aria-haspopup=\"listbox\"` and `aria-expanded`. Open: an absolute panel\nunder the trigger — full width, border, shadow, max-height with its own\nscroll, scrolled into view so it never hides under the rail's fold.\nOptions: **any** first (clears), then the board's values with\n`value — count` in board order, and a typed value the board does not have\nstill drawn as an extra option. The active option is highlighted and\n`aria-selected`.\n\n**The search.** At 8+ options, an input at the top of the panel filters by\ncase-insensitive substring; ArrowDown moves from the input into the list.\nUnder 8, the list is direct — no input row.\n\n**Keyboard and dismissal.** Enter/Space/ArrowDown open. Arrows move,\nEnter picks, Escape closes and returns focus to the trigger WITHOUT\nclosing the rail (the handler stops propagation before the rail's own\nEscape listener — fixing the parked \"rail selects lack the Escape guard\"\nfollow-up). Click outside closes. Picking closes and rewrites the\nexpression exactly as today: the `onSelect(value | null)` contract and the\ncomposer invariant (the expression is the only filter state) do not change.\n\n**What stays native.** The Created comparison select (3 fixed options) and\nthe dialog's Move-to select (focus must survive the card reparenting). The\n\"now the only menu on the board\" comment at the Move-to select is updated,\nbecause it stops being true.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "filter-composer-one-control-per-field",
          "milestone": "0.3",
          "type": "feature",
          "size": "M",
          "priority": "",
          "assignee": [
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-17",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — the native selects don't please; custom combobox with search at 8+ options; design approved in session."
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "9ff993995",
              "note": "shipped: the four pickers are one custom combobox — search at 8+ values, opens on the current value, Escape and focus caged properly after the final review caught the delegation trap"
            }
          ]
        },
        {
          "id": "the-roadmap-is-the-milestone-registry",
          "title": "The roadmap is the milestone registry",
          "description": "`milestone` is free text and formats.md admits the debt: \"a full registry\nwith validation is planned, not shipped\". The registry already exists —\nthe roadmap's phases carry `version` — and `_resolve_roadmap_phases`\nalready joins the two halves. What's missing is the complaint when the\njoin fails.\n\nAgreed shape (owner chose warning severity):\n\n**The rule.** When the config declares a roadmap with at least one\nversioned phase, a card whose `milestone` matches no phase version gets a\nwarning naming the card and the known versions — surfaced yellow by\n`folio kanban check`, never breaking the build. The \"future milestone the\nroadmap has not reached yet\" case stays legal, loudly. Boards without a\nroadmap section (or with no versioned phases) stay exactly as free as\ntoday: no warning, no coupling.\n\n**The seams.** The check lives beside `_resolve_roadmap_phases`, which\nalready computes `by_version` — one loop, one `warnings.warn` per\nunclaimed milestone. The `v`/`V` prefix stripping it already does applies.\nformats.md's milestone row drops the \"planned, not shipped\" confession and\nstates the shipped rule.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "0.3",
          "type": "feature",
          "size": "S",
          "priority": "",
          "assignee": [
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-17",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — standardize milestone against the roadmap's versions, warning severity; queued behind the combobox card."
            },
            {
              "date": "2026-08-17",
              "actor": "claude",
              "ref": "982eebe24",
              "note": "shipped: unclaimed milestones warn grouped against the roadmap's versions; check replays the resolution and shows them yellow; docs drop the planned-not-shipped note"
            }
          ]
        },
        {
          "id": "cards-carry-comments",
          "title": "Cards carry comments",
          "description": "The trail records what happened; nothing on a card holds a conversation.\nThe owner wants comments — and, correcting the first mockup, wants them\n**as their own separated section, like the artifacts**: a full-width band\nof the dialog, not prose squeezed between criteria and trail.\n\nAgreed shape:\n\n**The section.** `## Comments` in the card markdown, one line per\ncomment: `- YYYY-MM-DD @actor: text`. The trail's grammar family minus\nthe ref — a comment argues, it does not point at a commit. Strict\nwriter, tolerant reader: a bullet that misses the grammar warns at build\nand still renders as prose, exactly like a malformed trail line.\n\n**The band.** Between the body grid and the artifacts band: bubble glyph,\n`Comments · N`, one row per comment — mono date, bold `@actor`, the text\nwith its inline markdown rendered. Same scroll cap and keyboard stop as\nthe artifacts band. No comments, no band: a mail without replies shows\nno empty thread.\n\n**The pipeline.** Loader parses the section; normalizer carries\n`comments: {date, actor, text}[]`; the emitted interface grows\n`KanbanComment`; `boardToYaml` exports `comments:` only when present so\nv1 exports stay byte-identical. CLI: `folio kanban comment <id> \"text\"\n[--by NAME] [--commit]` — `--by` defaults to git user.name, the writer\nvalidates date/actor/single-line text, and the line appends at the\nsection's tail through the same surgery as trail.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "0.3",
          "type": "feature",
          "size": "M",
          "priority": "",
          "assignee": [
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-18",
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
          "artifacts": [],
          "comments": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "text": "dogfood: this very thread renders in the band this card ships"
            }
          ],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — comments as their own separated section like the artifacts; conversation distinct from the trail's record."
            },
            {
              "date": "2026-08-19",
              "actor": "claude",
              "ref": "bb05cf990",
              "note": "shipped: ## Comments parsed/normalized/exported, the thread band above the artifacts, folio kanban comment with git-user default; review reproduced the Rich-markup crash and the case-blind heading hole, both fixed with the trail sharing the cure"
            }
          ]
        },
        {
          "id": "the-card-dialog-reads-like-a-mail",
          "title": "The card dialog reads like a mail",
          "description": "The dialog opens on `board/cards/<id>.md` — a mono file path presiding\nover the strip that should identify the card — while the artifacts, the\none thing a card produces, sit as grey chips at the bottom of the rail.\nThe owner wants the hierarchy inverted, designed over HTML mockups in\nsession: the card reads like a mail, attachments at the foot.\n\nAgreed shape:\n\n**The header.** The title presides, `Esc` / a pen icon-button (edit) /\nthe close button at the right edge, all three 28px tall. The path leaves\nthe header and becomes the `Card` field in the rail — still the link,\nnow with the file glyph, sitting with the other facts.\n\n**The attachments band.** A full-width strip under the body grid, above\nthe footer: `Artifacts · N` with a paperclip, then one tile per artifact\n— a kind-tinted icon square (doc blue, pr green, url warm, api gold,\nfile ink), the label, and the full target in mono. A dashed ghost tile\nteaches the gesture: `folio kanban attach <id> --doc <path>`, shown\nwhenever moves are live; with no artifacts the band is the ghost alone.\n`ArtifactChip` dies.\n\n**Colour and marks.** Section labels get their small glyphs (check for\ncriteria, clock for trail, paperclip for artifacts), tags take a soft\naccent tint, and the status value carries a column dot. Priority keeps\nits existing ends-of-the-scale treatment. The footer keeps only the\nstaged-move export line; editing lives in the header now.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "kanban-single-board-with-filters",
          "milestone": "0.3",
          "type": "feature",
          "size": "M",
          "priority": "",
          "assignee": [
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-18",
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
          "artifacts": [
            {
              "doc": "docs/guide/plugins/kanban/index.md",
              "label": "Board guide — the dialog section"
            }
          ],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — dialog oriented to attaching artifacts, designed over HTML mockups iterated in session (title presides, mail-style attachment band, kind colours)."
            },
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "1895a736c",
              "note": "shipped: title presides the header with Esc/pen/close, the path is the rail's linked Card field, artifacts close the dialog as a mail-style band (kind-tinted tiles + attach ghost on cardfile boards); review wave fixed labelled-PR numbers, band scroll, and the missing pins; docs + screenshot regenerated"
            }
          ]
        },
        {
          "id": "the-dialog-renders-markdown",
          "title": "The dialog renders its markdown",
          "description": "Cards are markdown files, and the dialog prints their prose raw: a\ndescription authored as `**The header.**` shows its asterisks, backticked\ncommands show their backticks. The owner hit it on the board today. The\nbody is the one place a card talks, and it talks in the format the file\nalready is.\n\nAgreed shape:\n\n**The subset, from usage.** A scan of this board's own cards: bold and\ninline code everywhere, multi-paragraph descriptions common, zero em,\nlinks, or lists. Rendered: `` `code` ``, `**bold**`, `[text](https://…)`\nwith the scheme guard the repo already applies everywhere (anything not\nhttp(s) stays literal text), and paragraphs split on blank lines. No raw\nHTML ever — tokens become React nodes, never `dangerouslySetInnerHTML`.\nUnmatched marks stay literal: a stray asterisk is prose, not a crash.\n\n**The seams.** A pure `parseInlineMd(text) → MdToken[]` tokenizer beside\nthe other extracted-and-executed helpers, exercised by the node harness\nlike the filter language; a small renderer maps tokens to `<code>`,\n`<strong>`, `<a>`. Applied to the dialog description (paragraphs), each\nacceptance criterion, and each trail note. Faces stay title-only; raw\nstrings stay raw in data, export, and filters.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "the-card-dialog-reads-like-a-mail",
          "milestone": "0.3",
          "type": "feature",
          "size": "M",
          "priority": "",
          "assignee": [
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-18",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — the dialog must render the markdown the cards are written in; subset drawn from the board's real usage."
            },
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "269d5eb22",
              "note": "shipped: parseInlineMd tokenizes code/bold/http-links with paragraphs on blank lines, tokens become React nodes (no innerHTML path); review reproduced the double-backtick mangle on this very card and it now parses as CommonMark quoting; adversarial ReDoS claim refuted at card scale"
            }
          ]
        },
        {
          "id": "the-move-to-is-a-custom-dropdown",
          "title": "The Move-to is a custom dropdown",
          "description": "The dialog's one control is the board's last native select. Owner call:\nit becomes a custom dropdown like the composer's comboboxes — the OS\nmenu sits oddly in the redesigned dialog, and the parked \"Move-to Escape\nguard is theater\" follow-up dies with the select that carried it.\n\nAgreed shape:\n\n**The trigger.** The drawn 40px box stays byte-for-byte the reading it\nis today — dot, column title, chevron — but it is a real button now\n(`role=\"combobox\"`, APG select-only pattern), no transparent select on\ntop.\n\n**The panel.** Absolute under the trigger, `role=\"listbox\"`: one row per\ncolumn — title left, `n/limit` count right, over-limit count in warning\nink. Open seeds the active row to the current column. No search row:\ncolumns are a handful by construction.\n\n**Keyboard and dismissal.** The composer combobox's exact cage: arrows\nmove, Home/End jump, Enter/Space pick, Escape closes the panel — not the\ndialog — via preventDefault + stopImmediatePropagation, with the\ndialog's own document listener early-returning on `defaultPrevented`.\nTrigger and rows preventDefault on mousedown; focusout closes; the panel\nscrolls into view. Picking calls the same `onMove(index)` and refocuses\nthe trigger, which survives the card's reparenting because the dialog\nnever unmounts it.",
          "status": "in-review",
          "statusTitle": "In review",
          "parent": "the-card-dialog-reads-like-a-mail",
          "milestone": "0.3",
          "type": "feature",
          "size": "S",
          "priority": "",
          "assignee": [
            "claude"
          ],
          "tags": [
            "plugins",
            "kanban"
          ],
          "created": "2026-08-18",
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
          "artifacts": [],
          "comments": [],
          "trail": [
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "",
              "note": "carded from owner direction — the dialog's native select joins the custom-dropdown family; supersedes the parked Move-to Escape-guard follow-up."
            },
            {
              "date": "2026-08-18",
              "actor": "claude",
              "ref": "f54481e81",
              "note": "shipped: the drawn 40px box is a real combobox with a listbox of columns and their WIP counts; Escape caged with the dialog belted on defaultPrevented; live probe caught the mouse-open focus hole, fixed in both dropdown families; re-review hardened the pins"
            }
          ]
        }
      ]
    },
    {
      "id": "released",
      "title": "Released",
      "limit": null,
      "cards": []
    }
  ],
  "note": "Hierarchy in `parent` is INVENTED for prototyping; the real board has none yet."
};
