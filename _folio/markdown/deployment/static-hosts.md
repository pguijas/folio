# Static Hosts

Static hosts only need the generated `_site/` directory. The host can either run
`uv run folio build --clean` itself or serve a prebuilt artifact uploaded by your
CI pipeline.

## Vercel

Use Vercel as a static-site host:

### Install Folio

    Add Folio to your project so Vercel can run the same build command as your
    local machine:

    ```bash
    uv add folio-docs
    ```

### Configure the project

    In Vercel project settings, use:

    - **Framework Preset**: Other
    - **Install Command**: `corepack prepare pnpm@10 --activate && uv sync --locked`
    - **Build Command**: `uv run folio build --clean`
    - **Output Directory**: `_site`

### Deploy

    Push to your production branch. Vercel runs the build command and publishes
    `_site/`.

Vercel already builds automatically on push. If you need required documentation
checks before deploy, add a CI workflow that runs `folio coverage --min 80` and
`folio build --clean` as pull request checks.

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

## Self-hosted

Any static file server can host the generated site:

```bash
uv run folio build --clean
python3 -m http.server 8080 --directory _site
```

For containerized deployments, copy `_site/` into a small static web server
image such as Nginx, Caddy, or any equivalent platform image. Do not copy
`.build/`; it is a generated workspace cache, not the deployable artifact.

```dockerfile filename="Dockerfile"
FROM nginx:alpine
COPY _site/ /usr/share/nginx/html/
```
