---
title: Quick Start
description: Build and preview Folio's own Python documentation site with API reference pages, search, and static output.
---

# Quick Start

*Build and preview a real Folio documentation site from an existing Python repo.*

Folio is installed as a Python CLI, but every build uses the bundled Nextra/Next.js template to render the final static site. Install the CLI first:

```bash
uv tool install folio-docs
```

Folio expects Node.js 20.19+ and pnpm 10 for build and serve commands. If pnpm is not available, activate it with Corepack:

```bash
corepack prepare pnpm@10 --activate
```

<Steps>
  <Step title="Clone a real project">
    Use Folio's own repository so the output includes source code, Markdown guides, components, API reference pages, and config.
  </Step>
  <Step title="Inspect the generated site">
    Start with visual previews of the pages Folio produces instead of reading a long throwaway package example.
  </Step>
  <Step title="Build the static docs">
    Run the build command and inspect the deployable output Folio writes.
  </Step>
</Steps>

## Step 1: Clone a Real Project

The fastest way to understand Folio is to build documentation that already looks like a complete product. This guide uses Folio itself as the sample repository.

```bash
git clone https://github.com/pguijas/folio.git && cd folio
```

If you are already inside a Folio checkout, stay there and run the commands from the repository root.

## Step 2: Preview the Target Output

This preview shows the documentation system you are about to build in one place. It is a small docs-first generated site: guide pages, CLI notes, API reference, source tree, search-ready navigation, and theme-aware content.

<DocPreview
  title="Generated documentation site"
  example="generated-site"
  description="A single compiled example combines guide docs, CLI notes, API output, and the source files that produced it. The landing page is disabled for this first build."
  height={680}
/>

## Step 3: Inspect the Inputs

Folio uses a small set of source files and folders. In the Folio repo, those inputs are already present:

<FileTree tree={`
folio/
  docs.yaml
  docs/
    guide/
      quickstart.md
      configuration.md
      components/
  folio/
    config.py
    cli.py
    generator/
  template/
    components/
    app/
`} />

The important connection is in `docs.yaml`: Markdown guide pages and Python source paths are declared once, then Folio builds both into the same site.

<ConfigPanel
  title="docs.yaml"
  description="The Folio repository documents itself, so the source paths point at the real package and the guide pages."
  fields={[
    { name: "project.name", type: "string", description: "Displayed in the generated site chrome and metadata." },
    { name: "source.python.paths", type: "list[string]", description: "Python packages scanned for modules, classes, functions, and docstrings." },
    { name: "source.docs", type: "list[string]", description: "Markdown directories copied into the guide section." },
  ]}
>
```yaml
project:
  name: "Folio"
  repo: "https://github.com/pguijas/folio"

source:
  python:
    paths:
      - "folio/"
  docs:
    - "docs/guide/"
```
</ConfigPanel>

For a different existing repo, start with the same shape: point `source.python.paths` at your package and `source.docs` at your Markdown guides.

## Step 4: Build the Documentation

Run the build from the project root:

```bash
uv run folio build --clean
```

The build writes an intermediate Nextra app and a deployable static site:

<BuildArtifact
  title="Generated output"
  description="The generated workspace stays separate from the deployable artifact. Folio copies its bundled template into this workspace, runs pnpm there when dependencies need refreshing, and writes the exported site to _site/."
  items={[
    { path: ".build/", kind: "workspace", description: "Intermediate Next.js and Nextra app with generated MDX content." },
    { path: "_site/", kind: "static", description: "Final static output ready for hosting." },
    { path: "_site/llms.txt", kind: "llm", description: "Compact project summary for AI coding assistants." },
    { path: "_site/llms-full.txt", kind: "llm", description: "Complete plain-text documentation export." },
  ]}
/>

## Step 5: Use the Same Pattern in Your Repo

Once you have seen the Folio repo build itself, repeat the pattern in your own project:

```bash
uv add folio-docs
uv run folio init
uv run folio serve
```

Then point `docs.yaml` at your real package and guide folder:

```yaml
source:
  python:
    paths:
      - "src/your_package"
  docs:
    - "docs/"
```

You do not need to create a synthetic sample package first. Use the repo you actually want to document, then add docstrings and Markdown pages where the generated preview shows gaps.

## Advanced: Preview While You Edit

Use the dev server when you are actively working on docs and docstrings with live feedback:

```bash
uv run folio serve
```

Open `http://localhost:4321` and edit one of these inputs:

<Checklist
  title="Good first edits"
  items={[
    { label: "Change a guide page", description: "Edit docs/guide/configuration.md or docs/guide/quickstart.md and watch the page rebuild.", state: "todo" },
    { label: "Improve a docstring", description: "Edit a public function or class under folio/ and check the generated API reference page.", state: "todo" },
    { label: "Adjust navigation", description: "Update docs.yaml or the sidebar ordering when adding a new guide page.", state: "todo" },
  ]}
/>

Verbose mode is useful when something does not appear where you expected:

```bash
uv run folio build --verbose
```

It prints the source paths Folio scans and the pages it writes, which helps diagnose missing modules, excluded files, or incorrect routes.

## What's Next

- **[Configuration](./configuration)**: Full reference for `docs.yaml`.
- **[Writing Docstrings](./docstrings)**: How Folio parses Google-style and NumPy-style docstrings.
- **[Components](./components/index)**: Visual MDX components for richer documentation pages.
- **[Deployment](./deployment)**: Publish the generated `_site/` folder.
