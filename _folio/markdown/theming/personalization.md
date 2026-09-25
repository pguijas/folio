# Personalization

Personalization keeps the bundled Folio template and changes the theme data it
receives. This is the right level when the docs should still feel like Folio,
but with your project's brand, typography, accent, spacing, and header defaults.

## Basic Theme Options

```yaml
theme:
  preset: "organic-editorial"
  dark_mode: true
  logo: "docs/assets/logo.svg"
  favicon: "docs/assets/favicon.ico"
```

| Field | Purpose |
|-------|---------|
| `preset` | Default visual preset for the generated site. |
| `dark_mode` | `true` (the default) offers light, dark, and system modes through `next-themes`; `false` keeps the site light. |
| `logo` | Copies a project logo into the generated site and shows it in the docs navbar beside the project name. |
| `favicon` | Copies a project favicon into the generated site. |

`preset` must be a preset the configurator shows: a
[built-in id](/docs/components/theme-configurator#preset-library), one a
[theme package](/docs/theming/theme-packages#register-a-custom-preset) declares, or a new id
that `theme.name`, `theme.tokens` or `theme.style` defines (see
[Project Presets](#project-presets)). Any other value stops the build with the
list of valid ids and the nearest one, so `preset: "beakon"` asks whether you
meant `beacon`.

Dark mode is enabled by default. When enabled, readers can use the theme control
or press `d` outside form fields to switch between light and dark modes. With
`dark_mode: false` the site stays light whatever the reader's system or saved
preference: the mode controls leave the configurator, the header and landing
theme toggles are not rendered, and `d` does nothing. `theme.header.theme_toggle:
true` is then ignored with a warning.

The logo path is resolved from the project directory and must exist; a missing
file stops the build. The image takes the monogram's place in the docs navbar
and is served under `deploy.base_path` when one is set. The landing navbar and
the previews page keep the monogram.

## Theme Configurator

Every generated site includes the Folio `ThemeConfigurator` drawer when theme
presets are available. The drawer exposes the configured default preset, the
built-in preset library, and tuning controls for typography, accent, surfaces,
content width, reading rhythm, borders, code blocks, shell spacing, and radius.
It also offers light, dark and system mode unless `theme.dark_mode` is `false`.

Reader preferences are persisted in a project-scoped `localStorage` key derived
from the configured default preset. Folio also renders the default theme CSS into
the page before hydration so the site does not flash through unconfigured
typography or colors.

See [ThemeConfigurator](/docs/components/theme-configurator) for the built-in
preset catalog and the TypeScript preset contract.

## Tune Defaults

Use `theme.tune` to set the default configurator choices without creating a new
preset:

```yaml
theme:
  preset: "beacon"
  tune:
    font: "geist"
    accent: "laurel"
    surface: "paper"
    width: "wide"
    rhythm: "compact"
    borders: "fine"
    code: "terminal"
    radius: "0.3rem"
```

Common aliases map to the internal configurator ids:

| YAML key | Internal control |
|----------|------------------|
| `font` | `fontId` |
| `accent` or `color` | `colorId` |
| `surface` | `surfaceColorId` |
| `shell` | `shellPaddingId` |
| `width` or `content_width` | `contentWidthId` |
| `rhythm` or `reading` | `rhythmId` |
| `borders` or `border` | `borderId` |
| `code` or `code_blocks` | `codeTreatmentId` |

Each value must be one the configurator offers for that control:

| Control | Values |
|---------|--------|
| `fontId` | `folio`, `sans`, `geist`, `serif`, `mono` |
| `colorId` | `ink`, `laurel`, `indigo`, `copper` |
| `surfaceColorId` | `preset`, `paper`, `moss`, `mist` |
| `shellPaddingId` | `preset`, `flush`, `frame`, `gallery` |
| `contentWidthId` | `preset`, `focus`, `docs`, `wide` |
| `rhythmId` | `preset`, `compact`, `balanced`, `roomy` |
| `borderId` | `preset`, `fine`, `structured`, `ruled` |
| `codeTreatmentId` | `preset`, `soft`, `framed`, `plate`, `terminal` |

Any other value stops the build with the list and the nearest value, for example
`theme.tune.rhythm must be one of 'preset', 'compact', 'balanced', 'roomy'; got
'dense'`. A key that is none of the above warns, names the key it most likely
meant, and is ignored.

`font: "geist"` selects the bundled Geist and Geist Mono font pair and maps the
public `--font-sans` and `--font-mono` tokens used by Tailwind utilities.

`theme.radius` (and its `theme.tune.radius` alias) is validated against the
fixed radius scale: `"0"`, `"0.3rem"`, `"0.5rem"`, `"0.75rem"`, or `"1rem"`.
The named aliases `"none"`, `"sm"`, `"md"`, `"lg"`, and `"full"` map onto the
same scale (matching the configurator's radius labels). Any other value fails
config validation, because the configurator maps the configured radius onto
this fixed scale.

## Project Presets

When a project supplies `name`, `description`, `scene`, `preview`, `style`,
`tokens`, or `variants`, Folio emits `theme/project-theme.ts` during template preparation and
adds the project preset before the built-in preset library.

```yaml
theme:
  preset: "acme"
  name: "Acme"
  description: "Operational docs theme"
  preview:
    light: "oklch(0.64 0.12 155)"
    dark: "oklch(0.78 0.14 155)"
  tune:
    font: "geist"
    width: "wide"
    rhythm: "compact"
    radius: "0.3rem"
  header:
    brand: "Acme"
    badge: "Docs"
    repo: "https://github.com/acme/sdk"
    search: true
    theme_toggle: true
    action_label: "Dashboard"
    action_href: "https://app.acme.dev"
  tokens:
    light:
      --background: "oklch(0.985 0.01 150)"
      --foreground: "oklch(0.13 0.02 150)"
      --primary: "oklch(0.47 0.14 155)"
      --ring: "oklch(0.47 0.14 155)"
    dark:
      --background: "oklch(0.10 0.01 150)"
      --foreground: "oklch(0.94 0.01 150)"
      --primary: "oklch(0.73 0.15 155)"
      --ring: "oklch(0.73 0.15 155)"
  style:
    --folio-content-max-width: "82rem"
    --folio-section-gap: "2.75rem"
    --folio-card-padding: "1.1rem"
    --folio-code-bg: "oklch(0.14 0.01 150)"
```

`tokens.light` and `tokens.dark` accept CSS custom properties such as shadcn
tokens (`--background`, `--card`, `--border`, `--chart-1`) and project tokens
(`--brand-accent`). `style` accepts layout variables such as
`--folio-content-max-width`, `--folio-section-gap`, `--folio-card-padding`,
`--folio-code-bg`, `--folio-workspace-shell-topbar`,
`--folio-workspace-shell-topbar-blur`, and
`--folio-workspace-shell-topbar-border`. The un-prefixed legacy spellings
(for example `--content-max-width`) are still accepted for compatibility but
are deprecated; new configs should use the canonical `--folio-*` names.

### Header URL Validation

The header can carry links: `theme.header.repo` and `theme.header.action_href`.
Folio validates these URLs at config-load time against an allowlist of safe
schemes. Permitted values are:

- `http` and `https` URLs (for example `https://github.com/acme/sdk`);
- `mailto:` links; and
- relative URLs (for example `/dashboard` or `docs/index`).

Unsafe schemes — notably `javascript:` and `data:` — are rejected. A header
link using a rejected scheme raises a config error and fails the build, naming
the offending field, rather than being emitted into the generated site. This
keeps script-injection payloads out of the docs header even when the
`docs.yaml` comes from an untrusted source. Use an `http(s)`, `mailto:`, or
relative URL for any header link.

The top-level `project.repo` is validated less strictly because repository
URLs legitimately use non-web schemes: `ssh://`, `git://`, `git+https://`, and
scp-style `git@host:path` forms are accepted, and only schemes that could
execute script or read local files (`javascript:`, `data:`, `vbscript:`,
`file:`) are rejected.

## Variants

Variants let a project expose its own configurator controls. Each option can set
a swatch, preview colors, style overrides, and light/dark token overrides while
inheriting the base project preset.

```yaml
theme:
  preset: "acme"
  name: "Acme"
  variants:
    color:
      label: "Color"
      default: "default"
      options:
        default:
          label: "Default"
          swatch: "oklch(0.47 0.14 155)"
        ocean:
          label: "Ocean"
          swatch: "oklch(0.56 0.16 230)"
          tokens:
            light:
              --primary: "oklch(0.50 0.16 230)"
              --ring: "oklch(0.50 0.16 230)"
            dark:
              --primary: "oklch(0.74 0.15 230)"
              --ring: "oklch(0.74 0.15 230)"
```

If an option has `swatch` but no full light/dark `preview`, Folio uses the
swatch for both preview modes.

Every option combination across all variant controls is resolved and embedded
into each generated page, so `theme.variants` is capped at 256 combinations
(the product of each control's option count). Exceeding the cap fails config
validation; reduce the number of controls or options.

## CSS Variables

Folio themes use `oklch` colors through CSS custom properties:

```css
:root {
  --background: oklch(0.995 0 0);
  --foreground: oklch(0.145 0.005 285);
  --primary: oklch(0.51 0.14 170);
  --primary-foreground: oklch(0.99 0 0);
  --muted: oklch(0.96 0.003 264);
  --muted-foreground: oklch(0.50 0.015 264);
  --card: oklch(0.995 0 0);
  --card-foreground: oklch(0.145 0.005 285);
  --border: oklch(0.91 0.004 264);
  --input: oklch(0.91 0.004 264);
  --ring: oklch(0.51 0.14 170);
  --radius: 0.5rem;
}

.dark {
  --background: oklch(0.14 0.004 285);
  --foreground: oklch(0.92 0.004 264);
  --primary: oklch(0.72 0.17 170);
  --border: oklch(1 0 0 / 8%);
}
```

Sidebar-specific variables control the left navigation independently from the
main content area:

| Variable | Purpose |
|----------|---------|
| `--sidebar` | Sidebar background. |
| `--sidebar-foreground` | Sidebar text color. |
| `--sidebar-primary` | Sidebar active item color. |
| `--sidebar-accent` | Sidebar hover/focus background. |
| `--sidebar-border` | Sidebar border color. |

### What Plugin Surfaces Rely On

The landing and the roadmap are drawn from the tokens on this page and nothing
else: no colour of their own, no per-page override. That is the contract a
plugin surface keeps, and it is what makes a preset switch or a theme package
restyle every page at once.

| Family | Tokens | Set by |
|--------|--------|--------|
| Surfaces and ink | `--background`, `--foreground`, `--card`, `--card-foreground`, `--popover`, `--popover-foreground`, `--muted`, `--muted-foreground`, `--accent`, `--accent-foreground`, `--secondary`, `--secondary-foreground`, `--border`, `--input`, `--ring`, `--radius` | the preset; `theme.tokens` overrides |
| Emphasis | `--primary`, `--primary-foreground`, `--destructive`, `--warning` | the preset |
| Data | `--chart-1` to `--chart-5`; the index pages, the preview cards and Mermaid draw from these | the preset |
| Type | `--font-sans`, `--font-mono`, `--folio-heading-font-family`, `--folio-body-font-family` | the preset; `theme.tune` |
| Layout | the `--folio-*` variables listed under Project Presets | the preset; `theme.style` |

Mermaid diagrams read the computed values of these tokens when they render and
fall back to a neutral palette only when none resolve.

A plugin surface that needs a colour these families do not carry adds a named
token in the same shape rather than a literal, so a theme can reach it.

## When Personalization Is Not Enough

Use [theme packages](/docs/theming/theme-packages) when the project needs to override files
inside the bundled template while keeping Folio's template as a base. Use
[custom templates](/docs/theming/custom-templates) when the project needs to own the entire
frontend workspace.
