# CI/CD Integration

Automate your documentation builds with continuous integration. This guide provides ready-to-use workflows for GitHub Actions.

## GitHub Actions

### Build and deploy

`folio init` creates a single GitHub Pages workflow at `.github/workflows/pages.yml`.
It builds docs on every push to `main`, uploads `_site/`, and deploys with
GitHub Pages:

```yaml filename=".github/workflows/pages.yml"
name: Deploy Docs

"on":
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Build docs
        env:
          FOLIO_DEPLOY_PROVIDER: github-pages
        run: uv tool run --from folio-docs folio build --clean

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: _site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    permissions:
      pages: write
      id-token: write
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

If your docs build needs local project dependencies or versioned documentation,
edit the build steps in this same file. Folio's own repository currently uses
`uv sync --all-groups --locked` before `uv run --locked folio build --clean` to
deploy only the current version.

### Pull request checks

Run docs build and coverage checks on every PR:

```yaml filename=".github/workflows/docs-check.yml"
name: Docs Check

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: uv pip install --system folio-docs

      - name: Check docstring coverage
        run: folio coverage --min 80

      - name: Build docs (verify no errors)
        run: folio build --clean
```

## Coverage gates

Use `folio coverage` to enforce minimum docstring coverage in CI:

```bash
folio coverage --min 80
```

This exits with code 1 if any module falls below 80% coverage, failing the CI pipeline. Adjust the threshold to match your project's standards.

The coverage report shows per-module statistics:

```
Module                    Coverage
─────────────────────────────────
my_lib.core               92.3%
my_lib.utils              85.7%
my_lib.api                100.0%
my_lib.internal           45.2%  ← BELOW THRESHOLD
─────────────────────────────────
Overall                   80.8%
```

## Pre-commit hook

Run a quick coverage check before every commit:

```yaml filename=".pre-commit-config.yaml"
repos:
  - repo: local
    hooks:
      - id: folio-coverage
        name: Docstring coverage
        entry: folio coverage --min 80
        language: system
        pass_filenames: false
        always_run: true
```

## Vercel integration

If deploying to Vercel, no CI workflow is needed — Vercel builds automatically on push. To add coverage checks, use a GitHub Actions workflow that runs `folio coverage --min 80` as a required status check without the deploy step.
