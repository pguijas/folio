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
curl -LsSf https://pguijas.github.io/folio/install.sh | less
curl -LsSf -o install-folio-docs.sh https://pguijas.github.io/folio/install.sh
sh install-folio-docs.sh
```

Install a specific Folio version:

```bash
FOLIO_VERSION=0.3.0 sh install-folio-docs.sh
```

Skip automatic pnpm setup when you only want the Python CLI:

```bash
FOLIO_SKIP_PNPM_SETUP=1 sh install-folio-docs.sh
```

## Other Install Methods

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

Use `uv add folio-docs` inside a Python project. Use `uv tool install folio-docs`
when you want the `folio` command available outside a project. Add Folio for
Agents to the same tool environment when you also want `folio board`:

```bash
uv tool install folio-docs --with folio-agents
```

## Contributing to Folio

Repository setup, tests, and frontend development belong to the contributor
workflow rather than installation. See the
[contributing guide](https://github.com/pguijas/folio/blob/main/CONTRIBUTING).

## Next Steps

Once Folio is installed, head to the [Quick Start](./quickstart) guide to build your first documentation site.
