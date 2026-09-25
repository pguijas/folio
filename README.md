<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/wordmark-dark.png">
  <img src="docs/readme/wordmark.png" alt="Folio" width="340">
</picture>

### **HTML for people, MD for agents.**

[![Website](https://img.shields.io/badge/Website-pguijas.github.io%2Ffolio-111113)](https://pguijas.github.io/folio/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-000000?logo=github)](https://github.com/pguijas/folio)
[![Docs](https://img.shields.io/badge/Docs-Read-111113)](https://pguijas.github.io/folio/docs/)
[![License](https://img.shields.io/github/license/pguijas/folio)](LICENSE)

| [**Website**](https://pguijas.github.io/folio/) | [**Documentation**](https://pguijas.github.io/folio/docs/) | [**Quick Start**](https://pguijas.github.io/folio/docs/quickstart) | [**Components**](https://pguijas.github.io/folio/docs/components) |
|---|---|---|---|

</div>

-----

## News

- [2026/09] Folio 0.3: the engine becomes **one native Rust binary**, installed with one line. No Python, no package manager.
- [2026/08] Plugin platform: roadmap, landing and OpenAPI on one extension contract; every page gets a portable Markdown mirror.

## About

Folio Docs builds documentation for **people and coding agents**. One `docs.yaml` points it at the
source and Markdown guides already in your repository; one build turns them into a static site
with a generated API reference, search and dark mode, plus a Markdown twin of every page that
agents read instead of scraping HTML. Folio reads your code and never runs it.

> The page says what the code says.

### From source to site

- **API reference from source.** Python docstrings (Google and NumPy), JSDoc and Rust doc comments become pages with signatures, parameter tables and prose; in Python and JavaScript, a type named in a signature links to its page. ([Writing doc comments](https://pguijas.github.io/folio/docs/docstrings))
- **Guides in Markdown or MDX**, with 30+ components: callouts, tabs, steps, file trees, Mermaid, KaTeX, API tables. ([Components](https://pguijas.github.io/folio/docs/components))
- **Search without a service.** Pagefind indexes at build time and the index ships with the export.
- **Theming without forking.** Presets, tokens and a live configurator in the shipped site; overlay template files when that is not enough. ([Theming](https://pguijas.github.io/folio/docs/theming))
- **Built-in integrations.** Landing page, roadmap and OpenAPI switch on with their section in `docs.yaml`. ([Configuration](https://pguijas.github.io/folio/docs/configuration))
- **Plain files out.** GitHub Pages with zero config and a preview per branch; the same export runs on Vercel, Netlify or Docker. ([Deployment](https://pguijas.github.io/folio/docs/deployment))

### Built for agents

- **Every page twice.** `llms.txt`, `llms-full.txt`, a Markdown mirror per page and a typed authoring contract, emitted by the same build. ([Why Folio](https://pguijas.github.io/folio/docs/why-folio))
- **Fetched, not scraped.** Every page declares its Markdown mirror as a `text/markdown` alternate and lists it in the sitemap; `_folio/contract.json` lists the core MDX components with their props, the config keys the project accepts and every route the build emitted.

### What Folio runs

- **One binary.** `folio`, for Linux, macOS and Windows. `folio build` and `folio serve` render through a bundled Nextra/Next.js template and need Node.js 20.19+ and pnpm 10; the deployed site needs neither.
- **Python, JavaScript and Rust.** Three readers in the binary; TypeScript arrives with 0.4 "Every Reader", Go, C# and Java later on the roadmap.
- **Not its own reference yet.** Folio reads Rust now, but the live site still ships landing and guides without an API reference for its own code. That reference is part of 0.4.
- **Project plugins later.** Your own plugins return with the sidecar protocol; the built-in integrations are compiled in.

## Getting Started

```bash
curl -LsSf https://pguijas.github.io/folio/install.sh | sh
```

- [Install Folio](https://pguijas.github.io/folio/docs/installation)
- [Quick Start](https://pguijas.github.io/folio/docs/quickstart)
- [Configuration](https://pguijas.github.io/folio/docs/configuration)
- [Deployment](https://pguijas.github.io/folio/docs/deployment)
- [Developer Guide](docs/guide/developing.md)
- [Contribution Guide](CONTRIBUTING.md)

## The Repository

One product, one workspace. The engine is the crates; everything beside them is
either the frontend the engine ships, the specification its tests read, or this
site, which is a Folio project like any other.

```text
folio/
├── crates/                  the engine: eleven crates, one per boundary
│   ├── folio-cli/           CLI host, commands, pipeline, terminal UI
│   │   ├── src/bin/folio.rs the `folio` binary; it only calls folio_cli::run
│   │   └── tests/           the black-box suites that run the built binary
│   ├── folio-config/        docs.yaml: parsing, typing, path containment
│   ├── folio-docs/          the documentation pipeline over the IR
│   ├── folio-ir/            ModuleIR, the shape every parser produces
│   ├── folio-lang-python/   the Python reader
│   ├── folio-lang-javascript/  the JavaScript reader
│   ├── folio-lang-rust/     the Rust reader
│   ├── folio-mdx/           Markdown to MDX and back, the Markdown mirrors
│   ├── folio-plugins/       the plugin interface, the built-in integrations
│   │                        and the authoring contract
│   ├── folio-site/          the frontend workspace, theming, the static export
│   └── folio-watch/         the file watcher behind `folio serve`
├── template/                the bundled Next.js/Nextra template, embedded in
│                            the binary at compile time and built with pnpm
├── docs.yaml                this site's configuration
├── docs/                    this site's sources
│   ├── guide/               the published guides
│   ├── examples/            the sample projects the guides and tests build
│   ├── components/          components this site's pages use
│   └── readme/              the images above
├── theme/folio-site/        this site's theme package: the two files it
│                            owns on top of the bundled template
└── install.sh               the installer behind the one-liner above,
                             served from the site root by `public:`
```

Folio builds its own documentation with the binary this repository produces, so
`docs.yaml`, `docs/` and `theme/` are both the site you are reading and the
integration fixture that proves the engine works.

## Badge

Documenting with Folio? Say so:

[![Docs by Folio](https://img.shields.io/badge/docs-by_Folio-111113)](https://github.com/pguijas/folio)

```md
[![Docs by Folio](https://img.shields.io/badge/docs-by_Folio-111113)](https://github.com/pguijas/folio)
```

## Acknowledgment

Folio renders through [Next.js](https://nextjs.org/) and [Nextra](https://nextra.site/), with
[shadcn/ui](https://ui.shadcn.com/) and [Tailwind CSS](https://tailwindcss.com/) for the component
library, [Pagefind](https://pagefind.app/) for search, and [KaTeX](https://katex.org/) and
[Mermaid](https://mermaid.js.org/) for math and diagrams.

## License

MIT. See [LICENSE](LICENSE).
