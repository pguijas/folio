# Theme Packages

> [!WARNING] Security
> A theme package is **executed as trusted code** during every build. The
> package files are overlaid onto the template that Folio then builds with
> `pnpm install --frozen-lockfile` (which executes dependency lifecycle scripts)
> and `next build` (which runs `next.config.mjs` in Node), so pointing
> `theme.package` at a directory is equivalent to running that code on your
> machine. Only point `theme.package` at frontend code you have reviewed and
> trust. Building an untrusted repository or branch in CI inherits the same
> remote-code-execution surface — treat a docs build like any other
> untrusted-code execution. Never put secrets, API tokens, or credentials in
> theme code or `docs.yaml`: static docs are published.

Theme packages are the middle ownership level. They let a project ship a local
theme overlay that is copied over the bundled Folio template before generated
content and metadata are injected.

Use a theme package when YAML personalization is too limited, but a full custom
template would duplicate too much of Folio's default docs runtime.

## Configure a Package

```yaml
theme:
  package: "docs/theme/acme"
  preset: "acme"
```

`theme.package` is resolved relative to the project directory. The directory is
trusted frontend code: it can override template files, import dependencies
already available to the template, and replace Folio's default theme modules.

## Ownership Model

| Owner | Responsibilities |
|-------|------------------|
| Folio | Copy the bundled template, apply the theme package overlay, generate content, write metadata, inject fallback theme config, run the frontend build, and export static files. |
| Theme package | Own selected frontend files such as layouts, global CSS, the configurator UI, project header actions, or `theme/project-theme.ts`. |

Folio still writes generated docs content and reserved build files into `.build/`.
Do not edit `.build/` directly; change the package source instead.

## Package Anatomy

A package can be small and only override the files it owns:

```text
docs/theme/acme/
  app/
    globals.css
    docs/
      layout.tsx
  components/
    theme-configurator.tsx
    project-header-actions.tsx
  theme/
    project-theme.ts
```

Common override points:

| File | Purpose |
|------|---------|
| `app/layout.tsx` | Own font loading, metadata shell, providers, and global layout behavior. |
| `app/docs/layout.tsx` | Own the docs navbar, sidebar placement, search slot, and ThemeConfigurator mount. |
| `components/theme-configurator.tsx` | Replace the bundled configurator UI with a project-specific implementation. |
| `components/project-header-actions.tsx` | Replace the default generated header action component. |
| `theme/project-theme.ts` | Own all presets, controls, variants, defaults, and resolved tokens in TypeScript. |
| `app/globals.css` | Override or replace template-level CSS when a project needs exact visual parity. |

## YAML and TypeScript Together

If the package supplies `theme/project-theme.ts`, Folio does not overwrite it
with a YAML-generated module. The package owns the preset implementation.

If the package omits `theme/project-theme.ts`, Folio still emits the safe
`docs.yaml`-driven project preset described in
[Personalization](./personalization). This lets a project start with YAML and
graduate individual surfaces to TypeScript only when needed.

## Register a Custom Preset

A theme package can register a custom preset without forking `presets.ts`. From
`theme/project-theme.ts`, import `registerPreset` and call it before exporting
the `projectThemePreset`.

```typescript
import type { ThemePreset } from "./preset-types"
import { registerPreset } from "./preset-registry"

const acmePreset: ThemePreset = {
  id: "acme",
  name: "Acme",
  description: "Custom preset for Acme's design system",
  scene: "A developer browses API documentation with Acme brand colors.",
  preview: { light: "oklch(0.50 0.10 210)", dark: "oklch(0.70 0.08 210)" },
  defaultOptions: {},
  controls: [],
  resolve: (options) => ({
    preview: { light: "oklch(0.50 0.10 210)", dark: "oklch(0.70 0.08 210)" },
    radius: "0.5rem",
    style: {
      /* ThemeStyle fields */
    },
    light: {
      /* ThemeVars for light mode */
    },
    dark: {
      /* ThemeVars for dark mode */
    },
  }),
}

registerPreset(acmePreset, "project")

export const projectThemePreset = acmePreset
export const projectThemeDefaultConfig = {
  /* Default config object */
}
```

The `registerPreset` function is the supported extension point. The optional
second argument (`"project"`) adds the preset to that display group in the
configurator UI. If a preset with the same `id` already exists, it will be
replaced with a console warning.

See [ThemeConfigurator](../components/theme-configurator) for the full
`ThemePreset` contract, including `controls`, `resolve`, and all theme fields.

## What Packages Should Not Do

- Do not assume files written under `.build/` are stable source files.
- Do not put secrets in theme code or `docs.yaml`; static docs are public.
- Do not use a package when the project needs a different app structure,
  dependency graph, route model, or product shell. Use
  [custom templates](./custom-templates) for that level.

## Validation Checklist

Folio validates theme packages at build time before any overlay. If validation
fails, the build halts with a clear `ValueError` listing all violations.

### Reserved Paths

A theme package must NOT contain any of these paths. Folio generates them at
build time, and including them will cause a validation error:

- `content/` — Generated docs pages and metadata live here
- `lib/folio-template.ts` — Folio internal contract file
- `lib/folio-mdx-contract.ts` — Folio internal contract file
- `.next/` — Next.js build cache
- `node_modules/` — Dependency install directory

### Required Exports

If a theme package includes `theme/project-theme.ts`, that file MUST export both:

- `projectThemePreset` — The preset definition (colors, spacing, variants)
- `projectThemeDefaultConfig` — The default configuration object

Folio checks for `export const <name>` or `export { <name> }` forms. Missing
exports fail validation.

### Example Validation Error

```
Theme package validation failed:
  - Theme package must not contain reserved path 'content/'. Folio generates this at build time.
  - theme/project-theme.ts must export 'projectThemePreset'. Expected: export const projectThemePreset = ...
```

### Why This Fails Early

Validation runs before any file overlay. You get a clear Python error with
actionable messages instead of a cryptic Next.js build failure or runtime
