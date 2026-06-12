---
title: Installation
description: Install Folio, verify Python and Node.js requirements, and prepare the CLI for local documentation builds.
---

# Installation

*Install Folio and start the CLI.*

## Install Folio

```bash
uv tool install folio-docs
```

Dependency note: Folio uses Python 3.10+ for the CLI, and also depends on `Node.js 20.19+` and `pnpm 10` for `folio build` and `folio serve`. Use Corepack to activate pnpm 10:

```bash
corepack prepare pnpm@10 --activate
```

Then verify the CLI:

```bash
folio --version
```

### Standalone Installer

The standalone installer requires `uv`, installs the `folio-docs` distribution as
a `uv` tool, checks Node.js 20.19+, and tries to activate pnpm 10 through
Corepack when it can.

Inspect the script before running it:

```bash
curl -LsSf https://raw.githubusercontent.com/pguijas/folio/main/install.sh | less
curl -LsSf -o install-folio.sh https://raw.githubusercontent.com/pguijas/folio/main/install.sh
sh install-folio.sh
```

Install a specific Folio version:

```bash
FOLIO_VERSION=0.1.0 sh install-folio.sh
```

Skip automatic pnpm setup when you only want the Python CLI:

```bash
FOLIO_SKIP_PNPM_SETUP=1 sh install-folio.sh
```

## Other Install Methods

<CodeGroup labels={["uv project", "uv tool", "pip"]}>
```bash
uv add folio-docs
```

```bash
uv tool install folio-docs
```

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install folio-docs
```
</CodeGroup>

Use `uv add folio-docs` inside a Python project. Use `uv tool install folio-docs` when you want the `folio` command available outside a project.

## For Developers

Use the repository setup when you are working on Folio itself:

```bash
git clone https://github.com/pguijas/folio.git
cd folio
uv sync
cd template
pnpm install --frozen-lockfile
cd ..
uv run folio build
```

`uv sync` installs Folio and its Python development dependencies from `uv.lock`. The template has its own `pnpm-lock.yaml`, so install the frontend dependencies from `template/` before running template-specific commands.

Run the test suite from the repository root:

```bash
uv run pytest tests/ -q
```

For UI work, run Folio's dev server from the repository root:

```bash
uv run folio serve
```

## Next Steps

Once Folio is installed, head to the [Quick Start](./quickstart) guide to build your first documentation site.
