<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/wordmark-dark.svg">
  <img src="docs/readme/wordmark.svg" alt="Folioh" width="340">
</picture>

### **HTML for people, MD for agents.**

[![Website](https://img.shields.io/badge/Website-folioh.site-blue?color=233153)](https://folioh.site/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-000000?logo=github)](https://github.com/pguijas/folioh)
[![Docs](https://img.shields.io/badge/Docs-Read-233153)](https://folioh.site/docs/)
[![License](https://img.shields.io/github/license/pguijas/folioh)](LICENSE)

| [**Website**](https://folioh.site/) | [**Documentation**](https://folioh.site/docs/) | [**Quick Start**](https://folioh.site/docs/quickstart) | [**Components**](https://folioh.site/docs/components) |
|---|---|---|---|

</div>

-----

## News

- [2026/09] Folioh 0.3: the engine becomes **one native Rust binary**, installed with one line. No Python, no package manager.
- [2026/08] Plugin platform: roadmap, landing and OpenAPI on one extension contract; every page gets a portable Markdown mirror.

## About

Folioh Docs builds documentation for **people and coding agents**. One `docs.yaml` points it at the
source and Markdown guides already in your repository; one build turns them into a static site
with a generated API reference, search and dark mode, plus a Markdown twin of every page that
agents read instead of scraping HTML. Folioh reads your code and never runs it.

> The page says what the code says.

### From source to site

- **API reference from source.** Python docstrings (Google and NumPy), JSDoc and Rust doc comments become pages with signatures, parameter tables and prose; in Python and JavaScript, a type named in a signature links to its page. ([Writing doc comments](https://folioh.site/docs/docstrings))
- **Guides in Markdown or MDX**, with 30+ components: callouts, tabs, steps, file trees, Mermaid, KaTeX, API tables. ([Components](https://folioh.site/docs/components))
- **Search without a service.** Pagefind indexes at build time and the index ships with the export.
- **Theming without forking.** Presets, tokens and a live configurator in the shipped site; overlay template files when that is not enough. ([Theming](https://folioh.site/docs/theming))
- **Built-in integrations.** Landing page, roadmap and OpenAPI switch on with their section in `docs.yaml`. ([Configuration](https://folioh.site/docs/configuration))
- **Plain files out.** GitHub Pages with zero config and a preview per branch; the same export runs on Vercel, Netlify or Docker. ([Deployment](https://folioh.site/docs/deployment))

### Built for agents

- **Every page twice.** `llms.txt`, `llms-full.txt`, a Markdown mirror per page and a typed authoring contract, emitted by the same build. ([Why Folioh](https://folioh.site/docs/why-folioh))
- **Fetched, not scraped.** Every page declares its Markdown mirror as a `text/markdown` alternate and lists it in the sitemap; `_folioh/contract.json` lists the core MDX components with their props, the config keys the project accepts and every route the build emitted.

### What Folioh runs

- **One binary.** `folioh`, for Linux, macOS and Windows. `folioh build` and `folioh serve` render through a bundled Nextra/Next.js template and need Node.js 20.19+ and pnpm 10; the deployed site needs neither.
- **Python, JavaScript and Rust.** Three readers in the binary; TypeScript, then Go, C# and Java, arrive with 0.5 "Every Language" on the roadmap.
- **Not its own reference yet.** Folioh reads Rust now, but the live site still ships landing and guides without an API reference for its own code. That reference is part of 0.5.
- **Project plugins later.** Your own plugins return with the sidecar protocol; the built-in integrations are compiled in.

## Getting Started

```bash
curl -LsSf https://folioh.site/install.sh | sh
```

- [Install Folioh](https://folioh.site/docs/installation)
- [Quick Start](https://folioh.site/docs/quickstart)
- [Configuration](https://folioh.site/docs/configuration)
- [Deployment](https://folioh.site/docs/deployment)
- [Developer Guide](docs/guide/developing.md)
- [Contribution Guide](CONTRIBUTING.md)

## The Repository

One product, one workspace. The engine is the crates; everything beside them is
either the frontend the engine ships, the specification its tests read, or this
site, which is a Folioh project like any other.

```text
folioh/
├── crates/                  the engine: eleven crates, one per boundary
│   ├── folioh-cli/           CLI host, commands, pipeline, terminal UI
│   │   ├── src/bin/folioh.rs the `folioh` binary; it only calls folioh_cli::run
│   │   └── tests/           the black-box suites that run the built binary
│   ├── folioh-config/        docs.yaml: parsing, typing, path containment
│   ├── folioh-docs/          the documentation pipeline over the IR
│   ├── folioh-ir/            ModuleIR, the shape every parser produces
│   ├── folioh-lang-python/   the Python reader
│   ├── folioh-lang-javascript/  the JavaScript reader
│   ├── folioh-lang-rust/     the Rust reader
│   ├── folioh-mdx/           Markdown to MDX and back, the Markdown mirrors
│   ├── folioh-plugins/       the plugin interface, the built-in integrations
│   │                        and the authoring contract
│   ├── folioh-site/          the frontend workspace, theming, the static export
│   └── folioh-watch/         the file watcher behind `folioh serve`
├── template/                the bundled Next.js/Nextra template, embedded in
│                            the binary at compile time and built with pnpm
├── docs.yaml                this site's configuration
├── docs/                    this site's sources
│   ├── guide/               the published guides
│   ├── examples/            the sample projects the guides and tests build
│   ├── components/          components this site's pages use
│   └── readme/              the images above
├── theme/folioh-site/        this site's theme package: the two files it
│                            owns on top of the bundled template
└── install.sh               the installer behind the one-liner above,
                             served from the site root by `public:`
```

Folioh builds its own documentation with the binary this repository produces, so
`docs.yaml`, `docs/` and `theme/` are both the site you are reading and the
integration fixture that proves the engine works.

## Badge

Documenting with Folioh? Say so:

[![Docs by Folioh](https://img.shields.io/badge/docs-by_Folioh-blue?color=233153)](https://github.com/pguijas/folioh)

```md
[![Docs by Folioh](https://img.shields.io/badge/docs-by_Folioh-blue?color=233153)](https://github.com/pguijas/folioh)
```

## Acknowledgment

Folioh renders through [Next.js](https://nextjs.org/) and [Nextra](https://nextra.site/), with
[shadcn/ui](https://ui.shadcn.com/) and [Tailwind CSS](https://tailwindcss.com/) for the component
library, [Pagefind](https://pagefind.app/) for search, and [KaTeX](https://katex.org/) and
[Mermaid](https://mermaid.js.org/) for math and diagrams.

Folioh Pastel takes inspiration from [cojeev](https://000h.cojeev.com/): its organic
shapes, typography, floating docs layout and motion. Thank you to
[Sanjay Kumar (luv-jeri)](https://github.com/luv-jeri) for designing it and sharing
[cojeev-ui](https://github.com/luv-jeri/cojeev-ui) as open source.

## License

MIT. See [LICENSE](LICENSE).
