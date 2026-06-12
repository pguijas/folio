---
title: CLI Reference
description: Reference for Folio CLI commands, flags, and workflows including init, build, serve, coverage, and clean.
---

# CLI Reference

*Every command, flag, and option for the `folio` CLI.*

```
folio [OPTIONS] COMMAND [ARGS]
```

Running `folio` with no arguments displays the help text.

<CommandGrid>
  <CommandCard command="folio init" title="Initialize" description="Create docs.yaml for an existing Python project." flags={["--yes"]} href="#folio-init" />
  <CommandCard command="folio build" title="Build" description="Generate MDX, search data, LLM files, and static output." flags={["--clean", "--open", "--verbose"]} href="#folio-build" />
  <CommandCard command="folio serve" title="Serve" description="Start a local authoring server with source watching." flags={["--port", "--open", "--kill-existing"]} href="#folio-serve" />
  <CommandCard command="folio coverage" title="Coverage" description="Measure docstring coverage and enforce a minimum threshold." flags={["--min", "--verbose"]} href="#folio-coverage" />
</CommandGrid>

## Global Options

| Flag | Short | Description |
|------|-------|-------------|
| `--version` | `-V` | Print the installed folio version and exit. |
| `--install-completion` | | Install shell completion for the current shell. |
| `--show-completion` | | Print shell completion code for manual setup. |
| `--help` | | Show the help message and exit. |

```bash
folio --version
```

It prints the installed version, for example `folio 0.2.1`.

## Commands

### `folio init`

Generate a `docs.yaml` configuration file for an existing Python project. This is the recommended way to get started.

```
folio init [DIRECTORY]
```

| Argument / Option | Required | Default | Description |
|--------------------|----------|---------|-------------|
| `DIRECTORY` | No | Current working directory | Path to the project directory where `docs.yaml` will be created. |
| `--yes` / `-y` | No | `false` | Skip all prompts and use detected defaults (useful for CI/scripts). |

**Interactive wizard:**

When run without `--yes`, `folio init` launches an interactive wizard that walks you through configuration:

Interactive terminals use compact inline arrow-key menus for list choices and inline `(Y/n)` hints for short yes/no choices; press `y`/`n` to submit yes/no choices directly. The intro banner includes a sparkle-framed Folio update line that refreshes in place every second while arrow-key prompts are open. Detected project settings are pre-filled from the project scan.

```
$ folio init

 ████████╗ ██████╗ ██╗     ██╗ ██████╗
 ██╔═════╝██╔═══██╗██║     ██║██╔═══██╗
 █████╗   ██║   ██║██║     ██║██║   ██║
 ██╔══╝   ██║   ██║██║     ██║██║   ██║
 ██║      ╚██████╔╝███████╗██║╚██████╔╝
 ╚═╝       ╚═════╝ ╚══════╝╚═╝ ╚═════╝  v0.2.1

   ⚡Incremental builds skip pages whose sources are unchanged⚡

       ╭───────────────────── 🔎 Detected ─────────────────────╮
       │ 🎯 Target     .                                       │
       │ 📦 Project    my-library 1.2.0                        │
       │ 🧬 Source     src/my_library                           │
       │ 🌐 Repo       https://github.com/org/my-library        │
       │ 🐍 Python     3.12                                    │
       │ 🛠️ Framework  Typer package                           │
       │ ✨ Status     Documentation scaffold not found         │
       ╰───────────────────────────────────────────────────────╯

? 🧭 Docstring style      › - Use arrow-keys. Return to submit.
  Google
  NumPy
› Auto-detect
✔ 🧭 Docstring style      › Auto-detect
? 🎨 Visual preset        › - Use arrow-keys. Return to submit.
› Organic Editorial
  Beacon
  Atlas
  Workshop
✔ 🎨 Visual preset        › Organic Editorial

  ✔ Created docs.yaml
  ✔ Created docs/index.md
  ✔ Created .github/workflows/pages.yml
  Next folio serve
```

**What it does:**

1. Checks if `docs.yaml` already exists. If it does, prints a message and exits without overwriting.
2. Detects the project name and version from `pyproject.toml` (if present).
3. Detects the GitHub repo URL from `git remote origin` (if available).
4. Prints created file paths relative to the current shell directory, so `folio init tmp/project` reports `tmp/project/docs.yaml`.
5. Detects the Python source directory by checking, in order:
   - `src/<package_name>/` (src layout)
   - `src/` (generic src directory)
   - `<package_name>/` (flat layout)
   - `<project_name>/` (flat layout with project name)
6. Displays the detected project settings, pre-fills them, then prompts for docstring style and visual preset (or uses defaults with `--yes`).
7. Generates a `docs.yaml` file with the chosen theme preset.
8. Creates a `docs/` directory with a starter `index.md` file if one doesn't exist.
9. Creates a GitHub Pages workflow at `.github/workflows/pages.yml` if it does not already exist.

**Examples:**

```bash
# Interactive setup
folio init

# Non-interactive with defaults
folio init --yes

# Initialize a specific project
folio init /path/to/my-project -y
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Success, or `docs.yaml` already exists (skipped). |

### `folio build`

Parse Python source code and documentation files, then generate a static documentation site.

```
folio build [OPTIONS] [DIRECTORY]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `DIRECTORY` | `PATH` | Current working directory | Project directory containing `docs.yaml`. |

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--project-dir` | | `PATH` | Current working directory | Compatibility option for scripts that prefer named arguments. |
| `--verbose` | `-v` | `flag` | `false` | Show detailed output during the build process. |
| `--config` | `-c` | `TEXT` | `"docs.yaml"` | Path to the config file, relative to the project directory. |
| `--clean` | | `flag` | `false` | Force full rebuild, clearing the `.build/` cache directory. |
| `--open` | `-o` | `flag` | `false` | Serve the built static site locally, open it in your browser, and keep the preview server running until interrupted. |

**What it does:**

1. Loads the config file from the project directory.
2. Parses Python source files and extracts docstrings, class hierarchies, and module structure.
3. Converts Markdown documentation files to MDX.
4. Generates the Nextra site in a `.build/` directory.
5. Runs the Next.js build to produce the final output.

Build output uses the same compact terminal rhythm as `folio init`: a centered Folio banner followed by short status rows for sources, template prep, page generation, link checks, dependencies, export, completion, and the ready output path. Warnings stay attached to their step instead of appearing as raw Python warning traces. During static export, Folio prints the full export log once in a bordered build output panel and also saves it to `.build/.folio-build.log`.

The incremental cache tracks source file hashes plus config, template, and generator inputs. Changing `docs.yaml`, Folio's generator code, or the site template invalidates generated pages even when Python and Markdown sources are unchanged.

**Examples:**

```bash
# Build docs for the current directory
folio build

# Build with verbose output
folio build -v

# Build a project in a different directory
folio build /path/to/project

# Use a custom config file
folio build --config my-docs.yaml

# Build and open a local static preview
folio build --open
```

`folio build --open` is intentionally blocking after the build: it starts a static preview server and waits until you press `Ctrl+C`.

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Build succeeded. |
| `1` | Build failed. Error details are printed to the console. Common causes: missing config file, parse errors, or Next.js build failure. |

### `folio serve`

Build the documentation and start a local development server with hot reloading. This is the primary command during development.

```
folio serve [OPTIONS] [DIRECTORY]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `DIRECTORY` | `PATH` | Current working directory | Project directory containing `docs.yaml`. |

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--project-dir` | | `PATH` | Current working directory | Compatibility option for scripts that prefer named arguments. |
| `--verbose` | `-v` | `flag` | `false` | Show detailed output. |
| `--config` | `-c` | `TEXT` | `"docs.yaml"` | Path to the config file. |
| `--port` | `-p` | `INT` | `4321` | Port for the development server. Fails with a clear message if the port is already occupied. |
| `--open` | `-o` | `flag` | `false` | Open the documentation in your default browser after the server starts. |
| `--clean` | | `flag` | `false` | Force full rebuild, clearing the `.build/` cache directory. |
| `--kill-existing` | | `flag` | `false` | Stop an existing process on the selected port before serving. |

**What it does:**

1. Performs the same build steps as `folio build`.
2. Starts a Next.js development server on the specified port.
3. **File watching:** after the dev server starts, Folio watches your Python and Markdown source files for changes. Edits are automatically detected, the affected pages are regenerated, and the browser updates via hot reload.
4. **Incremental builds:** subsequent `serve` runs reuse cached dependencies (`.build/node_modules/`) and skip `pnpm install` when deps haven't changed.
5. Keeps the server running until interrupted with `Ctrl+C`.

The `--clean` flag forces a full rebuild from scratch, clearing all caches.

**Examples:**

```bash
# Start the dev server
folio serve

# Serve on a custom port and open the browser
folio serve --port 8080 --open

# Serve a different project with verbose output
folio serve ../my-lib -v -o

```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Server stopped cleanly (via `Ctrl+C`). |
| `1` | Failed to start. Usually a missing config file or build error. |

### `folio coverage`

Analyze docstring coverage for configured Python source files.

```
folio coverage [OPTIONS] [DIRECTORY]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `DIRECTORY` | `PATH` | Current working directory | Project directory containing `docs.yaml`. |

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--project-dir` | | `PATH` | Current working directory | Compatibility option for scripts that prefer named arguments. |
| `--config` | `-c` | `TEXT` | `"docs.yaml"` | Path to the config file. |
| `--verbose` | `-v` | `flag` | `false` | List each undocumented symbol. |
| `--min` | | `FLOAT` | `0` | Minimum coverage percentage. Exits with code `1` if coverage is below this value. |

**Examples:**

```bash
folio coverage
folio coverage --min 80
folio coverage --verbose
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Coverage check completed and met the configured threshold. |
| `1` | Config was missing, no modules were found, or coverage was below `--min`. |

### `folio clean`

Remove generated build artifacts and output directories.

```
folio clean [OPTIONS] [DIRECTORY]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `DIRECTORY` | `PATH` | Current working directory | Project directory. |

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--project-dir` | | `PATH` | Current working directory | Compatibility option for scripts that prefer named arguments. |

**What it does:**

Removes two directories:

1. **`.build/`** -- the intermediate Nextra project used during the build process.
2. **The output directory** -- by default `_site/`, or whatever `output` is set to in `docs.yaml`. The clean command reads this value directly from YAML, so cleanup still works if a configured plugin is missing or broken.

If neither directory exists, it prints "Nothing to clean."

**Examples:**

```bash
# Clean the current project
folio clean

# Clean a specific project
folio clean /path/to/project

# Example output:
# Cleaned: .build, _site
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | Always succeeds. |

## Error Messages

Here are common errors you might encounter and what they mean:

**`Error: Config file not found: docs.yaml`**
No `docs.yaml` was found in the project directory. Run `folio init` to create one, or specify the correct path with `--config`.

**`Build failed: ...`**
The build process encountered an error. Run with `--verbose` for detailed output. Common causes include syntax errors in Python source files, invalid YAML in the config, or missing dependencies.

**`docs.yaml already exists, skipping.`**
The `init` command found an existing config file and did not overwrite it. This is informational, not an error.

## Typical Workflow

A typical documentation workflow looks like this:

```bash
# 1. Initialize (one time)
folio init

# 2. Edit docs.yaml to customize settings

# 3. Start the dev server while writing docs
folio serve --open

# 4. Build for production
folio build

# 5. Deploy the _site/ directory to your hosting provider

# 6. Clean up build artifacts when needed
folio clean
```
