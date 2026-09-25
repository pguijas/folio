---
title: Configuration
description: Configure Folio source inputs, project metadata, theme options, custom templates, search, LLM files, and deployment settings in docs.yaml.
---

# Configuration

*Complete reference for every option in your `docs.yaml` file.*

## Quick Start

Start with the project name and at least one source input. Folio needs source
paths or Markdown docs to generate pages:

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
| `version` | `string` | `"0.0.0"` | Version string shown in the docs header. Quote it (`version: "1.0"`): an unquoted `1.0` is a YAML number, not a string, and fails the load. |
| `repo` | `string` | `""` | URL to the source repository (e.g. GitHub). Used for source links, the navbar repository link, the "Question? Give us feedback" link on docs pages (it opens an issue there) and project metadata. Without it, none of these links is shown. |
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

#### source.python

The `python` key can be either a mapping (recommended) or a simple list of paths.

**Mapping form (recommended):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `paths` | `list[string]` | `[]` | Python package directories, or a conventional `src/` import root. Each path is resolved relative to the project directory. |
| `exclude` | `list[string]` | `[]` | Glob patterns or directory paths to exclude from documentation. Useful for skipping tests, vendored code, or internal modules. |
| `docstring_style` | `string` | `"auto"` | Docstring format to parse. Options: `"auto"`, `"google"`, `"numpy"`. An unknown value warns and falls back to Google. |

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

When `src/` itself is listed and is not a Python package, Folio treats it as an
import root. A file such as `src/tools.py` publishes as `tools`, and
`src/my_library/client.py` publishes as `my_library.client`; Folio does not add a
synthetic `src.` prefix. A path that names a package directly, such as
`src/my_library`, continues to use that directory as the package name.

**List form (shorthand):**

You can also pass a plain list of paths. In this case, no exclude patterns are applied:

```yaml
source:
  python:
    - "src/my_library"
    - "src/my_library_utils"
```

#### source.javascript

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `paths` | `list[string]` | required | Directories with `.js`, `.mjs` or `.cjs` sources. Each path is resolved relative to the project directory. |
| `exclude` | `list[string]` | `[]` | Glob patterns or file/directory paths to skip. |

```yaml
source:
  javascript:
    paths:
      - "web/src"
    exclude:
      - "web/src/vendor"
```

Folio names a module after its path (`utils/format.js` is `utils.format`, and
an `index.js` takes its directory's name), reads the JSDoc comment above each
export, and publishes what the file exports under `api-reference/javascript/`.
`node_modules` is never read, and a `.jsx` file is skipped with a warning.

#### source.rust

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `paths` | `list[string]` | required | Crate directories, a workspace holding them, or a crate's `src/`. Each path is resolved relative to the project directory. |
| `exclude` | `list[string]` | `[]` | Glob patterns or file/directory paths to skip. |

```yaml
source:
  rust:
    paths:
      - "crates/core/src"
```

Folio reads each crate's `Cargo.toml` for its name, follows the `pub mod`
declarations from `lib.rs` or `main.rs`, and publishes the public items under
`api-reference/rust/`.

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

### versions and i18n

Not available in this release; ignored with a warning. A project can keep
either key in `docs.yaml`: the build warns and carries on without it.

### output

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output` | `string` | `"_site"` | Directory where the generated documentation site is written. Resolved relative to the project directory. Removed by `folio clean`. |

```yaml
output: "build/docs"
```

Folio keeps an incremental manifest in `.build/`. The manifest includes source hashes plus config, template, and generator fingerprints, so changing `docs.yaml` or the generator invalidates stale generated pages automatically.

### public

Repository files served verbatim from the site root, such as an installer script or a file that needs a stable URL.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `public` | `list[string]` | `[]` | Project-relative files copied to the root of the built site under their own file name. `folio serve` serves them from `/` too. |

```yaml
public:
  - "install.sh"
  - "docs/changelog.md"
```

A file that does not exist fails the build with `public file not found: <absolute path>`. A path outside the project directory fails with `public must stay within the project directory`; a path under `.build/` or the output directory fails with `public cannot point inside the .build directory` or `public cannot point inside the output directory`. Folio's own site serves `install.sh` this way.

### theme

Controls the visual appearance of the generated documentation site.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `preset` | `string` | `"organic-editorial"` | Default visual preset for the generated site. `folio init` offers `organic-editorial`, `beacon`, `atlas`, and `workshop`; it may also be any built-in id, one a theme package or overlay declares, or a new id that `theme.name`, `theme.tokens` or `theme.style` defines. Anything else stops the build and names the nearest id. |
| `dark_mode` | `bool` | `true` | Enable the dark mode toggle. When enabled, users can press `d` to switch between light and dark themes; `false` keeps the site light, with no mode controls, toggles or `d` shortcut, and `theme.header.theme_toggle` then warns. Must be a YAML boolean; an explicit `null` is an error. |
| `logo` | `string` | `""` | Path to a logo image shown in the docs navbar beside the project name, under `deploy.base_path`. Resolved relative to the project directory; a missing file stops the build. |
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
| `package` | `string` \| `mapping` | `""` | Theme package copied over the bundled template before generated content and metadata are injected. A string is a directory in the project. A mapping (`git`, `rev`, `digest`, optional `path`) fetches a published package and verifies its tree against the digest. See [Theme Packages](./theming/theme-packages#install-a-package-someone-else-published). |

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
| `enabled` | `bool` | `true` | Enable or disable the navbar search. Set to `false` to hide search entirely. Must be a YAML boolean; an explicit `null` is an error. |
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
| `default_collapsed` | `bool` | `true` | Render generated folder entries with Nextra's `open: false` state so sidebar sections start collapsed. Leaf pages are unchanged. Set to `false` to expand generated groups. Must be a YAML boolean; an explicit `null` is an error. |

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

Both keys must be YAML booleans; an explicit `null` is an error.

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

Every entry resolves relative to the project directory and must stay inside
it, directory or spec `from`/`path` alike: a component is trusted frontend code,
held to the rule `theme.package` already obeys.

Custom React components to include in the generated site. Registered components are copied into Folio's generated component namespace and exposed to MDX without requiring manual imports in Markdown pages. This is how a site adds its own components.

Each list entry is either a **directory path** or a **named component spec**:

| Entry form | Type | Description |
|------------|------|-------------|
| Directory | `string` | Path to a directory, relative to the project directory. Every top-level `.tsx`/`.jsx` file in it is registered as a component named after its PascalCased file stem (`hero.tsx` → `Hero`, `my-chart.tsx` → `MyChart`). Each file must have a named export matching the derived name. |
| Named spec | `mapping` | A single component file with an explicit name, source path, and options. |

Named spec fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | JSX name exposed to MDX. |
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

A malformed value — a non-list value (`components: "docs/components"` must be `components: ["docs/components"]`), or a list entry that is neither a path string nor a `{name, from}` mapping — fails config loading for every command (`folio build`, `folio serve`, ...).

A component whose name matches a Folio builtin (for example `Callout`) replaces the builtin and emits a warning; two `components:` entries (or a config entry and a component of a built-in plugin) with the same name raise an error.

### Built-in integrations

The [landing page](./plugins/landing), the [roadmap](./plugins/roadmap) and OpenAPI ship in the `folio` binary; [Plugins](./plugins/index) covers each. Each one activates through its own top-level section in `docs.yaml` and stays inert without it; there is no `plugins:` list.

```yaml
roadmap:
  phases:
    - id: "foundation"
      version: "0.1"
      title: "Foundation"
      status: "shipped"
      layer: "Source analysis"
      summary: "Source in, documented site out."

openapi:
  sources:
    - path: "openapi.yaml"
```

Project plugins loaded from your own repository: Not available in this release.

## Path Resolution

In CLI commands, relative paths in `docs.yaml` are resolved from the active project directory. When you run `folio build /path/to/project` or `folio build --project-dir /path/to/project`, that directory becomes the base for config paths.

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

folio validates your config file. A few problems stop the load; everything else is a warning, and the build proceeds with defaults where possible:

- **Duplicate keys** anywhere in the file fail the load.

- **Typed keys** are checked. String keys such as `project.version` must be quoted YAML strings (`version: "1.0"`); boolean keys (`theme.dark_mode`, `llm.*`, `search.enabled`, `sidebar.default_collapsed`) must be YAML booleans. An explicit `null` on a typed key is an error.

- **Missing config file** stops the command with an error naming the path that was expected.

- **Unknown top-level keys** produce a warning listing the unrecognized keys. Core top-level keys are: `project`, `source`, `output`, `public`, `theme`, `template`, `nav`, `sidebar`, `llm`, `search`, `components`, and `deploy`, plus the sections of the built-in integrations: `landing`, `roadmap`, and `openapi`. `versions` and `i18n` are recognised and [ignored with a warning](#versions-and-i18n).

- **Unknown keys inside a core section** (`project`, `source`, `theme`, `template`, `llm`, `deploy`, `sidebar`, `search`, `components`) produce a warning too, naming the nearest valid key when one is close: `Unknown project keys in docs.yaml: vesion (did you mean 'version'?)`. The `landing`, `roadmap` and `openapi` sections are not checked in this release: a typo there is ignored without a warning. An unknown `source.python.docstring_style` warns and falls back to Google.

- **The `plugins:` key** warns with exactly `project plugins are not available in this release; the plugins key is ignored`. The `configKeys` list in the authoring contract (`/_folio/contract.json`) never includes `plugins`.

- **Missing or empty `project.name`** produces a warning and defaults to `"Untitled"`.

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
