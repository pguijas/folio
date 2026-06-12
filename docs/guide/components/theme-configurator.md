# ThemeConfigurator

A drawer popover widget that replaces the default light/dark control when documentation presets are available. A preset owns color tokens, document rhythm, code block treatment, borders, radius defaults, typography defaults, and its own controls.

Changes are persisted in `localStorage` under the key `folio-theme` and applied immediately.

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
| Code blocks | Switch source examples between soft, framed, and plate treatments. |
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

The "Reset appearance" button restores Organic Editorial.

### Create a Custom Preset

Custom presets live in `template/theme/presets.ts` and use the interfaces from `template/theme/preset-types.ts`.

1. Create a new object that satisfies `ThemePreset`.
2. Give it stable `defaultOptions`, optional `defaultRadiusIndex`, optional `defaultCustomization`, and matching `controls`.
3. Implement `resolve(options)` so every option combination returns `light`, `dark`, `style`, `radius`, and `preview`.
4. Add the exported preset to `presets`.

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
        "--heading-font-family": "Georgia, \"Times New Roman\", ui-serif, serif",
        "--body-font-family": "var(--font-sans), ui-sans-serif, system-ui, sans-serif",
        "--code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
        "--heading-letter-spacing": "0",
        "--heading-weight": "780",
        "--body-line-height": ruled ? "1.78" : "1.70",
        "--font-size-base": "1rem",
        "--card-shadow": "none",
        "--card-border-width": "1px",
        "--card-padding": "1.25rem",
        "--card-hover-shadow": "0 0 0 1px var(--foreground)",
        "--card-backdrop": "none",
        "--card-opacity": "1",
        "--code-border-radius": blockCode ? "0.2rem" : "0",
        "--code-border": blockCode ? "1px solid var(--border)" : "1px solid var(--foreground)",
        "--code-bg": blockCode ? "var(--muted)" : "var(--background)",
        "--code-foreground": "inherit",
        "--code-shadow": "none",
        "--h2-border": ruled ? "1px solid var(--border)" : "none",
        "--h2-transform": "none",
        "--h2-letter-spacing": "0",
        "--h2-weight": "760",
        "--h2-padding-left": "0",
        "--h2-border-left": "none",
        "--link-decoration": "underline",
        "--section-gap": ruled ? "2.5rem" : "2.75rem",
        "--content-max-width": "48rem",
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
