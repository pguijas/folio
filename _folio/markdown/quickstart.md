# Quick Start

*Go from an existing repository to searchable documentation in a few minutes.*

Folio Docs reads your source and guides without importing the package. It needs
Python 3.10+, Node.js 20.19+, and pnpm 10. See [Installation](./installation)
for alternatives and troubleshooting.

### Install Folio

    Install the CLI once as a uv tool.

### Initialize your repository

    Let Folio detect the package and create a small docs.yaml.

### Preview the result

    Open the generated site and inspect its HTML and agent-readable outputs.

### Build the static site

    Export plain files that can be deployed anywhere.

## 1. Install Folio

```bash
uv tool install folio-docs
corepack prepare pnpm@10 --activate
folio --version
```

## 2. Initialize your repository

Run the wizard from the project you want to document:

```bash
cd your-project
folio init
```

`folio init` detects project metadata and Python packages, then writes
`docs.yaml`. A minimal configuration looks like this:

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

Only keep source paths that exist. The [configuration reference](./configuration)
covers exclusions, docstring formats, plugins, and theming.

## 3. Preview the result

```bash
folio serve
```

Open `http://localhost:4321`. The development server watches Python and
Markdown sources and rebuilds changed pages. Its public root also exposes:

- `/llms.txt`, the compact project index;
- `/llms-full.txt`, the expanded text export;
- `/_folio/markdown/`, the per-page Markdown mirrors.

Use `folio serve --verbose` when a module or page is missing.

## 4. Build the static site

```bash
folio build --clean
```

Deploy `_site/` with the [deployment guide](./deployment/index).

## Next steps

- [Writing docstrings](./docstrings)
- [Components](./components/index)
- [Plugins](./plugins/index)
