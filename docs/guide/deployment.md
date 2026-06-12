# Deployment

Folio builds a static site into `_site/`. Deploy that folder to any static host.
The internal build workspace is only a cache and should not be committed or used
as the public artifact.

## Build Once

Run the build from your project root:

```bash
uv add folio-docs
uv run folio build --clean
```

The `_site/` directory contains HTML, assets, Pagefind search data, `llms.txt`,
and `llms-full.txt`.

## Vercel

Use Vercel as a static-site host:

<Steps>
  <Step title="Install Folio">
    Add Folio to your project so Vercel can run the same build command as your
    local machine:

    ```bash
    uv add folio-docs
    ```
  </Step>
  <Step title="Configure the project">
    In Vercel project settings, use:

    - **Framework Preset**: Other
    - **Install Command**: `corepack prepare pnpm@10 --activate && uv sync --locked`
    - **Build Command**: `uv run folio build --clean`
    - **Output Directory**: `_site`
  </Step>
  <Step title="Deploy">
    Push to your production branch. Vercel runs the build command and publishes
    `_site/`.
  </Step>
</Steps>

## Netlify

Create a `netlify.toml` that publishes the static artifact:

```toml filename="netlify.toml"
[build]
  command = "corepack prepare pnpm@10 --activate && uv sync --locked && uv run folio build --clean"
  publish = "_site"

[build.environment]
  NODE_VERSION = "20"
```

Netlify will rebuild the docs on each deploy and serve `_site/` directly.

## GitHub Pages

GitHub Pages serves static files. Set `project.url` in `docs.yaml` to the final
Pages URL before deploying so sitemap and metadata use the public URL.

For GitHub Pages builds, set `FOLIO_DEPLOY_PROVIDER=github-pages` in the build
step or add `deploy.provider: "github-pages"` to `docs.yaml`. Folio then infers
`/repo-name` for project pages from `GITHUB_REPOSITORY`, while user and
organization pages such as `owner.github.io` stay at `/`. Use `FOLIO_BASE_PATH`
or `deploy.base_path` only when you need an explicit override.

<Steps>
  <Step title="Build your docs">
    ```bash
    uv run folio build --clean
    ```
  </Step>
  <Step title="Publish the static site">
    Upload `_site/` as the GitHub Pages artifact.
  </Step>
  <Step title="Configure GitHub Actions">
    See the [CI/CD guide](./ci-cd) for a complete GitHub Actions workflow.
  </Step>
</Steps>

## Self-hosted

Any static file server can host the generated site:

```bash
uv run folio build --clean
python3 -m http.server 8080 --directory _site
```

For containerized deployments, copy `_site/` into a small static web server
image such as Nginx, Caddy, or any equivalent platform image.
