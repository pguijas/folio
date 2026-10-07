# Quick Start

*Go from an existing repository to searchable documentation in a few minutes.*

Folioh Docs reads your source and guides without running any of your code. It is
one native binary, so your project does not need Python; `folioh build` and
`folioh serve` need Node.js 20.19+ and pnpm 10. See [Installation](/docs/installation)
for manual installs and troubleshooting.

### Install Folioh

    Install the `folioh` binary once with the installer script.

### Initialize your repository

    Let Folioh detect the package and create a small docs.yaml.

### Preview the result

    Open the generated site and inspect its HTML and agent-readable outputs.

### Build the static site

    Export plain files that can be deployed anywhere.

## 1. Install Folioh

```bash
curl -LsSf https://folioh.site/install.sh | sh
corepack enable pnpm && corepack prepare pnpm@10 --activate   # or: npm install -g pnpm@10
folioh --version
```

## 2. Initialize your repository

Run the wizard from the project you want to document:

```bash
cd your-project
folioh init
```

`folioh init` detects Python, JavaScript, and Rust projects, reads their metadata
and source directories, then writes `docs.yaml`; the
[CLI Reference](/docs/cli#folioh-init) lists what it detects. A minimal configuration
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
folioh serve
```

Open `http://localhost:4321`. The development server watches the source files
of every configured language and the Markdown guides, and rebuilds changed
pages; restart it after editing `docs.yaml`. Its public root also exposes:

- `/llms.txt`, the compact project index;
- `/llms-full.txt`, the expanded text export;
- `/_folioh/markdown/`, the per-page Markdown mirrors.

Use `folioh serve --verbose` when a module or page is missing.

## 4. Build the static site

```bash
folioh build --clean
```

Deploy `_site/` with the [deployment guide](/docs/deployment).

## Next steps

- [Writing doc comments](/docs/docstrings)
- [Components](/docs/components)
- [Plugins](/docs/plugins)
