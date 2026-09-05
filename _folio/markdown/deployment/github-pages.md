# GitHub Pages

GitHub Pages serves static files. Folio's Pages integration publishes the same
`_site/` artifact used by other hosts, with extra handling for project-site base
paths and branch previews.

## Base Path Setup

Set `project.url` in `docs.yaml` to the final Pages URL before deploying so
sitemap and metadata use the public URL.

For GitHub Pages builds, set `FOLIO_DEPLOY_PROVIDER=github-pages` in the build
step or add `deploy.provider: "github-pages"` to `docs.yaml`. Folio then infers
`/repo-name` for project pages from `GITHUB_REPOSITORY`, while user and
organization pages such as `owner.github.io` stay at `/`.

Use `FOLIO_BASE_PATH` or `deploy.base_path` only when you need an explicit
override.

```yaml
deploy:
  provider: "github-pages"
```

## Production Deploys

### Build your docs

    ```bash
    uv run folio build --clean
    ```

### Publish the static site

    Upload `_site/` as the GitHub Pages artifact.

### Automate with GitHub Actions

    Use the workflow in [CI/CD](./ci-cd) when Pages should deploy on push.

## Branch Previews

`folio init` creates a second GitHub Actions workflow for branch previews on the
same GitHub Pages site. It runs from `pull_request_target`: PR branch code is
built in an unprivileged job, and the privileged deploy job only consumes the
static `_site/` artifact. The preview appears under
`/previews/pr-<number>-<branch>/`, for example
`https://owner.github.io/project/previews/pr-17-docs-redesign/`.

GitHub Pages publishes one artifact for the whole site. Folio keeps production
and branch previews together in that single artifact:

- A `main` deploy builds production docs at the site root.
- It restores existing preview folders from the internal `folio-pages-state`
  branch.
- A branch deploy starts from the saved `folio-pages-state` root, downloads the
  static preview artifact, replaces only `/previews/pr-<number>-<branch>/`, and
  deploys the complete artifact again.

That means the production URL stays stable while PR previews are updated
independently. The preview index is available at `/previews/`, and each deploy
prints the preview URL and index URL in the Actions summary before verifying
both return HTTP 200. Successful preview deploys also create or update one
sticky PR comment with the latest preview link, so reviewers do not need to open
the Actions run to find it.

## State Branch

The production workflow and preview workflow cooperate through an internal
`folio-pages-state` branch. This branch stores the last complete Pages artifact
so a preview deploy can replace one preview folder without dropping production
docs or other previews.

Do not edit the state branch manually unless you are intentionally repairing the
published Pages artifact.
