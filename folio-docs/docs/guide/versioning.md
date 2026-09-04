# Versioning (Alpha)

*Document multiple versions of your library side by side with an explicit workflow.*

<Callout type="warning" title="Alpha feature">
  Multi-version documentation is disabled in this release while the routing surface stabilizes. These notes are kept for future work and are not included in generated public docs.
</Callout>

Folio supports multi-version documentation using a multi-build approach. Each version is built into its own static subdirectory, and older versions should usually be built from immutable git tags. A version selector dropdown in the docs navbar lets users switch between versions.

## Quick Start

Add a `versions` section to your `docs.yaml`:

```yaml
versions:
  - label: "v2.0.0 (latest)"
    path: "latest"
  - label: "v1.0.0"
    path: "v1"
    ref: "v1.0.0"
```

The first entry is the default version. The `versions` section alone does not change plain builds; it is read only by the explicit versioning commands. When you run `folio build-versions`, Folio writes `_site/index.html` as a redirect to that version, so opening `/` goes to `/latest/` in this example.

Build all versions:

```bash
folio build-versions
```

Preview the configured versions locally:

```bash
folio serve --versions
```

This produces:

```
_site/
  index.html  # redirects to latest/
  latest/    # docs from the current working tree
  v1/        # docs from v1.0.0 tag
```

A version dropdown appears automatically in the versioned docs navbar. Users can switch between versions while staying on the same page. During local preview, `folio serve --versions` serves the generated `_site/` directory so paths like `/latest/` and `/v1/` work directly in the browser. The generated links are relative, so cross-version navigation also works when opening exported files from disk.

Plain `folio build` and `folio serve` remain optimized for the current docs. They build or serve the current working tree only, even when `versions` is configured.

## Recommended Release Flow

Use the current working tree for the first, default entry and use tags for frozen releases:

```yaml
project:
  version: "0.2.0"

versions:
  - label: "v0.2.0 (latest)"
    path: "latest"
  - label: "v0.1.0"
    path: "v0.1"
    ref: "v0.1.0"
```

Before building versioned docs, make sure every historical ref exists locally:

```bash
git tag v0.1.0 <release-commit>
git tag v0.2.0 HEAD
```

Then preview the exact release matrix:

```bash
folio serve --versions --clean
```

When the preview is correct, push the commit and tags:

```bash
git push origin main
git push origin v0.1.0 v0.2.0
```

This keeps `latest` easy to work on while making old versions reproducible. Rebuilding the docs later uses the tag for `v0.1.0`, not whatever the branch happens to contain at that time.

In CI, build and deploy from the branch that contains the current `versions`
matrix and fetch tags with full history. Restore `_site/` from the previous
deploy before running `folio build-versions`; Folio will rebuild the current
version and reuse historical `ref` versions whose cached manifests still match.
The final artifact should include all versions you want to keep online.

By default, `folio build-versions` preserves existing sibling folders in
`_site/` and skips unchanged historical versions. Use `--clean` when you want a
fresh full artifact, and make sure the `versions` matrix lists every version
that should remain online.

## How It Works

The `folio build-versions` command:

<Steps>
  <Step title="Reads the versions list">
    Parses the `versions` section from `docs.yaml` to get the list of versions to build.
  </Step>
  <Step title="Creates git worktrees">
    For each version with a `ref` that is not already cached, creates a temporary git worktree at that ref. This lets Folio build from any branch or tag without switching your working directory.
  </Step>
  <Step title="Syncs current version metadata">
    Injects the current `versions` list, plugin list, and plugin-owned configuration into each checked-out ref before building, so historical docs still show the latest version dropdown and current generated plugin components.
  </Step>
  <Step title="Builds each version">
    Runs `folio build` against each version's source tree, outputting to `_site/{path}/`. Historical versions with a matching `.folio-version.json` manifest are reused instead.
  </Step>
  <Step title="Writes version manifests">
    Stores cache metadata in each version folder so the next CI run can skip unchanged historical versions restored from `_site/`.
  </Step>
  <Step title="Cleans up">
    Removes temporary worktrees after building.
  </Step>
</Steps>

## Configuration

Each version entry has three fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | `string` | Yes | Display name shown in the version dropdown. |
| `path` | `string` | Yes | Output subdirectory and URL path prefix. |
| `ref` | `string` | No | Git branch or tag to build from. If omitted, builds from the current working tree. Source links for this version point at the same ref. |
| `default_path` | `string` | No | Path to open from the version dropdown instead of preserving the current page path. Use this when a historical version has a different docs structure. |

The first version in the list is the default. Put the current release first, normally with `path: "latest"` and no `ref`, then add older tagged releases below it.

### Using tags

You can reference specific release tags:

```yaml
versions:
  - label: "v3.0 (latest)"
    path: "latest"
  - label: "v2.4.1"
    path: "v2"
    ref: "v2.4.1"
  - label: "v1.9.0"
    path: "v1"
    ref: "v1.9.0"
```

For smoke testing, this repository also includes a mocked `v0.0.1` tag. It contains a minimal docs tree with a single `Hello world` page and is configured at `path: "v0.0"` with `default_path: "docs/"` so `folio serve --versions --clean` can verify that old tagged docs still receive the current version dropdown.

### Development version

Omit `ref` to build from the current working tree. This is useful for a "dev" or "latest" version:

```yaml
versions:
  - label: "dev (unreleased)"
    path: "dev"
  - label: "v2.0 (stable)"
    path: "stable"
    ref: "v2.0.0"
```

## Version Selector

When versions are configured and built with `folio build-versions` or `folio serve --versions`, a dropdown appears in the docs navbar next to the theme configurator. By default, selecting a version navigates to the same page path under the new version prefix. If a version entry defines `default_path`, the dropdown links to that path instead.

The hot-reloading `folio serve` dev server hides the dropdown and serves the current working tree only. Use `folio serve --versions` to preview the generated dropdown and cross-version links locally.

When no `versions` section is present in `docs.yaml`, the versioning commands exit with guidance and Folio behaves as a single-version site.

## Deployment

Each version is a complete, self-contained Next.js build. Deploy the entire `_site/` directory to your hosting provider:

```
_site/
  index.html   # redirects to latest/
  latest/
    index.html
    docs/
      ...
  v1/
    index.html
    docs/
      ...
```

### With Vercel

Set the output directory to `_site` and Vercel will serve all versions under their respective paths.

### With GitHub Pages

Use the workflow from [Deployment: CI/CD](./deployment/ci-cd). The important pieces are restoring `_site/` before `folio build-versions`, running without `--clean` for normal deploys, and uploading the complete `_site/` artifact.

## Requirements

- Your project must be a **git repository** (worktrees require git).
- Each `ref` must exist as a valid branch or tag before running `folio build-versions` or `folio serve --versions`.
- Each referenced ref must contain a valid `docs.yaml` at the project root.
- Prefer tags for released versions so older docs remain stable and reproducible.

## CLI Reference

```bash
# Build all configured versions
folio build-versions

# Preview all configured versions locally
folio serve --versions

# With verbose output
folio build-versions -v

# Force clean rebuild of all versions
folio build-versions --clean
```

Run `folio build-versions --help` for all options.
