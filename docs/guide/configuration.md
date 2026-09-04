---
title: Configuration
description: Configure Folio source inputs, project metadata, theme options, custom templates, search, LLM files, and deployment settings in docs.yaml.
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
| `repo` | `string` | `""` | URL to the source repository (e.g. GitHub). Used for source links and project metadata. |
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
| `name` | `string` | `""` | Optional project preset display name. When set with project theme data, Folio adds a Project group to the configurator. |
| `description` | `string` | `""` | Optional project preset description. |
| `preview` | `mapping` | `{}` | Optional `light` and `dark` swatch colors for the project preset preview. |
| `radius` | `string` | `""` | Default radius choice for the theme configurator. Must be one of `"0"`, `"0.3rem"`, `"0.5rem"`, `"0.75rem"`, or `"1rem"`, or a named alias (`"none"`, `"sm"`, `"md"`, `"lg"`, `"full"`); any other value fails config validation. |
| `tune` | `mapping` | `{}` | Default configurator choices such as font, accent, surface, width, rhythm, borders, code blocks, and radius. |
| `style` | `mapping` | `{}` | Safe layout and typography CSS custom property overrides. |
| `tokens` | `mapping` | `{}` | Safe light/dark CSS variable overrides for shadcn tokens and project tokens. |
| `header` | `mapping` | `{}` | Docs header brand, badge, repository link, search visibility, theme toggle, and project action. |
| `variants` | `mapping` | `{}` | Project-owned configurator controls with options, swatches, previews, style overrides, and token overrides. Capped at 256 option combinations across all controls (the product of each control's option count); larger products fail config validation. |
| `package` | `string` | `""` | Local theme package directory copied over the bundled template before generated content and metadata are injected. |

```yaml
theme:
  preset: "organic-editorial"
  dark_mode: true
  logo: "docs/assets/logo.svg"
  favicon: "docs/assets/favicon.ico"
  tune:
    font: "geist"
    width: "wide"
```

See [Theming](./theming/index) for the ownership model, safe personalization
options, theme packages, and custom templates.

### template

Expert escape hatch for replacing the bundled Folio frontend with a project-owned
template. Omit this section to use the default Folio template.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | `string` | `""` | Local Next/Nextra-compatible template directory. Resolved relative to the project directory. Must stay inside the project and cannot point at `.build/` or the output directory. |
| `overlay_path` | `string` | `""` | Directory of files layered on top of the bundled template (overlay files win; missing files fall back to the bundled template). Mutually exclusive with `path`: if both are set, `path` wins and the overlay is ignored with a warning. Held to the same location guards as `path`. |
| `docs_route_base` | `string` | `"/docs"` | Public route where generated documentation pages are served. Folio rewrites generated links, search URLs, sitemap entries, canonical metadata, LLM output, and the copied Next.js docs route to this path. |
| `params` | `mapping` | `{}` | Arbitrary JSON-serializable values exposed to the template as build-time data. Folio does not interpret these values. |

```yaml
template:
  path: "docs-template"
  docs_route_base: "/reference/docs"
  params:
    navbarVariant: "dense"
    productName: "Acme SDK"
```

Custom templates own layout, CSS, JavaScript, package dependencies, routing
chrome, search UI, and the meaning of `template.params`. Folio still owns the
generated MDX content, `_meta.ts` files, search index, Markdown exports, and
static export pipeline. See [Custom Templates](./theming/custom-templates) for
the full contract and required file structure.

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

An ordered list of strings defining the top-level sidebar sections. `Guide`
keeps all authored pages together in their normal order. `API Reference` and
`Source Code` both place the generated source tree, which keeps the stable
`/api-reference/` route. Other labels order a matching top-level page or folder;
unknown labels are ignored rather than creating dead routes.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `nav` | `list[string]` | `[]` | Top-level navigation sections. |

```yaml
nav:
  - "Introduction"
  - "Getting Started"
  - "Source Code"
  - "Changelog"
```

### sidebar

Controls generated sidebar section behavior. Generated groups start collapsed by
default (`sidebar.default_collapsed: true`). Set `default_collapsed: false` if you
want generated groups to start expanded.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_collapsed` | `bool` | `true` | Render generated folder entries with Nextra's `open: false` state so sidebar sections start collapsed. Leaf pages are unchanged. Set to `false` to expand generated groups. |

```yaml
sidebar:
  default_collapsed: false # expand generated groups instead of collapsing them
```

By default, Folio emits object entries in generated `_meta.ts` files for folders:

```ts
export default {
  "components": {
    "title": "Components",
    "theme": { "collapsed": true },
  },
}
```

This applies to generated guide folders and API reference folder groups. It does not
change the route for folder index pages, and it does not collapse individual leaf
pages.

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

Every page is also written as plain Markdown under `_folio/markdown/`, linked from
the page head as a `text/markdown` alternate and listed in the sitemap. These mirrors
are lossy on purpose: complex component props, such as an entire data table, do
not survive. Prose, headings, lists, code blocks, Mermaid source, component
children, and useful labels from simple cards do. Treat a mirror as the page's
portable text, not as a pixel-equivalent copy of the page.

### components

Custom React components to include in the generated site. Registered components are copied into Folio's generated component namespace and exposed to MDX without requiring manual imports in Markdown pages. For registering components from Python (together with data modules, layouts, and views), see the [plugins guide](./plugins/authoring) — for a handful of component files, `components:` is the lighter option.

Each list entry is either a **directory path** or a **named component spec**:

| Entry form | Type | Description |
|------------|------|-------------|
| Directory | `string` | Path to a directory, relative to the project directory. Every top-level `.tsx`/`.jsx` file in it is registered as a component named after its PascalCased file stem (`hero.tsx` → `Hero`, `my-chart.tsx` → `MyChart`). Each file must have a named export matching the derived name. |
| Named spec | `mapping` | A single component file with an explicit name, source path, and options. |

Named spec fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | JSX name exposed to MDX and plugin views. |
| `from` | `string` | Path to the `.tsx` or `.jsx` component file, relative to the project directory. |
| `export` | `string` | Export name in the source file. Defaults to `name`. |
| `expose.mdx` | `bool` | Make the component available in docs MDX. Defaults to `true`. |

```yaml
components:
  - "docs/components"          # every top-level .tsx/.jsx in the directory
  - name: "Hero"
    from: "docs/widgets/hero.tsx"
    export: "Hero"
    expose:
      mdx: true
```

Validation is loud: a directory that does not exist fails the build, a directory without any `.tsx`/`.jsx` files produces a warning, and a `from:` file that does not exist fails the build when components are copied into the workspace. If two source files share the same filename stem, Folio generates distinct component import paths automatically.

> **Upgrade note:** earlier releases gated `components:` behind an experimental feature flag and silently ignored the key when the flag was off. Now that the key is always active, a malformed value — a non-list value (`components: "docs/components"` must be `components: ["docs/components"]`), or a list entry that is neither a path string nor a `{name, from}` mapping — fails config loading for every command (`folio build`, `folio serve`, ...). If an upgrade suddenly reports a `components` error, fix the key's shape or remove it.

A component whose name matches a Folio builtin (for example `Callout`) replaces the builtin and emits a warning; two `components:` entries (or a config entry and a plugin component) with the same name raise an error.

### plugins

Python plugins that extend the build pipeline. See the [plugins guide](./plugins/authoring) for the hook reference and registration forms.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `plugins` | `list[string]` | `[]` | Plugin identifiers: a Python module path (e.g. `"my_plugin"`) or a relative file path starting with `./` (e.g. `"./plugins/custom.py"`). |

```yaml
plugins:
  - "my_docs_plugin"
  - "./plugins/post_build_hook.py"
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

- **Unknown top-level keys** produce a warning listing the unrecognized keys. Core top-level keys are: `project`, `source`, `output`, `theme`, `template`, `nav`, `sidebar`, `llm`, `search`, `plugins`, `components`, and `deploy`.

- **Missing or empty `project.name`** produces a warning and defaults to `"Untitled"`.

- **Missing config file** raises a `FileNotFoundError` with the path that was expected.

- **MVP-disabled features** are excluded from public docs, API reference, search, sitemap, and LLM output until the feature is ready to publish as beta.

These are warnings, not errors — the build will still proceed with defaults where possible.

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
