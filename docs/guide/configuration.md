---
title: Configuration
description: Configure Folio source inputs, project metadata, theme options, search, LLM files, and deployment settings in docs.yaml.
---

# Configuration

*Complete reference for every option in your `docs.yaml` file.*

## Quick Start

Start with the project name and at least one source input. Folio needs Python
source paths or Markdown docs to generate pages:

<ConfigPanel
  title="Minimum docs.yaml"
  description="This is enough for Folio to scan source, write _site/, and enable the default docs theme."
  fields={[
    { name: "project.name", type: "string", description: "The product name shown in navigation, metadata, and generated pages." },
    { name: "source.python.paths", type: "list[string]", description: "Python packages or modules to scan." },
    { name: "source.docs", type: "list[string]", description: "Markdown guide directories to include." },
  ]}
>
```yaml
project:
  name: "my-library"

source:
  python:
    paths:
      - "src/my_library"
  docs:
    - "docs"
```
</ConfigPanel>

This scans your Python package and Markdown guides, outputs to `_site/`, and enables dark mode.

## Full Reference

Here is every available section and field.

### project

Project metadata shown in the navbar, page titles, and generated output.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `string` | `"Untitled"` | Project name displayed in the navbar and page titles. If missing or empty, a warning is emitted and `"Untitled"` is used. |
| `version` | `string` | `"0.0.0"` | Version string shown in the docs header. |
| `repo` | `string` | `""` | URL to the source repository (e.g. GitHub). Enables "Edit this page" links in the generated site. |
| `repo_ref` | `string` | `"main"` | Branch, tag, or commit used for generated source links. |
| `url` | `string` | `""` | Public site URL for sitemap, canonical metadata, and social previews. It does not control local routing or static asset paths. |

```yaml
project:
  name: "my-library"
  version: "2.0.0"
  repo: "https://github.com/org/my-library"
  repo_ref: "main"
```

### source

Controls where folio looks for source code and documentation files.

### deploy

Controls deployment-specific path handling. Most sites can omit this section. Use it when the static site is published under a subpath such as `/my-repo`.

Base path priority is:

1. `FOLIO_BASE_PATH` environment variable.
2. `deploy.base_path` in `docs.yaml`.
3. GitHub Pages inference when `deploy.provider: "github-pages"` or `FOLIO_DEPLOY_PROVIDER=github-pages` is active in GitHub Actions.
4. No base path.

`folio serve` stays rooted at `/` unless `FOLIO_BASE_PATH` is explicitly set.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `"github-pages" \| string` | `""` | Enables provider-specific inference. For GitHub Pages project sites, Folio infers `/{repo}` from `GITHUB_REPOSITORY`; user or organization pages like `owner.github.io` stay at `/`. |
| `base_path` | `string` | `""` | Explicit static asset base path such as `"/docs"` or `"/my-repo"`. Use `"/"` for a root deployment. |

```yaml
deploy:
  provider: "github-pages"
```

For custom domains or reverse proxies, set the base path explicitly:

```yaml
deploy:
  base_path: "/"
```

#### source.python

The `python` key can be either a mapping (recommended) or a simple list of paths.

**Mapping form (recommended):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `paths` | `list[string]` | `[]` | Directories containing Python source code to document. Each path is resolved relative to the project directory. |
| `exclude` | `list[string]` | `[]` | Glob patterns or directory paths to exclude from documentation. Useful for skipping tests, vendored code, or internal modules. |
| `docstring_style` | `string` | `"auto"` | Docstring format to parse. Options: `"auto"`, `"google"`, `"numpy"`. |

<ConfigPanel
  title="source.python"
  description="Use the mapping form when you need exclusions or a specific docstring parser."
  fields={[
    { name: "paths", type: "list[string]", description: "Python source directories to scan." },
    { name: "exclude", type: "list[string]", default: "[]", description: "Glob patterns or directories to skip." },
    { name: "docstring_style", type: "string", default: "auto", description: "Docstring parser: auto, google, or numpy." },
  ]}
>
```yaml
source:
  python:
    paths:
      - "src/my_library"
    exclude:
      - "**/test_*.py"
      - "src/my_library/_internal/"
    docstring_style: "numpy"
```
</ConfigPanel>

**List form (shorthand):**

You can also pass a plain list of paths. In this case, no exclude patterns are applied:

```yaml
source:
  python:
    - "src/my_library"
    - "src/my_library_utils"
```

#### source.docs

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `docs` | `list[string]` | `[]` | Directories containing Markdown (`.md`) documentation pages. These are converted to MDX and included in the site alongside the API reference. |

```yaml
source:
  docs:
    - "docs/"
```

`.rst` files are migration inputs, not build inputs. Convert them to Markdown before placing them in `source.docs`; Folio warns when `.rst` files are present in a docs source directory.

### output

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output` | `string` | `"_site"` | Directory where the generated documentation site is written. Resolved relative to the project directory. Removed by `folio clean`. |

```yaml
output: "build/docs"
```

Folio keeps an incremental manifest in `.build/`. The manifest includes source hashes plus config, template, and generator fingerprints, so changing `docs.yaml` or the generator invalidates stale generated pages automatically.

### theme

Controls the visual appearance of the generated documentation site.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `preset` | `string` | `"organic-editorial"` | Default visual preset for the generated site. `folio init` offers `organic-editorial`, `beacon`, `atlas`, and `workshop`; advanced users can use any preset id available in the bundled theme library. |
| `dark_mode` | `bool` | `true` | Enable the dark mode toggle. When enabled, users can press `d` to switch between light and dark themes. |
| `logo` | `string` | `""` | Path to a logo image file displayed in the navbar. Resolved relative to the project directory. |
| `favicon` | `string` | `""` | Path to a favicon file. Resolved relative to the project directory. |

```yaml
theme:
  preset: "organic-editorial"
  dark_mode: true
  logo: "docs/assets/logo.svg"
  favicon: "docs/assets/favicon.ico"
```

### search

Controls the built-in full-text search powered by [Pagefind](https://pagefind.app). Search is enabled by default, appears in the docs navbar, and opens with `Cmd+K` on macOS or `Ctrl+K` on Windows/Linux.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `bool` | `true` | Enable or disable the navbar search. Set to `false` to hide search entirely. |
| `placeholder` | `string` | `""` | Custom placeholder text for the search input. When empty, the default "Search documentation..." is used. |

```yaml
search:
  enabled: true
  placeholder: "Search documentation..."
```

To disable search completely:

```yaml
search:
  enabled: false
```

### nav

An ordered list of strings defining the top-level navigation sections. The order here determines the order in the navbar. `"API Reference"` is typically generated automatically from your Python sources.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nav` | `list[string]` | `[]` | Top-level navigation sections. |

```yaml
nav:
  - "Introduction"
  - "Getting Started"
  - "API Reference"
  - "Changelog"
```

### llm

Controls generation of [llms.txt](https://llmstxt.org/) files for AI consumption.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `generate_llms_txt` | `bool` | `true` | Generate an `llms.txt` summary file in the output directory. This is a condensed index of your documentation for LLMs. |
| `generate_llms_full_txt` | `bool` | `true` | Generate an `llms-full.txt` file containing the full text of all documentation pages. |

```yaml
llm:
  generate_llms_txt: true
  generate_llms_full_txt: false
```

## Path Resolution

In CLI commands, relative paths in `docs.yaml` are resolved from the active project directory. When you run `folio build /path/to/project` or `folio build --project-dir /path/to/project`, that directory becomes the base for config paths. If you call `load_config()` directly, file plugin paths are resolved from the directory containing the config file.

For example, given this structure:

```
my-project/
  docs.yaml
  src/
    my_lib/
      __init__.py
  docs/
    index.md
```

The config `source.python.paths: ["src/my_lib"]` resolves to `/path/to/my-project/src/my_lib`.

## Config Validation

folio validates your config file and warns about issues:

- **Unknown top-level keys** produce a warning listing the unrecognized keys. Core top-level keys are: `project`, `source`, `output`, `theme`, `nav`, `llm`, `search`, and `deploy`.

- **Missing or empty `project.name`** produces a warning and defaults to `"Untitled"`.

- **Missing config file** raises a `FileNotFoundError` with the path that was expected.

- **MVP-disabled features** are excluded from public docs, API reference, search, sitemap, and LLM output until the feature is ready to publish as beta.

These are warnings, not errors -- the build will still proceed with defaults where possible.

## Common Patterns

### Monorepo Setup

When your Python package lives in a subdirectory of a larger repository:

```yaml
project:
  name: "my-service"
  repo: "https://github.com/org/monorepo"

source:
  python:
    paths:
      - "packages/my-service/src/my_service"
    exclude:
      - "**/test_*.py"
      - "**/conftest.py"
  docs:
    - "packages/my-service/docs/"

output: "packages/my-service/_site"
```

### Excluding Test Files

Keep test files out of your API reference:

```yaml
source:
  python:
    paths:
      - "src/"
    exclude:
      - "**/test_*.py"
      - "**/tests/"
      - "**/conftest.py"
      - "src/my_lib/_fixtures/"
```

### Custom Output Directory

Write the built site to a specific location for CI/CD deployment:

```yaml
output: "build/site"
```

### Multiple Python Source Directories

Document code spread across multiple directories:

```yaml
source:
  python:
    paths:
      - "src/core"
      - "src/plugins"
      - "src/utils"
```

### Minimal Docs-Only Site

If you just want to serve Markdown documentation without Python API reference:

```yaml
project:
  name: "My Docs"

source:
  docs:
    - "docs/"

nav:
  - "Guide"
  - "FAQ"
```
