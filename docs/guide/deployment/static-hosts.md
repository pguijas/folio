---
title: Static Hosts
description: Deploy Folio's _site artifact to Vercel, Netlify, or self-hosted static infrastructure.
---

# Static Hosts

Static hosts only need the generated `_site/` directory. The host can either run
`folio build --clean` itself or serve a prebuilt artifact uploaded by your CI
pipeline.

## Vercel

Use Vercel as a static-site host:

<Steps>
  <Step title="Configure the project">
    In Vercel project settings, use:

    - **Framework Preset**: Other
    - **Install Command**: `npm install -g pnpm@10 && curl -LsSf https://pguijas.github.io/folio/install.sh | sh`
    - **Build Command**: `~/.local/bin/folio build --clean`
    - **Output Directory**: `_site`

    The install command runs the standalone installer from
    [Installation](../installation) during each build, so there is nothing to
    add to your repository. The binary lands in `~/.local/bin`, which is why the
    build command calls it by path.
  </Step>
  <Step title="Deploy">
    Push to your production branch. Vercel runs the build command and publishes
    `_site/`.
  </Step>
</Steps>

Vercel already builds automatically on push. If you need required documentation
checks before deploy, add a CI workflow that runs `folio build --clean` as a pull
request check, plus `folio coverage --min 80` for Python projects (coverage reads
Python only in this release; see [CI/CD](./ci-cd#coverage-gates)).

## Netlify

Create a `netlify.toml` that publishes the static artifact:

```toml filename="netlify.toml"
[build]
  command = "npm install -g pnpm@10 && curl -LsSf https://pguijas.github.io/folio/install.sh | sh && ~/.local/bin/folio build --clean"
  publish = "_site"

[build.environment]
  NODE_VERSION = "20"
```

Netlify will rebuild the docs on each deploy and serve `_site/` directly.

## Self-hosted

Any static file server can host the generated site:

```bash
folio build --clean
python3 -m http.server 8080 --directory _site
```

For containerized deployments, copy `_site/` into a small static web server
image such as Nginx, Caddy, or any equivalent platform image. Do not copy
`.build/`; it is a generated workspace cache, not the deployable artifact.

```dockerfile filename="Dockerfile"
FROM nginx:alpine
COPY _site/ /usr/share/nginx/html/
```
