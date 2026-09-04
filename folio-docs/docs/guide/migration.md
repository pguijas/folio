---
title: Migrating from Sphinx
description: Move from Sphinx to Folio by converting RST content, simplifying configuration, and generating modern Python API docs.
---

# Migrating from Sphinx

*Step-by-step guide to moving your project from Sphinx to Folio.*

## Why migrate

**Simpler configuration.** Sphinx uses a Python `conf.py` file that can grow to hundreds
of lines with complex extension configurations. Folio uses a single `docs.yaml`, and
`folio init` writes one about thirty lines long.

**Modern UI.** Folio generates a responsive, dark-mode-enabled site with a
component-based UI built on Next.js and shadcn/ui. No theme hunting or template
customization required.

**Faster iteration.** The dev server supports hot reload — edit your docstrings and see
changes instantly without running a full rebuild.

**Zero-config API docs.** Point Folio at your source directories and it
automatically generates API reference pages. No `autodoc` directives, no `.. automodule::`
boilerplate.

## Step-by-step migration

### 1. Install Folio

```bash
uv add folio-docs
```

### 2. Initialize configuration

Run the init command in your project root. It detects your project name, version, and
source layout from `pyproject.toml`:

```bash
uv run folio init
```

This creates a `docs.yaml` file. Edit it to point to your Python source directories:

```yaml
project:
  name: "my-project"
  version: "1.0.0"
  repo: "https://github.com/org/my-project"

source:
  python:
    paths:
      - "src/my_project/"
    exclude:
      - "src/my_project/_vendor/"
  docs:
    - "docs/"

nav:
  - "Guide"
  - "API Reference"
```

### 3. Convert existing documentation

If you have hand-written documentation in `.rst` format, convert it to Markdown before
adding it to `source.docs`. Folio does not ship or invoke an RST converter; use your
migration tool of choice, review the generated Markdown, and then let Folio build the
converted pages.

Folio warns about `.rst` files only when those files are still present inside a
directory listed in `source.docs`. It does not emit a warning if the `.rst` files were
already removed before running `folio build` or `folio serve`.

Markdown docs routes use kebab-case URLs. A source file such as
`common_errors/index.md` is published at `/docs/common-errors/`. Folio also generates
underscore aliases for hand-written docs routes, so `/docs/common_errors/` keeps
working after migration. API reference routes are the exception: Python package and
module names keep their original underscores.

### 4. Update Sphinx-style docstrings

Folio supports Google-style and NumPy-style docstrings natively — if your project
uses NumPy-style docstrings, just set `source.python.docstring_style: "numpy"` (or
rely on `"auto"`) and no conversion is needed. Only Sphinx-style docstrings
(`:param name:`) need to be converted. Here is a comparison:

<BeforeAfter
  before={`def connect(host, port=8080):
    """Connect to a server.

    :param host: The hostname.
    :type host: str
    :param port: The port number.
    :type port: int
    :returns: A connection object.
    :rtype: Connection
    :raises ConnectionError: If unreachable.
    """`}
  after={`def connect(host: str, port: int = 8080) -> Connection:
    """Connect to a server.

    Args:
        host: The hostname.
        port: The port number.

    Returns:
        A connection object.

    Raises:
        ConnectionError: If unreachable.
    """`}
  beforeLabel="Sphinx style"
  afterLabel="Google style"
/>

### 5. Remove Sphinx configuration

Once migration is complete, you can remove Sphinx-related files:

- `conf.py`
- `Makefile` (if only used for docs)
- `make.bat`
- `_build/` directory
- `_static/`, `_templates/` directories
- Sphinx from your dependencies

### 6. Build and verify

```bash
folio serve
```

This starts a dev server at `http://localhost:4321` where you can verify your
documentation looks correct.

## Mapping Sphinx concepts to Folio

### conf.py to docs.yaml

| Sphinx `conf.py` | Folio `docs.yaml` |
|-------------------|-------------------------|
| `project = "Name"` | `project.name: "Name"` |
| `version = "1.0"` | `project.version: "1.0"` |
| `extensions = ["autodoc"]` | Not needed (automatic) |
| `html_theme = "furo"` | Built-in theme (see Theming guide) |
| `html_static_path` | Custom assets copied by a plugin or referenced from docs |
| `html_logo` | `theme.logo` |
| `html_favicon` | `theme.favicon` |
| `exclude_patterns` | `source.python.exclude` |
| `autodoc_member_order` | Not configurable (source order) |

### autodoc to automatic generation

In Sphinx, you write explicit directives to pull in API documentation:

```rst
.. automodule:: my_project.core
   :members:
   :undoc-members:
   :show-inheritance:
```

In Folio, you list your source directories and everything is documented
automatically:

```yaml
source:
  python:
    paths:
      - "src/my_project/"
```

No per-module directives needed. Use `__all__` in your Python modules to control which
symbols appear in the documentation.

### RST directives

Folio does not translate RST directives during a build. Convert them before adding the
page to `source.docs`, then review common constructs against this mapping:

**Common manual rewrites:**

| RST Directive | Converted To |
|---------------|-------------|
| `.. code-block:: python` | Fenced code block (` ```python `) |
| `.. note::` | Callout (info) |
| `.. warning::` | Callout (warning) |
| `.. tip::` | Callout (tip) |
| `.. hint::` | Callout (tip) |
| `.. danger::` | Callout (danger) |
| `.. error::` | Callout (danger) |
| `.. important::` | Callout (warning) |
| `.. caution::` | Callout (warning) |
| `.. attention::` | Callout (warning) |
| `.. seealso::` | Callout (info) |
| `.. deprecated::` | Callout (danger) with version |
| `.. versionadded::` | Callout (note) with version |
| `.. versionchanged::` | Callout (note) with version |
| `.. image:: path` | `![path](path)` |
| RST headings (underlines) | Markdown headings (`#`, `##`, etc.) |
| `` ``inline code`` `` | `` `inline code` `` |
| `` :role:`text` `` | `` `text` `` |

**Features that need manual redesign:**

| RST Feature | Status |
|-------------|--------|
| `.. toctree::` | Not needed (auto-generated navigation) |
| `.. include::` | Not supported |
| `.. math::` | Not supported |
| `.. table::` | Use Markdown tables instead |
| `.. raw::` | Not supported |
| `.. tab-set::` / `.. tab-item::` | Convert manually to `<Tabs>` and `<TabItem>` |
| `.. only::` | Not supported |
| Cross-references (`:ref:`, `:doc:`) | Not yet supported |
| Substitutions (`\|name\|`) | Not supported |
| Field lists (`:field:`) | Not supported |
| Footnotes | Not supported |

For Sphinx tab sets, rewrite each block with Folio's MDX tabs components:

````mdx
<Tabs>
  <TabItem label="Python">
    ```python
    import my_library
    ```
  </TabItem>
  <TabItem label="CLI">
    ```bash
    my-library run
    ```
  </TabItem>
</Tabs>
````

For callouts that were written as Markdown blockquotes during migration, use Folio's
`Callout` component directly. Patterns such as `> **Warning:**` should become
`<Callout type="warning">`. For example, convert `> **Warning:** This changes state.`
to:

```mdx
<Callout type="warning">
  This changes state.
</Callout>
```

### Sphinx extensions to Folio features

Many common Sphinx extension use cases are built into Folio. Custom extension authoring is not part of the public MVP surface yet.

| Sphinx Extension | Folio Equivalent |
|-----------------|----------------------|
| `autodoc` | Built-in (automatic) |
| `napoleon` | Built-in (Google style) |
| `viewcode` | Source file + line tracking (built-in) |
| `intersphinx` | Not yet supported |
| `todo` | Not yet supported |
| `coverage` | Not yet supported |
| `doctest` | Not yet supported |
| `sphinx-copybutton` | Built-in (code blocks have copy buttons) |
| Custom extensions | Not public in the MVP |

### make html to folio build

| Sphinx Command | Folio Command |
|---------------|-------------------|
| `make html` | `folio build` |
| `make clean` | `folio clean` |
| `sphinx-autobuild` | `folio serve` |
| `sphinx-quickstart` | `folio init` |

## What works differently

### Sphinx-style docstrings require conversion

Folio supports both Google-style and NumPy-style docstrings. If your project uses
NumPy-style docstrings, set `source.python.docstring_style: "numpy"` in your
`docs.yaml` and no conversion is needed. If your project uses Sphinx (`:param:`) style, you need to
convert them to either Google or NumPy style. This is the most significant migration
effort for projects using Sphinx-style docstrings.

Tools like `pyment` can help automate docstring conversion:

```bash
uv tool run pyment -w -o google src/
```

### Sphinx role cross-references require conversion

Sphinx has an extensive cross-reference system (`:class:`, `:func:`, `:meth:`, etc.) that
creates links between documented symbols. Folio generates API links for parsed type
annotations, but it does not support Sphinx role syntax yet. Role syntax like
`:class:\`MyClass\`` is converted to inline code (`` `MyClass` ``) and should be
replaced with Markdown links where needed.

### No intersphinx

Sphinx's `intersphinx` extension lets you link to other projects' documentation.
Folio does not yet support this. If your docs heavily link to external API
documentation (e.g., linking to Python stdlib docs), those links will need to be
replaced with plain URLs or removed.

### Source order, not alphabetical

Folio documents members in the order they appear in the source file. Sphinx's
`autodoc_member_order` option with alphabetical sorting has no equivalent.

### No RST-only features in docstrings

If your docstrings use RST features like field lists, substitutions, or complex table
markup, they will not be converted. Stick to plain text and Google-style sections in
docstrings.

## Common gotchas

**Docstring parsing errors.** If a docstring does not follow Google style correctly, the
parser falls back to treating the entire text as a plain description. Indentation
matters — section content must be indented under the section header.

**Missing `__init__` docs.** Folio documents `__init__` like any other method. If
you were relying on Sphinx's `autoclass_content = "both"` to merge class and `__init__`
docstrings, you may need to adjust your docstrings.

**Private members.** By default, Folio documents all top-level definitions. Use
`__all__` to control what gets included, or rely on the convention that names starting
with `_` are excluded from `__all__`.

**RST in Markdown files.** If your Markdown files contain RST directives wrapped in
`{eval-rst}` blocks, these are stripped during conversion. Replace them with Markdown
equivalents. There is no `folio migrate` command yet that automatically rewrites
`{eval-rst}` blocks, tab sets, or blockquote-style callouts into native Folio syntax.
Review externally converted Markdown by hand before adding it to `source.docs`.

**Raw `<iframe>` tags are stripped.** The Markdown-to-MDX sanitizer removes raw
`<iframe>`, `<script>`, `<style>`, `<video>`, `<audio>`, `<object>`, and `<embed>` tags
before writing generated MDX. A build can still succeed, but the embed will not render.
Use a normal Markdown link or a reviewed MDX component instead of relying on raw
YouTube or HTML embeds in source Markdown.

**Curly braces in Markdown.** Since Folio outputs MDX (Markdown + JSX), bare
curly braces `{` and `}` in your Markdown files are interpreted as JSX expressions. If
your docs contain literal curly braces (e.g., in code explanations outside of code
blocks), they will need to be escaped or placed in code blocks.

## Feature comparison

| Feature | Sphinx | Folio |
|---------|--------|-------------|
| Python API docs | Via autodoc extension | Built-in, automatic |
| Docstring styles | Google, NumPy, Sphinx | Google, NumPy |
| Configuration | Python (conf.py) | YAML (docs.yaml) |
| Output format | HTML, PDF, ePub, etc. | HTML (Next.js) |
| Theme system | Jinja2 templates | React + shadcn/ui |
| Dark mode | Theme-dependent | Built-in |
| Hot reload dev server | Via sphinx-autobuild | Built-in |
| Search | Built-in | Built-in (Pagefind) |
| Cross-references | Full support | Generated API type links; Sphinx roles not yet |
| Intersphinx | Full support | Not yet |
| RST support | Native | Convert to Markdown before build |
| Markdown support | Via MyST | Native |
| Custom extensions | Extensive plugin ecosystem | Not public in the MVP |
| PDF output | Built-in | Not supported |
| i18n | Built-in | Not yet |
| LLM-friendly output | Not built-in | llms.txt + llms-full.txt |
| Custom components | Jinja2 macros | React/MDX components |
| Setup complexity | High | Low |
| Build speed | Moderate | Fast (Turbopack) |

## Migration checklist

<Checklist
  items={[
    { label: "Install Folio and run folio init", state: "done" },
    { label: "Edit docs.yaml with project details and source paths", state: "done" },
    { label: "Convert Sphinx-style docstrings", description: "Use Google or NumPy style. NumPy-style docstrings are supported with source.python.docstring_style: \"numpy\".", state: "warn" },
    { label: "Convert .rst files to .md", description: "Use the migration converter for common directives or your preferred tooling.", state: "warn" },
    { label: "Replace :ref: and :doc: cross-references", description: "Use Markdown links or inline code where links are not available yet.", state: "todo" },
    { label: "Remove {eval-rst} blocks from Markdown", state: "todo" },
    { label: "Move custom static assets into documented source assets or plugin output", state: "todo" },
    { label: "Run folio serve and verify every page", state: "todo" },
    { label: "Remove Sphinx configuration files and dependencies", state: "todo" },
    { label: "Update CI/CD scripts to use folio build", state: "todo" },
  ]}
/>
