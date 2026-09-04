# ThemeConfigurator

A drawer popover widget that replaces the default light/dark control when documentation presets are available. A preset owns color tokens, document rhythm, code block treatment, borders, radius defaults, typography defaults, and its own controls.

Changes are persisted in `localStorage` under a project-scoped key derived from the configured default preset and applied immediately. The default theme CSS is also rendered into the page so the generated site does not flash or fall back to Folio's bundled typography before hydration.

## API

### ThemeConfigurator

This component takes no props. It is rendered in the documentation sidebar drawer beside the existing appearance controls.

### Theme Flow

The drawer palette uses a compact two-step flow:

| Step | Purpose |
|------|---------|
| Grouped library | Choose a visual direction from Workspace, Product Docs, Reference, or Expressive. |
| Customize | Tune the selected preset's controls, surface color, accent color, shell spacing, content width, reading rhythm, borders, code blocks, typography, and corner radius. |

The Back button returns readers from Customize to the grouped library.

Light and dark selection lives in the same drawer palette as preset selection, while the keyboard shortcut still toggles between light and dark.

### Preset Library

All built-in visual directions are presets. The drawer picker shows a current theme summary before the grouped library. Each group is rendered as a compact carousel row so the panel stays short as the preset library grows.

| Group | Presets |
|-------|---------|
| Workspace | Workshop, Canopy |
| Product Docs | Beacon, Aperture, Ledger |
| Reference | Atlas, Stacks, Draftline, Proof |
| Expressive | Organic Editorial, Carbon |

| Preset | Purpose |
|--------|---------|
| Workshop | Warm generated-site workspace based on the saved inspiration example, with light paper contrast and botanical accents. |
| Canopy | Compact green workspace for simple examples, source snippets, and generated guides. |
| Beacon | Main product-docs preset with endpoint cards, compact API workflows, and high-contrast examples. |
| Atlas | Classic reference documentation with paper rhythm and sharp source examples. |
| Ledger | Dense API tables and register pages for fast scanning. |
| Proof | Printed-manual hierarchy with strong rules and editorial emphasis. |
| Stacks | Calm catalog reading for long guides and stable navigation. |
| Draftline | Working-document warmth for docs before release. |
| Aperture | Neutral developer-docs style with compact spacing and rounded code panels. |
| Organic Editorial | Poster-scale typography with cobalt organic image language for launches, programs, and editorial docs. |
| Carbon | Stark monochrome technical mode. |

Organic Editorial is the default preset because it makes generated sites feel distinctive on first load while still keeping docs controls, code blocks, and API reference pages available through the same preset system.

Each preset can be selected directly. Selecting a preset applies its default controls, typography, accent, radius, and layout defaults. Customize keeps the selected preset active while changing its options.

Workshop and Canopy include a Borders control for switching between fine, structured, and ruled outlines. This keeps the saved inspiration's framed workspace feel available without forcing every generated page into the same border weight.

### Shared Controls

Every preset can expose its own controls. The global controls are always available and override the selected preset when changed:

| Control | Purpose |
|---------|---------|
| Surface color | Override the page, sidebar, card, muted, and border palette. |
| Shell spacing | Expose the outer page padding used by framed workspace themes. |
| Content width | Adjust the prose and component measure without changing presets. |
| Reading rhythm | Override base type size, line height, section gaps, and card padding. |
| Borders | Tune card and shell rule strength globally. |
| Code blocks | Switch source examples between soft, framed, plate, and terminal treatments. |
| Typography | Switch heading, body, and code font treatment. |
| Accent color | Override the preset's primary accent. |
| Corner radius | Adjust shared UI and card radius. |

### Radius Options

| Option | Value |
|--------|-------|
| None | `0` |
| Sm | `0.3rem` |
| Md | `0.5rem` |
| Lg | `0.75rem` |
| Full | `1rem` |

The "Reset appearance" button restores the configured default preset and tuning.

### Project Theme Contract

Projects can define their own ThemeConfigurator preset in `docs.yaml` without forking the bundled template. During template preparation, Folio writes `theme/project-theme.ts` with a typed `ThemePreset` that merges Folio's base docs tokens with the project's overrides.

```yaml
theme:
  preset: "acme"
  name: "Acme"
  description: "Operational docs theme"
  scene: "Engineers scan APIs, examples, and release notes in a compact product surface."
  preview:
    light: "oklch(0.490 0.130 285)"
    dark: "oklch(0.720 0.100 285)"
  header:
    brand: "Acme"
    badge: "Platform"
    repo: "https://github.com/acme/project"
    theme_toggle: true
    action_label: "Dashboard"
    action_href: "/dashboard"
    search: false
  radius: "0.5rem"
  tune:
    font: "geist"
    accent: "ink"
    surface: "preset"
    shell: "flush"
    width: "wide"
    rhythm: "compact"
    borders: "fine"
    code: "terminal"
  style:
    "--folio-content-max-width": "74rem"
    "--folio-body-line-height": "1.58"
    "--folio-workspace-shell-topbar": "color-mix(in oklch, var(--background) 80%, transparent)"
    "--folio-workspace-shell-topbar-blur": "blur(12px)"
    "--folio-workspace-shell-topbar-border": "1px solid color-mix(in oklch, var(--border) 50%, transparent)"
  tokens:
    light:
      "--background": "oklch(0.985 0.008 80)"
      "--foreground": "oklch(0.175 0.008 75)"
      "--primary": "oklch(0.490 0.130 285)"
    dark:
      "--background": "oklch(0.155 0.010 75)"
      "--foreground": "oklch(0.950 0.008 80)"
      "--primary": "oklch(0.720 0.100 285)"
  variants:
    palette:
      label: "Palette"
      default: "default"
      options:
        default:
          label: "Default"
          swatch: "oklch(0.490 0.130 285)"
        midnight:
          label: "Midnight"
          swatch: "oklch(0.680 0.180 200)"
          tokens:
            light:
              "--background": "oklch(0.985 0.008 250)"
              "--primary": "oklch(0.480 0.160 200)"
            dark:
              "--background": "oklch(0.095 0.020 250)"
              "--primary": "oklch(0.680 0.180 200)"
```

`tokens.light` and `tokens.dark` accept CSS custom properties such as shadcn tokens (`--background`, `--card`, `--border`, `--chart-1`) and project tokens (`--status-running`). `style` accepts ThemeConfigurator layout variables such as `--folio-content-max-width`, `--folio-section-gap`, `--folio-card-padding`, `--folio-code-bg`, `--folio-workspace-shell-topbar`, `--folio-workspace-shell-topbar-blur`, and `--folio-workspace-shell-topbar-border`. Un-prefixed legacy names such as `--content-max-width` are still accepted for compatibility but are deprecated; use the `--folio-*` names.

`header.brand` and `header.badge` replace the default docs navbar wordmark. `header.repo`, `header.theme_toggle`, `header.action_label`, and `header.action_href` replace the default docs navbar actions with project-owned actions; `header.search: false` hides the navbar search field while leaving the generated search index controlled by `search.enabled`. `variants` defines project-owned preset controls; each option can set a `swatch` for the control UI, override `preview`, `style`, and light/dark tokens while inheriting the base project theme. If an option has `swatch` but no full light/dark `preview`, Folio uses the swatch for both preview modes.

For safety, token and style keys must be CSS custom properties beginning with `--`, values must be strings without CSS statement or block delimiters, and header and variant labels cannot include markup. Unknown `tune` keys are ignored with a warning.

`theme.radius` must be one of the fixed radius scale values `"0"`, `"0.3rem"`, `"0.5rem"`, `"0.75rem"`, or `"1rem"`, or a named alias (`"none"`, `"sm"`, `"md"`, `"lg"`, `"full"`) that maps onto the same scale; any other value fails config validation. `theme.variants` is capped at 256 option combinations across all controls (the product of each control's option count) because every combination is resolved and embedded into each generated page; a larger product fails config validation.

Tune aliases map to the shared controls:

| YAML key | Runtime control |
|----------|-----------------|
| `font` | `fontId` |
| `accent` / `color` | `colorId` |
| `surface` | `surfaceColorId` |
| `shell` | `shellPaddingId` |
| `width` / `content_width` | `contentWidthId` |
| `rhythm` / `reading` | `rhythmId` |
| `borders` / `border` | `borderId` |
| `code` / `code_blocks` | `codeTreatmentId` |

`font: "geist"` selects the bundled Geist/Geist Mono pair and maps the public `--font-sans` / `--font-mono` tokens used by Tailwind utility classes. If `theme.preset` matches a built-in preset and the project only provides `tune`, Folio keeps the built-in preset and applies the configured defaults. If the project supplies `name`, `description`, `preview`, `style`, `tokens`, or `variants`, Folio adds a Project group to the drawer and places the project preset before the built-in library.

### Theme Packages

Theme packages can replace the bundled configurator, project header actions, or
`theme/project-theme.ts` while Folio still supplies generated content and
metadata. See [Theme Packages](../theming/theme-packages) for the ownership
model, file overlay rules, and validation checklist.

### Create a Custom Preset

Custom presets live in `template/theme/presets.ts` and use the interfaces from `template/theme/preset-types.ts`.

1. Create a new object that satisfies `ThemePreset`.
2. Give it stable `defaultOptions`, optional `defaultRadiusIndex`, optional `defaultCustomization`, and matching `controls`.
3. Implement `resolve(options)` so every option combination returns `light`, `dark`, `style`, `radius`, and `preview`.
4. Add the exported preset to `presets`.

The `style` object must use the namespaced `--folio-*` keys defined by `ThemeStyle` in `template/theme/theme-contract.generated.ts` (generated from `folio/schemas/theme_contract.py`). Un-prefixed keys such as `--card-shadow` fail the TypeScript check against `ThemeStyle` and are not read by the generated CSS.

Example:

```ts
import type { ThemePreset } from "./preset-types"

export const notebookPreset: ThemePreset = {
  id: "notebook",
  name: "Notebook",
  description: "Lab notes, ruled paper, compact examples",
  scene: "A maintainer reviews examples and release notes in a working notebook before publishing.",
  preview: {
    light: "oklch(0.34 0.035 236)",
    dark: "oklch(0.78 0.040 236)",
  },
  defaultOptions: {
    paper: "ruled",
    code: "margin",
  },
  defaultRadiusIndex: 1,
  defaultCustomization: {
    fontId: "sans",
    colorId: "indigo",
  },
  controls: [
    {
      id: "paper",
      label: "Paper",
      options: [
        { label: "Ruled", value: "ruled" },
        { label: "Plain", value: "plain" },
      ],
    },
    {
      id: "code",
      label: "Code",
      options: [
        { label: "Margin", value: "margin" },
        { label: "Block", value: "block" },
      ],
    },
  ],
  resolve(options) {
    const ruled = options.paper === "ruled"
    const blockCode = options.code === "block"

    return {
      preview: {
        light: "oklch(0.34 0.035 236)",
        dark: "oklch(0.78 0.040 236)",
      },
      radius: "0.25rem",
      style: {
        "--folio-heading-font-family": "Georgia, \"Times New Roman\", ui-serif, serif",
        "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, sans-serif",
        "--folio-code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
        "--folio-heading-letter-spacing": "0",
        "--folio-heading-weight": "780",
        "--folio-body-line-height": ruled ? "1.78" : "1.70",
        "--folio-font-size-base": "1rem",
        "--folio-card-shadow": "none",
        "--folio-card-border-width": "1px",
        "--folio-card-padding": "1.25rem",
        "--folio-card-hover-shadow": "0 0 0 1px var(--foreground)",
        "--folio-card-backdrop": "none",
        "--folio-card-opacity": "1",
        "--folio-code-border-radius": blockCode ? "0.2rem" : "0",
        "--folio-code-border": blockCode ? "1px solid var(--border)" : "1px solid var(--foreground)",
        "--folio-code-bg": blockCode ? "var(--muted)" : "var(--background)",
        "--folio-code-foreground": "inherit",
        "--folio-code-shadow": "none",
        "--folio-h2-border": ruled ? "1px solid var(--border)" : "none",
        "--folio-h2-transform": "none",
        "--folio-h2-letter-spacing": "0",
        "--folio-h2-weight": "760",
        "--folio-h2-padding-left": "0",
        "--folio-h2-border-left": "none",
        "--folio-link-decoration": "underline",
        "--folio-section-gap": ruled ? "2.5rem" : "2.75rem",
        "--folio-content-max-width": "48rem",
        "--folio-workspace-shell-padding": "0px",
        "--folio-workspace-shell-border": "0 solid transparent",
        "--folio-workspace-shell-shadow": "none",
        "--folio-workspace-shell-background": "var(--background)",
        "--folio-workspace-shell-surface": "transparent",
        "--folio-workspace-shell-topbar": "var(--background)",
        "--folio-workspace-shell-topbar-blur": "none",
        "--folio-workspace-shell-topbar-border": "1px solid var(--border)",
      },
      light: {
        "--background": "oklch(0.976 0.006 236)",
        "--foreground": "oklch(0.180 0.012 236)",
        "--card": "oklch(0.988 0.005 236)",
        "--card-foreground": "oklch(0.180 0.012 236)",
        "--popover": "oklch(0.992 0.005 236)",
        "--popover-foreground": "oklch(0.180 0.012 236)",
        "--primary": "oklch(0.340 0.060 236)",
        "--primary-foreground": "oklch(0.976 0.006 236)",
        "--secondary": "oklch(0.935 0.007 236)",
        "--secondary-foreground": "oklch(0.180 0.012 236)",
        "--muted": "oklch(0.935 0.007 236)",
        "--muted-foreground": "oklch(0.460 0.012 236)",
        "--accent": "oklch(0.890 0.018 236)",
        "--accent-foreground": "oklch(0.180 0.012 236)",
        "--destructive": "oklch(0.550 0.200 28)",
        "--border": "oklch(0.760 0.010 236)",
        "--input": "oklch(0.760 0.010 236)",
        "--ring": "oklch(0.340 0.060 236)",
        "--chart-1": "oklch(0.340 0.060 236)",
        "--chart-2": "oklch(0.500 0.040 180)",
        "--chart-3": "oklch(0.560 0.070 120)",
        "--chart-4": "oklch(0.520 0.090 48)",
        "--chart-5": "oklch(0.420 0.040 290)",
        "--sidebar": "oklch(0.950 0.006 236)",
        "--sidebar-foreground": "oklch(0.180 0.012 236)",
        "--sidebar-primary": "oklch(0.340 0.060 236)",
        "--sidebar-primary-foreground": "oklch(0.976 0.006 236)",
        "--sidebar-accent": "oklch(0.915 0.008 236)",
        "--sidebar-accent-foreground": "oklch(0.180 0.012 236)",
        "--sidebar-border": "oklch(0.760 0.010 236)",
        "--sidebar-ring": "oklch(0.340 0.060 236)",
      },
      dark: {
        "--background": "oklch(0.120 0.012 236)",
        "--foreground": "oklch(0.910 0.007 236)",
        "--card": "oklch(0.155 0.012 236)",
        "--card-foreground": "oklch(0.910 0.007 236)",
        "--popover": "oklch(0.170 0.012 236)",
        "--popover-foreground": "oklch(0.910 0.007 236)",
        "--primary": "oklch(0.780 0.060 236)",
        "--primary-foreground": "oklch(0.120 0.012 236)",
        "--secondary": "oklch(0.205 0.012 236)",
        "--secondary-foreground": "oklch(0.910 0.007 236)",
        "--muted": "oklch(0.205 0.012 236)",
        "--muted-foreground": "oklch(0.620 0.008 236)",
        "--accent": "oklch(0.250 0.020 236)",
        "--accent-foreground": "oklch(0.910 0.007 236)",
        "--destructive": "oklch(0.650 0.180 28)",
        "--border": "oklch(0.315 0.012 236)",
        "--input": "oklch(0.315 0.012 236)",
        "--ring": "oklch(0.780 0.060 236)",
        "--chart-1": "oklch(0.780 0.060 236)",
        "--chart-2": "oklch(0.640 0.040 180)",
        "--chart-3": "oklch(0.680 0.070 120)",
        "--chart-4": "oklch(0.680 0.090 48)",
        "--chart-5": "oklch(0.620 0.050 290)",
        "--sidebar": "oklch(0.100 0.012 236)",
        "--sidebar-foreground": "oklch(0.910 0.007 236)",
        "--sidebar-primary": "oklch(0.780 0.060 236)",
        "--sidebar-primary-foreground": "oklch(0.100 0.012 236)",
        "--sidebar-accent": "oklch(0.190 0.012 236)",
        "--sidebar-accent-foreground": "oklch(0.910 0.007 236)",
        "--sidebar-border": "oklch(0.315 0.012 236)",
        "--sidebar-ring": "oklch(0.780 0.060 236)",
      },
    }
  },
}
```

Then register it:

```ts
export const presets: ThemePreset[] = [
  workshopPreset,
  canopyPreset,
  beaconPreset,
  atlasPreset,
  ledgerPreset,
  proofPreset,
  stacksPreset,
  draftlinePreset,
  aperturePreset,
  organicEditorialPreset,
  carbonPreset,
  notebookPreset,
]
```

### Generate a Preset with ChatGPT

Paste this prompt into ChatGPT, then add the returned object to `template/theme/presets.ts`.

```text
Create a documentation theme preset as a TypeScript object that satisfies ThemePreset from ./preset-types.

Rules:
- Return only TypeScript code.
- No gradients, no neon, no glow.
- Use OKLCH colors.
- Include id, name, description, scene, preview, defaultOptions, controls, defaultRadiusIndex, defaultCustomization, and resolve(options).
- The preset must feel like a documentation material system, not a decorative skin.
- Controls should change real aspects of the preset, such as paper tone, rule weight, density, code block treatment, or contrast.
- resolve(options) must return preview, radius, style, light, and dark.
- style must include every ThemeStyle key.
- light and dark must include every shadcn color token used by the existing built-in presets.

Preset concept:
[describe the material or publishing idea here]
```

After ChatGPT returns a preset:

1. Paste it into `template/theme/presets.ts`.
2. Add the exported preset to `presets`.
3. Run `pnpm run lint` from `template`.
4. Build the docs and open the drawer palette button.
5. Test each generated control in light and dark mode.

## Example

<PreviewCode>

```mdx
<ThemeConfigurator />
```

<Callout type="info" title="Layout Component">
  ThemeConfigurator is rendered in the documentation drawer when theme presets are available. If presets are disabled, Nextra's native light/dark control remains in place.
</Callout>

</PreviewCode>
