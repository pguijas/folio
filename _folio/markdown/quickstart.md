# Quick Start

*Go from an existing repository to searchable documentation in a few minutes.*

Folio Docs reads your source and guides without running any of your code. It is
one native binary, so your project does not need Python; `folio build` and
`folio serve` need Node.js 20.19+ and pnpm 10. See [Installation](/docs/installation)
for manual installs and troubleshooting.

### Install Folio

    Install the `folio` binary once with the installer script.

### Initialize your repository

    Let Folio detect the package and create a small docs.yaml.

### Preview the result

    Open the generated site and inspect its HTML and agent-readable outputs.

### Build the static site

    Export plain files that can be deployed anywhere.

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
[CLI Reference](/docs/cli#folio-init) lists what it detects. A minimal configuration
for a Python package looks like this:

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

Only keep source paths that exist. A JavaScript or Rust project uses
`source.javascript` or `source.rust` instead; [Languages](/docs/languages) covers each
reader. The [configuration reference](/docs/configuration) covers exclusions,
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

Deploy `_site/` with the [deployment guide](/docs/deployment).

## Next steps

- [Writing doc comments](/docs/docstrings)
- [Components](/docs/components)
- [Plugins](/docs/plugins)
