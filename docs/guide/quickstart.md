---
title: Quick Start
description: Generate and preview documentation for an existing project.
---

# Quick Start

*Go from an existing repository to searchable documentation in a few minutes.*

Folio Docs reads your source and guides without running any of your code. It is
one native binary, so your project does not need Python; `folio build` and
`folio serve` need Node.js 20.19+ and pnpm 10. See [Installation](./installation)
for manual installs and troubleshooting.

<Steps>
  <Step title="Install Folio">
    Install the `folio` binary once with the installer script.
  </Step>
  <Step title="Initialize your repository">
    Let Folio detect the package and create a small docs.yaml.
  </Step>
  <Step title="Preview the result">
    Open the generated site and inspect its HTML and agent-readable outputs.
  </Step>
  <Step title="Build the static site">
    Export plain files that can be deployed anywhere.
  </Step>
</Steps>

## 1. Install Folio

```bash
curl -LsSf https://pguijas.github.io/folio/install.sh | sh
corepack enable pnpm && corepack prepare pnpm@10 --activate   # or: npm install -g pnpm@10
folio --version
```

## 2. Initialize your repository

Run the wizard from the project you want to document:

```bash
cd your-project
folio init
```

`folio init` detects Python, JavaScript, and Rust projects, reads their metadata
and source directories, then writes `docs.yaml`; the
[CLI Reference](./cli#folio-init) lists what it detects. A minimal configuration
for a Python package looks like this:

<ConfigPanel
  title="docs.yaml"
  description="Folio reads these paths; it never imports or executes the package."
  fields={[
    { name: "project.name", type: "string", description: "Name shown in the generated site." },
    { name: "source.python.paths", type: "list[string]", description: "Python packages scanned for public symbols." },
    { name: "source.docs", type: "list[string]", description: "Markdown directories published as guides." },
  ]}
>
```yaml
project:
  name: "your-project"

source:
  python:
    paths:
      - "src/your_package"
  docs:
    - "docs/"
```
</ConfigPanel>

Only keep source paths that exist. A JavaScript or Rust project uses
`source.javascript` or `source.rust` instead; [Languages](./languages) covers each
reader. The [configuration reference](./configuration) covers exclusions,
docstring formats, the built-in integrations, and theming.

## 3. Preview the result

```bash
folio serve
```

Open `http://localhost:4321`. The development server watches the source files
of every configured language and the Markdown guides, and rebuilds changed
pages; restart it after editing `docs.yaml`. Its public root also exposes:

- `/llms.txt`, the compact project index;
- `/llms-full.txt`, the expanded text export;
- `/_folio/markdown/`, the per-page Markdown mirrors.

Use `folio serve --verbose` when a module or page is missing.

## 4. Build the static site

```bash
folio build --clean
```

<BuildArtifact
  title="Generated output"
  description="The workspace is disposable; the static output is the artifact you deploy."
  items={[
    { path: ".build/", kind: "workspace", description: "Generated frontend workspace and development cache." },
    { path: "_site/", kind: "static", description: "Deployable HTML, assets, search, and agent outputs." },
    { path: "_site/llms.txt", kind: "llm", description: "Compact project context for agents." },
    { path: "_site/_folio/markdown/", kind: "llm", description: "One discoverable Markdown mirror per page." },
  ]}
/>

Deploy `_site/` with the [deployment guide](./deployment/index).

## Next steps

- [Writing doc comments](./docstrings)
- [Components](./components/index)
- [Plugins](./plugins/index)
