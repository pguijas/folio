---
title: GitHub Pages
description: Deploy Folioh docs to GitHub Pages, including base path inference, production deploys, and branch previews.
---

# GitHub Pages

GitHub Pages serves static files. Folioh's Pages integration publishes the same
`_site/` artifact used by other hosts, with extra handling for project-site base
paths and branch previews.

## Base Path Setup

Set `project.url` in `docs.yaml` to the final Pages URL before deploying so
sitemap and metadata use the public URL.

For GitHub Pages builds, set `FOLIOH_DEPLOY_PROVIDER=github-pages` in the build
step or add `deploy.provider: "github-pages"` to `docs.yaml`. Folioh then infers
`/repo-name` for project pages from `GITHUB_REPOSITORY`, while user and
organization pages such as `owner.github.io` stay at `/`.

Use `FOLIOH_BASE_PATH` or `deploy.base_path` only when you need an explicit
override.

For a custom domain, set it in the repository's Pages settings and configure
its DNS records with your domain provider. The workflows created by `folioh init`
read the configured Pages URL and base path for both production and previews.
An apex domain such as `https://example.com` uses `/`, so preview assets stay
under `/previews/pr-<number>-<branch>/`. Set `project.url` to the custom domain
as well so metadata and sitemap links use it.

```yaml
deploy:
  provider: "github-pages"
```

## Production Deploys

<Steps>
  <Step title="Build your docs">
    ```bash
    folioh build --clean
    ```
  </Step>
  <Step title="Publish the static site">
    Upload `_site/` as the GitHub Pages artifact.
  </Step>
  <Step title="Automate with GitHub Actions">
    Use the workflow in [CI/CD](./ci-cd) when Pages should deploy on push.
  </Step>
</Steps>

## Branch Previews

`folioh init` creates a second GitHub Actions workflow for branch previews on the
same GitHub Pages site. It runs from `pull_request_target`: PR branch code is
built in an unprivileged job, and the privileged deploy job only consumes the
static `_site/` artifact. The preview appears under
`/previews/pr-<number>-<branch>/`, for example
`https://owner.github.io/project/previews/pr-17-docs-redesign/`.

GitHub Pages publishes one artifact for the whole site. Folioh keeps production
and branch previews together in that single artifact:

- A `main` deploy builds production docs at the site root.
- It restores existing preview folders from the internal `folioh-pages-state`
  branch.
- A branch deploy starts from the saved `folioh-pages-state` root, downloads the
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
`folioh-pages-state` branch. This branch stores the last complete Pages artifact
so a preview deploy can replace one preview folder without dropping production
docs or other previews.

Do not edit the state branch manually unless you are intentionally repairing the
published Pages artifact.
