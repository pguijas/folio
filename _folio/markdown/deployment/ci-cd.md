# CI/CD

CI/CD is a deployment strategy: the pipeline builds `_site/`, checks it, and
publishes the same static artifact that local builds produce.

This page focuses on GitHub Actions because `folio init` can generate ready-to-use
Pages workflows.

## GitHub Actions Deployment

`folio init` creates a GitHub Pages workflow at `.github/workflows/pages.yml`.
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
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      pull-requests: read
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Configure GitHub Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install Folio
        run: |
          curl -LsSf https://pguijas.github.io/folio/install.sh | sh
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"

      - name: Build docs
        env:
          FOLIO_BASE_PATH: "${{ steps.pages.outputs.base_path || '/' }}"
        run: folio build --clean

      - name: Preserve branch previews
        shell: bash
        run: folio github-pages preserve-previews --site-dir _site --git-repo . --state-dir _pages-state --state-branch folio-pages-state

      - name: Prune stale previews
        shell: bash
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          open_prs="$(gh pr list --state open --json number,headRefName)"
          folio github-pages prune-previews \
            --previews-dir _site/previews \
            --open-prs-json "$open_prs"

      - name: Write previews data
        shell: bash
        run: folio github-pages write-previews-data --previews-dir _site/previews

      - name: Save Pages state
        shell: bash
        run: folio github-pages save-state --artifact-dir _site --git-repo . --state-dir _pages-state --state-branch folio-pages-state --commit-message "Update Pages state"

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
      - name: Install Folio
        run: |
          curl -LsSf https://pguijas.github.io/folio/install.sh | sh
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4

      - name: Verify and print deployment URL
        shell: bash
        run: |
          url="${{ steps.deployment.outputs.page_url }}"
          index_url="${url%/}/previews/"
          folio github-pages verify-url \
            --url "$url" \
            --index-url "$index_url" \
            --summary-heading "Production docs" \
            --primary-label "Production URL" \
            --index-label "Previews index" \
            --success-message "Verified deployment and previews index with HTTP 200." \
            --error-message "Deployment URL or previews index did not return HTTP 200"
```

If your docs build needs local project dependencies, edit the build steps in this
same file.

The `folio github-pages` commands are internal deployment helpers shipped in
the `folio` binary. They keep the generated workflow readable while still
preserving branch previews, pruning the previews whose pull request has closed,
updating the preview index, saving Pages state, and verifying the deployed
URLs. Pruning is why the build job asks for `pull-requests: read`: without it
the previews of closed pull requests are published forever.

## Branch Preview Deploys

`folio init` also creates `.github/workflows/branch-previews.yml` for GitHub
Pages branch previews. It runs from `pull_request_target` so the workflow
definition and deploy steps come from the trusted base branch, while PR branch
code is built in a separate unprivileged job.

GitHub Pages serves one artifact per site, so Folio does not deploy each branch
as an independent Pages site. Instead, every deploy publishes a complete static
artifact with this layout:

```text
/
  index.html                 # production docs built from main
  docs/...
  previews/
    index.html               # preview index
    pr-17-docs-redesign/     # preview built from PR 17, branch docs-redesign
    pr-24-api-polish/        # preview built from PR 24, branch api-polish
```

The production workflow and preview workflow cooperate through an internal
`folio-pages-state` branch:

1. A `main` deploy builds production docs into `_site/`.
2. It copies any existing `_site/previews/` folders from `folio-pages-state`.
3. It regenerates `/previews/index.html`.
4. It saves the complete artifact back to `folio-pages-state`.
5. It deploys the combined artifact to GitHub Pages.

A branch preview deploy follows the same rule: publish the complete site, not
just the branch folder.

1. The preview workflow resolves the open same-repository PR for the branch.
2. An unprivileged build job checks out the PR head with persisted credentials
   disabled and builds docs with
   `FOLIO_BASE_PATH=/repo/previews/pr-<number>-<branch>/`.
3. That build job uploads only the static `_site/` preview artifact.
4. A privileged deploy job revalidates that the PR head is still current before
   doing any write-capable work.
5. The deploy job checks out the trusted base branch, starts the Pages artifact
   from the saved `folio-pages-state` root, and uses a trusted production build
   only as the first-deploy fallback.
6. It downloads the static preview artifact and replaces only
   `/previews/pr-<number>-<branch>/`.
7. It regenerates `/previews/index.html`, saves state, deploys, and verifies the
   preview URL.
8. It creates or updates a sticky PR comment with the preview URL, preview
   index, branch, and commit.

Production therefore remains at the normal Pages URL, while each open PR gets a
stable preview URL such as:

```text
https://owner.github.io/project/
https://owner.github.io/project/previews/pr-17-docs-redesign/
https://owner.github.io/project/previews/
```

The preview folder name includes the PR number plus a URL-safe version of the
branch name, which keeps similarly named branches from overwriting each other.
If a PR is stale, closed, still a draft, or comes from a fork, the preview deploy
exits early and leaves the current Pages site unchanged.

The PR comment uses a hidden marker so the workflow updates the same comment on
each deploy. Reviewers get the latest preview link directly in the conversation
without a new comment on every push. The workflow still writes the same links to
the Actions summary for debugging failed runs.

## Pull Request Checks

Run the docs build and, for a Python project, the coverage gate on every PR. Drop
the coverage step for a JavaScript or Rust project: `folio coverage` reads Python
only in this release.

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

      - name: Install Folio
        run: |
          curl -LsSf https://pguijas.github.io/folio/install.sh | sh
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"

      - name: Install pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Check docstring coverage
        run: folio coverage --min 80

      - name: Build docs
        run: folio build --clean
```

## Coverage Gates

Use `folio coverage` to enforce minimum docstring coverage in CI. It reads Python
only in this release.

```bash
folio coverage --min 80
```

The gate applies to the total, not to each module: when the total falls below the
threshold, the command prints `Coverage 60.0% is below minimum 80.0%` (with your
numbers) and exits with code 1, failing the pipeline. Adjust the threshold to match
your project's standards.

The report counts each module, its public classes, functions and methods, and
shows per-module statistics. This run passes `--min 80` even though one module
sits at 50%:

```text
              Documentation Coverage
┏━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Module          ┃ Total ┃ Documented ┃ Coverage ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ my_lib.api      │    10 │         10 │   100.0% │
│ my_lib.core     │    13 │         12 │    92.3% │
│ my_lib.internal │     4 │          2 │    50.0% │
│ my_lib.utils    │     7 │          6 │    85.7% │
├─────────────────┼───────┼────────────┼──────────┤
│ Total           │    34 │         30 │    88.2% │
└─────────────────┴───────┴────────────┴──────────┘
```

## Pre-commit Hook

In a Python project, run a quick coverage check before every commit:

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
