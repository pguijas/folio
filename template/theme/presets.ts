import type {
  PresetOptionValues,
  ResolvedPresetTheme,
  ThemePreset,
  ThemeStyle,
  ThemeVars,
} from "./preset-types"
import { projectThemePreset } from "./project-theme"
import { registerPreset, registerGroup, getPresets } from "./preset-registry"

interface ThemeTokenInput {
  bg: string
  fg: string
  primary: string
  primaryFg: string
  muted: string
  mutedFg: string
  border: string
  card?: string
  popover?: string
  secondary?: string
  secondaryFg?: string
  accent?: string
  accentFg?: string
  destructive?: string
  input?: string
  charts?: [string, string, string, string, string]
  sidebar?: string
  sidebarFg?: string
  sidebarAccent?: string
  sidebarAccentFg?: string
  sidebarBorder?: string
}

function makeVars(input: ThemeTokenInput): ThemeVars {
  const card = input.card ?? input.bg
  const popover = input.popover ?? card
  const secondary = input.secondary ?? input.muted
  const secondaryFg = input.secondaryFg ?? input.fg
  const accent = input.accent ?? input.muted
  const accentFg = input.accentFg ?? input.fg
  const destructive = input.destructive ?? "oklch(0.55 0.20 28)"
  const inputColor = input.input ?? input.border
  const charts = input.charts ?? [
    input.primary,
    input.mutedFg,
    accent,
    destructive,
    input.fg,
  ]
  const sidebar = input.sidebar ?? input.bg
  const sidebarFg = input.sidebarFg ?? input.fg
  const sidebarAccent = input.sidebarAccent ?? input.muted
  const sidebarAccentFg = input.sidebarAccentFg ?? input.fg
  const sidebarBorder = input.sidebarBorder ?? input.border

  return {
    "--background": input.bg,
    "--foreground": input.fg,
    "--card": card,
    "--card-foreground": input.fg,
    "--popover": popover,
    "--popover-foreground": input.fg,
    "--primary": input.primary,
    "--primary-foreground": input.primaryFg,
    "--secondary": secondary,
    "--secondary-foreground": secondaryFg,
    "--muted": input.muted,
    "--muted-foreground": input.mutedFg,
    "--accent": accent,
    "--accent-foreground": accentFg,
    "--destructive": destructive,
    "--border": input.border,
    "--input": inputColor,
    "--ring": input.primary,
    "--chart-1": charts[0],
    "--chart-2": charts[1],
    "--chart-3": charts[2],
    "--chart-4": charts[3],
    "--chart-5": charts[4],
    "--sidebar": sidebar,
    "--sidebar-foreground": sidebarFg,
    "--sidebar-primary": input.primary,
    "--sidebar-primary-foreground": input.primaryFg,
    "--sidebar-accent": sidebarAccent,
    "--sidebar-accent-foreground": sidebarAccentFg,
    "--sidebar-border": sidebarBorder,
    "--sidebar-ring": input.primary,
  }
}

const baseStyle: ThemeStyle = {
  "--folio-heading-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
  "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
  "--folio-code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
  "--folio-heading-letter-spacing": "0",
  "--folio-heading-weight": "800",
  "--folio-body-line-height": "1.72",
  "--folio-font-size-base": "1rem",
  "--folio-card-shadow": "none",
  "--folio-card-border-width": "1px",
  "--folio-card-padding": "1.35rem",
  "--folio-card-hover-shadow": "0 0 0 1px var(--foreground)",
  "--folio-card-backdrop": "none",
  "--folio-card-opacity": "1",
  "--folio-code-border-radius": "0",
  "--folio-code-border": "1px solid var(--border)",
  "--folio-code-bg": "color-mix(in oklch, var(--muted) 86%, var(--background))",
  "--folio-code-foreground": "inherit",
  "--folio-code-shadow": "none",
  "--folio-h2-border": "1px solid var(--border)",
  "--folio-h2-transform": "none",
  "--folio-h2-letter-spacing": "0",
  "--folio-h2-weight": "800",
  "--folio-h2-padding-left": "0",
  "--folio-h2-border-left": "none",
  "--folio-link-decoration": "underline",
  "--folio-section-gap": "2.75rem",
  "--folio-content-max-width": "48rem",
  "--folio-workspace-shell-padding": "0px",
  "--folio-workspace-shell-border": "0 solid transparent",
  "--folio-workspace-shell-shadow": "none",
  "--folio-workspace-shell-background": "var(--background)",
  "--folio-workspace-shell-surface": "transparent",
  "--folio-workspace-shell-topbar": "var(--background)",
  "--folio-workspace-shell-topbar-blur": "none",
  "--folio-workspace-shell-topbar-border": "1px solid var(--border)",
}

function makeStyle(overrides: Partial<ThemeStyle> = {}): ThemeStyle {
  return { ...baseStyle, ...overrides }
}

function choose<T>(choices: Record<string, T>, value: string, fallback: string): T {
  return choices[value] ?? choices[fallback]
}

const folioPaper = {
  wove: {
    preview: { light: "oklch(0.27 0.014 82)", dark: "oklch(0.90 0.008 82)" },
    light: {
      bg: "oklch(0.966 0.008 82)",
      fg: "oklch(0.155 0.007 82)",
      card: "oklch(0.976 0.007 82)",
      popover: "oklch(0.986 0.006 82)",
      primary: "oklch(0.155 0.007 82)",
      primaryFg: "oklch(0.966 0.008 82)",
      muted: "oklch(0.920 0.007 82)",
      mutedFg: "oklch(0.420 0.007 82)",
      accent: "oklch(0.875 0.026 110)",
      border: "oklch(0.740 0.007 82)",
      sidebar: "oklch(0.940 0.007 82)",
      sidebarAccent: "oklch(0.890 0.008 82)",
      charts: [
        "oklch(0.155 0.007 82)",
        "oklch(0.500 0.007 82)",
        "oklch(0.620 0.080 130)",
        "oklch(0.560 0.120 36)",
        "oklch(0.360 0.052 250)",
      ] as [string, string, string, string, string],
    },
    dark: {
      bg: "oklch(0.130 0.007 82)",
      fg: "oklch(0.920 0.007 82)",
      card: "oklch(0.155 0.007 82)",
      popover: "oklch(0.170 0.007 82)",
      primary: "oklch(0.920 0.007 82)",
      primaryFg: "oklch(0.130 0.007 82)",
      muted: "oklch(0.210 0.007 82)",
      mutedFg: "oklch(0.620 0.007 82)",
      accent: "oklch(0.240 0.024 110)",
      border: "oklch(0.330 0.007 82)",
      sidebar: "oklch(0.105 0.007 82)",
      sidebarAccent: "oklch(0.200 0.007 82)",
      charts: [
        "oklch(0.920 0.007 82)",
        "oklch(0.680 0.007 82)",
        "oklch(0.720 0.090 130)",
        "oklch(0.690 0.120 36)",
        "oklch(0.620 0.080 250)",
      ] as [string, string, string, string, string],
    },
  },
  cotton: {
    preview: { light: "oklch(0.31 0.012 70)", dark: "oklch(0.91 0.006 70)" },
    light: {
      bg: "oklch(0.982 0.006 70)",
      fg: "oklch(0.170 0.008 70)",
      card: "oklch(0.990 0.005 70)",
      popover: "oklch(0.990 0.005 70)",
      primary: "oklch(0.170 0.008 70)",
      primaryFg: "oklch(0.982 0.006 70)",
      muted: "oklch(0.945 0.006 70)",
      mutedFg: "oklch(0.450 0.007 70)",
      accent: "oklch(0.900 0.020 95)",
      border: "oklch(0.790 0.006 70)",
      sidebar: "oklch(0.960 0.006 70)",
      sidebarAccent: "oklch(0.920 0.006 70)",
    },
    dark: {
      bg: "oklch(0.125 0.007 70)",
      fg: "oklch(0.925 0.006 70)",
      card: "oklch(0.155 0.007 70)",
      popover: "oklch(0.170 0.007 70)",
      primary: "oklch(0.925 0.006 70)",
      primaryFg: "oklch(0.125 0.007 70)",
      muted: "oklch(0.205 0.007 70)",
      mutedFg: "oklch(0.630 0.006 70)",
      accent: "oklch(0.250 0.020 95)",
      border: "oklch(0.320 0.007 70)",
      sidebar: "oklch(0.105 0.007 70)",
      sidebarAccent: "oklch(0.195 0.007 70)",
    },
  },
  parchment: {
    preview: { light: "oklch(0.34 0.025 68)", dark: "oklch(0.88 0.016 68)" },
    light: {
      bg: "oklch(0.950 0.020 68)",
      fg: "oklch(0.180 0.012 62)",
      card: "oklch(0.965 0.018 68)",
      popover: "oklch(0.980 0.014 68)",
      primary: "oklch(0.250 0.045 58)",
      primaryFg: "oklch(0.950 0.020 68)",
      muted: "oklch(0.900 0.018 68)",
      mutedFg: "oklch(0.440 0.016 64)",
      accent: "oklch(0.850 0.040 92)",
      border: "oklch(0.710 0.020 68)",
      sidebar: "oklch(0.925 0.019 68)",
      sidebarAccent: "oklch(0.880 0.020 68)",
    },
    dark: {
      bg: "oklch(0.135 0.012 62)",
      fg: "oklch(0.895 0.014 68)",
      card: "oklch(0.165 0.012 62)",
      popover: "oklch(0.180 0.012 62)",
      primary: "oklch(0.895 0.014 68)",
      primaryFg: "oklch(0.135 0.012 62)",
      muted: "oklch(0.220 0.012 62)",
      mutedFg: "oklch(0.620 0.012 68)",
      accent: "oklch(0.270 0.028 92)",
      border: "oklch(0.340 0.012 62)",
      sidebar: "oklch(0.112 0.012 62)",
      sidebarAccent: "oklch(0.205 0.012 62)",
    },
  },
  canvas: {
    preview: { light: "oklch(0.180 0.006 160)", dark: "oklch(0.930 0.004 160)" },
    light: {
      bg: "oklch(0.982 0.003 160)",
      fg: "oklch(0.180 0.006 160)",
      card: "oklch(0.995 0.002 160)",
      popover: "oklch(0.998 0.002 160)",
      primary: "oklch(0.180 0.006 160)",
      primaryFg: "oklch(0.982 0.003 160)",
      muted: "oklch(0.944 0.004 160)",
      mutedFg: "oklch(0.455 0.006 160)",
      accent: "oklch(0.910 0.026 154)",
      border: "oklch(0.860 0.004 160)",
      sidebar: "oklch(0.963 0.003 160)",
      sidebarAccent: "oklch(0.930 0.004 160)",
      charts: [
        "oklch(0.180 0.006 160)",
        "oklch(0.500 0.080 165)",
        "oklch(0.520 0.070 235)",
        "oklch(0.560 0.090 72)",
        "oklch(0.500 0.080 20)",
      ] as [string, string, string, string, string],
    },
    dark: {
      bg: "oklch(0.135 0.004 160)",
      fg: "oklch(0.930 0.004 160)",
      card: "oklch(0.170 0.004 160)",
      popover: "oklch(0.190 0.004 160)",
      primary: "oklch(0.930 0.004 160)",
      primaryFg: "oklch(0.135 0.004 160)",
      muted: "oklch(0.220 0.004 160)",
      mutedFg: "oklch(0.660 0.004 160)",
      accent: "oklch(0.265 0.032 154)",
      border: "oklch(0.305 0.004 160)",
      sidebar: "oklch(0.112 0.004 160)",
      sidebarAccent: "oklch(0.205 0.004 160)",
      charts: [
        "oklch(0.930 0.004 160)",
        "oklch(0.720 0.080 165)",
        "oklch(0.700 0.070 235)",
        "oklch(0.760 0.090 72)",
        "oklch(0.720 0.080 20)",
      ] as [string, string, string, string, string],
    },
  },
}

const folioBinding = {
  thread: {
    radius: "0",
    style: makeStyle({
      "--folio-heading-font-family": "Georgia, \"Times New Roman\", ui-serif, serif",
      "--folio-heading-weight": "900",
      "--folio-card-padding": "1.25rem",
      "--folio-h2-transform": "uppercase",
      "--folio-h2-weight": "900",
      "--folio-section-gap": "3rem",
      "--folio-content-max-width": "50rem",
    }),
  },
  case: {
    radius: "0.35rem",
    style: makeStyle({
      "--folio-heading-weight": "850",
      "--folio-card-hover-shadow": "0 6px 18px oklch(0.155 0.007 82 / 0.08)",
      "--folio-card-padding": "1.5rem",
      "--folio-section-gap": "2.75rem",
      "--folio-content-max-width": "48rem",
    }),
  },
  index: {
    radius: "0.15rem",
    style: makeStyle({
      "--folio-card-border-width": "1.5px",
      "--folio-card-padding": "1.1rem",
      "--folio-h2-transform": "uppercase",
      "--folio-h2-weight": "900",
      "--folio-section-gap": "2.5rem",
      "--folio-content-max-width": "46rem",
    }),
  },
  reference: {
    radius: "0.75rem",
    style: makeStyle({
      "--folio-heading-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-heading-weight": "700",
      "--folio-body-line-height": "1.62",
      "--folio-font-size-base": "0.975rem",
      "--folio-card-shadow": "0 14px 40px -34px oklch(0.180 0.006 160 / 0.28)",
      "--folio-card-border-width": "1px",
      "--folio-card-padding": "1rem",
      "--folio-card-hover-shadow": "0 18px 54px -42px oklch(0.180 0.006 160 / 0.38)",
      "--folio-h2-border": "none",
      "--folio-h2-transform": "none",
      "--folio-h2-weight": "700",
      "--folio-link-decoration": "none",
      "--folio-section-gap": "2.25rem",
      "--folio-content-max-width": "54rem",
    }),
  },
}

const folioCode = {
  ink: {
    "--folio-code-bg": "color-mix(in oklch, var(--muted) 86%, var(--background))",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid color-mix(in oklch, var(--border) 72%, var(--background))",
    "--folio-code-border-radius": "0.45rem",
  },
  paper: {
    "--folio-code-bg": "var(--muted)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid var(--border)",
    "--folio-code-border-radius": "0.25rem",
  },
  plate: {
    "--folio-code-bg": "var(--card)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1.5px solid var(--foreground)",
    "--folio-code-border-radius": "0",
  },
  panel: {
    "--folio-code-bg": "var(--muted)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid var(--border)",
    "--folio-code-border-radius": "0.7rem",
  },
} satisfies Record<string, Partial<ThemeStyle>>

function resolveFolio(options: PresetOptionValues): ResolvedPresetTheme {
  const paper = choose(folioPaper, options.paper, "wove")
  const binding = choose(folioBinding, options.binding, "thread")
  const code = choose(folioCode, options.code, "ink")

  return {
    preview: paper.preview,
    radius: binding.radius,
    style: makeStyle({ ...binding.style, ...code }),
    light: makeVars(paper.light),
    dark: makeVars(paper.dark),
  }
}

function resolveLedger(options: PresetOptionValues): ResolvedPresetTheme {
  const density = choose(
    {
      compact: {
        lineHeight: "1.58",
        sectionGap: "2.15rem",
        padding: "1rem",
        width: "54rem",
        fontSize: "0.975rem",
      },
      balanced: {
        lineHeight: "1.68",
        sectionGap: "2.5rem",
        padding: "1.2rem",
        width: "50rem",
        fontSize: "1rem",
      },
      roomy: {
        lineHeight: "1.82",
        sectionGap: "3rem",
        padding: "1.5rem",
        width: "48rem",
        fontSize: "1.025rem",
      },
    },
    options.density,
    "balanced"
  )
  const rule = choose(
    {
      fine: { border: "1px", h2: "1px solid var(--border)" },
      ruled: { border: "1.5px", h2: "1.5px solid var(--foreground)" },
    },
    options.rules,
    "fine"
  )

  return {
    preview: { light: "oklch(0.36 0.038 154)", dark: "oklch(0.76 0.050 154)" },
    radius: "0.2rem",
    style: makeStyle({
      "--folio-body-line-height": density.lineHeight,
      "--folio-font-size-base": density.fontSize,
      "--folio-card-border-width": rule.border,
      "--folio-card-padding": density.padding,
      "--folio-h2-border": rule.h2,
      "--folio-section-gap": density.sectionGap,
      "--folio-content-max-width": density.width,
      "--folio-code-border-radius": "0.15rem",
      "--folio-link-decoration": "underline",
    }),
    light: makeVars({
      bg: "oklch(0.972 0.008 132)",
      fg: "oklch(0.170 0.012 138)",
      card: "oklch(0.982 0.006 132)",
      popover: "oklch(0.990 0.006 132)",
      primary: "oklch(0.360 0.070 154)",
      primaryFg: "oklch(0.980 0.006 132)",
      muted: "oklch(0.930 0.010 132)",
      mutedFg: "oklch(0.430 0.018 145)",
      accent: "oklch(0.885 0.026 150)",
      border: "oklch(0.750 0.014 132)",
      sidebar: "oklch(0.945 0.010 132)",
      sidebarAccent: "oklch(0.900 0.014 136)",
      charts: [
        "oklch(0.360 0.070 154)",
        "oklch(0.420 0.045 118)",
        "oklch(0.550 0.070 180)",
        "oklch(0.500 0.090 58)",
        "oklch(0.360 0.040 260)",
      ],
    }),
    dark: makeVars({
      bg: "oklch(0.120 0.012 138)",
      fg: "oklch(0.910 0.008 132)",
      card: "oklch(0.155 0.012 138)",
      popover: "oklch(0.170 0.012 138)",
      primary: "oklch(0.740 0.075 154)",
      primaryFg: "oklch(0.120 0.012 138)",
      muted: "oklch(0.205 0.014 138)",
      mutedFg: "oklch(0.620 0.014 136)",
      accent: "oklch(0.250 0.030 150)",
      border: "oklch(0.315 0.014 138)",
      sidebar: "oklch(0.100 0.012 138)",
      sidebarAccent: "oklch(0.195 0.014 138)",
    }),
  }
}

function resolvePress(options: PresetOptionValues): ResolvedPresetTheme {
  const ink = choose(
    {
      graphite: {
        fg: "oklch(0.165 0.005 78)",
        darkFg: "oklch(0.910 0.005 78)",
        primary: "oklch(0.165 0.005 78)",
      },
      black: {
        fg: "oklch(0.105 0.004 78)",
        darkFg: "oklch(0.940 0.004 78)",
        primary: "oklch(0.105 0.004 78)",
      },
    },
    options.ink,
    "graphite"
  )
  const impression = choose(
    {
      clean: { border: "1px", weight: "820", code: "0.2rem" },
      heavy: { border: "1.75px", weight: "900", code: "0" },
    },
    options.impression,
    "clean"
  )

  return {
    preview: { light: ink.primary, dark: ink.darkFg },
    radius: "0",
    style: makeStyle({
      "--folio-heading-weight": impression.weight,
      "--folio-card-border-width": impression.border,
      "--folio-card-padding": "1.2rem",
      "--folio-code-border-radius": impression.code,
      "--folio-code-border": `${impression.border} solid var(--foreground)`,
      "--folio-h2-border": `${impression.border} solid var(--foreground)`,
      "--folio-h2-transform": "uppercase",
      "--folio-h2-weight": impression.weight,
      "--folio-section-gap": "2.6rem",
      "--folio-content-max-width": "47rem",
    }),
    light: makeVars({
      bg: "oklch(0.970 0.004 78)",
      fg: ink.fg,
      card: "oklch(0.980 0.004 78)",
      popover: "oklch(0.990 0.004 78)",
      primary: ink.primary,
      primaryFg: "oklch(0.970 0.004 78)",
      muted: "oklch(0.925 0.004 78)",
      mutedFg: "oklch(0.420 0.004 78)",
      accent: "oklch(0.880 0.030 62)",
      border: "oklch(0.700 0.004 78)",
      sidebar: "oklch(0.945 0.004 78)",
      sidebarAccent: "oklch(0.900 0.004 78)",
    }),
    dark: makeVars({
      bg: "oklch(0.115 0.004 78)",
      fg: ink.darkFg,
      card: "oklch(0.145 0.004 78)",
      popover: "oklch(0.165 0.004 78)",
      primary: ink.darkFg,
      primaryFg: "oklch(0.115 0.004 78)",
      muted: "oklch(0.195 0.004 78)",
      mutedFg: "oklch(0.620 0.004 78)",
      accent: "oklch(0.250 0.030 62)",
      border: "oklch(0.330 0.004 78)",
      sidebar: "oklch(0.095 0.004 78)",
      sidebarAccent: "oklch(0.185 0.004 78)",
    }),
  }
}

function resolveArchive(options: PresetOptionValues): ResolvedPresetTheme {
  const tone = choose(
    {
      slate: {
        hue: "248",
        primary: "oklch(0.390 0.060 248)",
        darkPrimary: "oklch(0.730 0.065 248)",
      },
      catalog: {
        hue: "206",
        primary: "oklch(0.370 0.055 206)",
        darkPrimary: "oklch(0.720 0.060 206)",
      },
      sepia: {
        hue: "70",
        primary: "oklch(0.350 0.040 70)",
        darkPrimary: "oklch(0.740 0.045 70)",
      },
    },
    options.tone,
    "catalog"
  )
  const reading = choose(
    {
      standard: { lineHeight: "1.74", width: "48rem", gap: "2.75rem" },
      spacious: { lineHeight: "1.88", width: "46rem", gap: "3.25rem" },
    },
    options.reading,
    "standard"
  )

  return {
    preview: { light: tone.primary, dark: tone.darkPrimary },
    radius: "0.45rem",
    style: makeStyle({
      "--folio-heading-weight": "760",
      "--folio-body-line-height": reading.lineHeight,
      "--folio-card-padding": "1.45rem",
      "--folio-code-border-radius": "0.35rem",
      "--folio-section-gap": reading.gap,
      "--folio-content-max-width": reading.width,
    }),
    light: makeVars({
      bg: `oklch(0.970 0.007 ${tone.hue})`,
      fg: `oklch(0.180 0.012 ${tone.hue})`,
      card: `oklch(0.982 0.006 ${tone.hue})`,
      popover: `oklch(0.990 0.006 ${tone.hue})`,
      primary: tone.primary,
      primaryFg: `oklch(0.970 0.007 ${tone.hue})`,
      muted: `oklch(0.930 0.008 ${tone.hue})`,
      mutedFg: `oklch(0.460 0.012 ${tone.hue})`,
      accent: `oklch(0.880 0.018 ${tone.hue})`,
      border: `oklch(0.760 0.009 ${tone.hue})`,
      sidebar: `oklch(0.945 0.008 ${tone.hue})`,
      sidebarAccent: `oklch(0.905 0.009 ${tone.hue})`,
    }),
    dark: makeVars({
      bg: `oklch(0.120 0.011 ${tone.hue})`,
      fg: `oklch(0.910 0.007 ${tone.hue})`,
      card: `oklch(0.155 0.011 ${tone.hue})`,
      popover: `oklch(0.170 0.011 ${tone.hue})`,
      primary: tone.darkPrimary,
      primaryFg: `oklch(0.120 0.011 ${tone.hue})`,
      muted: `oklch(0.205 0.011 ${tone.hue})`,
      mutedFg: `oklch(0.620 0.008 ${tone.hue})`,
      accent: `oklch(0.250 0.018 ${tone.hue})`,
      border: `oklch(0.315 0.011 ${tone.hue})`,
      sidebar: `oklch(0.100 0.011 ${tone.hue})`,
      sidebarAccent: `oklch(0.190 0.011 ${tone.hue})`,
    }),
  }
}

function resolveDraft(options: PresetOptionValues): ResolvedPresetTheme {
  const pencil = choose(
    {
      soft: { fg: "oklch(0.255 0.006 88)", primary: "oklch(0.340 0.010 88)" },
      firm: { fg: "oklch(0.185 0.006 88)", primary: "oklch(0.240 0.012 88)" },
    },
    options.pencil,
    "soft"
  )
  const marks = choose(
    {
      quiet: { border: "oklch(0.800 0.008 88)", h2: "1px dashed var(--border)" },
      visible: { border: "oklch(0.690 0.010 88)", h2: "1px solid var(--foreground)" },
    },
    options.marks,
    "quiet"
  )

  return {
    preview: { light: pencil.primary, dark: "oklch(0.820 0.006 88)" },
    radius: "0.25rem",
    style: makeStyle({
      "--folio-heading-weight": "720",
      "--folio-body-line-height": "1.82",
      "--folio-card-border-width": "1px",
      "--folio-card-padding": "1.35rem",
      "--folio-code-border-radius": "0.25rem",
      "--folio-h2-border": marks.h2,
      "--folio-section-gap": "3rem",
      "--folio-content-max-width": "47rem",
    }),
    light: makeVars({
      bg: "oklch(0.976 0.006 88)",
      fg: pencil.fg,
      card: "oklch(0.986 0.005 88)",
      popover: "oklch(0.990 0.005 88)",
      primary: pencil.primary,
      primaryFg: "oklch(0.976 0.006 88)",
      muted: "oklch(0.940 0.006 88)",
      mutedFg: "oklch(0.500 0.006 88)",
      accent: "oklch(0.900 0.012 88)",
      border: marks.border,
      sidebar: "oklch(0.955 0.006 88)",
      sidebarAccent: "oklch(0.920 0.006 88)",
    }),
    dark: makeVars({
      bg: "oklch(0.135 0.006 88)",
      fg: "oklch(0.900 0.006 88)",
      card: "oklch(0.165 0.006 88)",
      popover: "oklch(0.180 0.006 88)",
      primary: "oklch(0.820 0.006 88)",
      primaryFg: "oklch(0.135 0.006 88)",
      muted: "oklch(0.220 0.006 88)",
      mutedFg: "oklch(0.630 0.006 88)",
      accent: "oklch(0.255 0.010 88)",
      border: "oklch(0.340 0.006 88)",
      sidebar: "oklch(0.112 0.006 88)",
      sidebarAccent: "oklch(0.205 0.006 88)",
    }),
  }
}

function resolveCarbon(options: PresetOptionValues): ResolvedPresetTheme {
  const contrast = choose(
    {
      tempered: {
        bg: "oklch(0.970 0.006 70)",
        fg: "oklch(0.160 0.008 70)",
        darkBg: "oklch(0.120 0.008 70)",
        darkFg: "oklch(0.920 0.006 70)",
      },
      stark: {
        bg: "oklch(0.945 0.004 70)",
        fg: "oklch(0.105 0.004 70)",
        darkBg: "oklch(0.095 0.004 70)",
        darkFg: "oklch(0.945 0.004 70)",
      },
    },
    options.contrast,
    "tempered"
  )
  const code = choose(
    {
      block: {
        "--folio-code-bg": "color-mix(in oklch, var(--muted) 86%, var(--background))",
        "--folio-code-foreground": "inherit",
        "--folio-code-border": "1.5px solid color-mix(in oklch, var(--border) 72%, var(--background))",
      },
      outline: {
        "--folio-code-bg": "var(--background)",
        "--folio-code-foreground": "inherit",
        "--folio-code-border": "1.5px solid var(--foreground)",
      },
    },
    options.code,
    "block"
  )

  return {
    preview: { light: contrast.fg, dark: contrast.darkFg },
    radius: "0",
    style: makeStyle({
      "--folio-heading-weight": "900",
      "--folio-card-border-width": "1.5px",
      "--folio-card-padding": "1.25rem",
      "--folio-card-hover-shadow": "3px 3px 0 0 var(--foreground)",
      "--folio-code-border-radius": "0",
      "--folio-h2-transform": "uppercase",
      "--folio-h2-weight": "900",
      "--folio-section-gap": "2.5rem",
      "--folio-content-max-width": "44rem",
      ...code,
    }),
    light: makeVars({
      bg: contrast.bg,
      fg: contrast.fg,
      card: contrast.bg,
      popover: "oklch(0.980 0.006 70)",
      primary: contrast.fg,
      primaryFg: contrast.bg,
      muted: "oklch(0.925 0.006 70)",
      mutedFg: "oklch(0.450 0.006 70)",
      accent: "oklch(0.905 0.006 70)",
      border: "oklch(0.800 0.006 70)",
      sidebar: "oklch(0.945 0.006 70)",
      sidebarAccent: "oklch(0.910 0.006 70)",
      charts: [
        contrast.fg,
        "oklch(0.360 0.006 70)",
        "oklch(0.560 0.006 70)",
        "oklch(0.260 0.006 70)",
        "oklch(0.700 0.006 70)",
      ],
    }),
    dark: makeVars({
      bg: contrast.darkBg,
      fg: contrast.darkFg,
      card: contrast.darkBg,
      popover: "oklch(0.140 0.006 70)",
      primary: contrast.darkFg,
      primaryFg: contrast.darkBg,
      muted: "oklch(0.180 0.006 70)",
      mutedFg: "oklch(0.560 0.006 70)",
      accent: "oklch(0.205 0.006 70)",
      border: "oklch(0.260 0.006 70)",
      sidebar: "oklch(0.100 0.006 70)",
      sidebarAccent: "oklch(0.185 0.006 70)",
    }),
  }
}

const beaconSurfaces = {
  studio: {
    preview: { light: "oklch(0.470 0.120 258)", dark: "oklch(0.780 0.080 258)" },
    light: {
      bg: "oklch(0.982 0.006 250)",
      fg: "oklch(0.175 0.014 254)",
      card: "oklch(0.996 0.004 250)",
      popover: "oklch(0.998 0.004 250)",
      primary: "oklch(0.470 0.120 258)",
      primaryFg: "oklch(0.985 0.006 250)",
      muted: "oklch(0.936 0.008 250)",
      mutedFg: "oklch(0.455 0.016 254)",
      accent: "oklch(0.900 0.050 162)",
      border: "oklch(0.825 0.010 250)",
      sidebar: "oklch(0.958 0.008 250)",
      sidebarAccent: "oklch(0.925 0.014 258)",
      charts: [
        "oklch(0.470 0.120 258)",
        "oklch(0.590 0.115 162)",
        "oklch(0.670 0.120 76)",
        "oklch(0.560 0.155 26)",
        "oklch(0.440 0.035 252)",
      ] as [string, string, string, string, string],
    },
    dark: {
      bg: "oklch(0.125 0.014 254)",
      fg: "oklch(0.928 0.008 250)",
      card: "oklch(0.160 0.016 254)",
      popover: "oklch(0.178 0.016 254)",
      primary: "oklch(0.780 0.080 258)",
      primaryFg: "oklch(0.125 0.014 254)",
      muted: "oklch(0.220 0.016 254)",
      mutedFg: "oklch(0.660 0.012 250)",
      accent: "oklch(0.275 0.052 162)",
      border: "oklch(0.315 0.016 254)",
      sidebar: "oklch(0.105 0.014 254)",
      sidebarAccent: "oklch(0.205 0.020 258)",
      charts: [
        "oklch(0.780 0.080 258)",
        "oklch(0.720 0.100 162)",
        "oklch(0.790 0.110 76)",
        "oklch(0.720 0.145 26)",
        "oklch(0.690 0.034 252)",
      ] as [string, string, string, string, string],
    },
  },
  console: {
    preview: { light: "oklch(0.390 0.052 252)", dark: "oklch(0.805 0.056 252)" },
    light: {
      bg: "oklch(0.972 0.008 252)",
      fg: "oklch(0.150 0.018 252)",
      card: "oklch(0.988 0.006 252)",
      popover: "oklch(0.994 0.006 252)",
      primary: "oklch(0.390 0.085 252)",
      primaryFg: "oklch(0.982 0.006 252)",
      muted: "oklch(0.920 0.010 252)",
      mutedFg: "oklch(0.430 0.018 252)",
      accent: "oklch(0.890 0.038 186)",
      border: "oklch(0.780 0.012 252)",
      sidebar: "oklch(0.938 0.010 252)",
      sidebarAccent: "oklch(0.900 0.014 252)",
    },
    dark: {
      bg: "oklch(0.108 0.018 252)",
      fg: "oklch(0.925 0.008 252)",
      card: "oklch(0.145 0.020 252)",
      popover: "oklch(0.165 0.020 252)",
      primary: "oklch(0.805 0.056 252)",
      primaryFg: "oklch(0.108 0.018 252)",
      muted: "oklch(0.198 0.020 252)",
      mutedFg: "oklch(0.620 0.014 252)",
      accent: "oklch(0.245 0.045 186)",
      border: "oklch(0.290 0.020 252)",
      sidebar: "oklch(0.090 0.018 252)",
      sidebarAccent: "oklch(0.185 0.022 252)",
    },
  },
}

const beaconDensity = {
  docs: {
    lineHeight: "1.66",
    sectionGap: "2.35rem",
    padding: "1.1rem",
    width: "55rem",
    fontSize: "0.985rem",
    headingWeight: "780",
    h2Weight: "760",
  },
  workbench: {
    lineHeight: "1.58",
    sectionGap: "2rem",
    padding: "0.95rem",
    width: "58rem",
    fontSize: "0.955rem",
    headingWeight: "760",
    h2Weight: "740",
  },
}

const beaconCode = {
  terminal: {
    "--folio-code-bg": "color-mix(in oklch, var(--muted) 86%, var(--background))",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid color-mix(in oklch, var(--border) 72%, var(--background))",
    "--folio-code-border-radius": "0.65rem",
  },
  panel: {
    "--folio-code-bg": "var(--muted)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid var(--border)",
    "--folio-code-border-radius": "0.65rem",
  },
} satisfies Record<string, Partial<ThemeStyle>>

function resolveBeacon(options: PresetOptionValues): ResolvedPresetTheme {
  const surface = choose(beaconSurfaces, options.surface, "studio")
  const density = choose(beaconDensity, options.density, "docs")
  const code = choose(beaconCode, options.code, "terminal")

  return {
    preview: surface.preview,
    radius: "0.7rem",
    style: makeStyle({
      "--folio-heading-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-heading-weight": density.headingWeight,
      "--folio-body-line-height": density.lineHeight,
      "--folio-font-size-base": density.fontSize,
      "--folio-card-shadow": "0 18px 60px -44px oklch(0.175 0.014 254 / 0.45)",
      "--folio-card-border-width": "1px",
      "--folio-card-padding": density.padding,
      "--folio-card-hover-shadow": "0 20px 64px -44px oklch(0.175 0.014 254 / 0.55)",
      "--folio-h2-border": "1px solid var(--border)",
      "--folio-h2-transform": "uppercase",
      "--folio-h2-weight": density.h2Weight,
      "--folio-link-decoration": "none",
      "--folio-section-gap": density.sectionGap,
      "--folio-content-max-width": density.width,
      ...code,
    }),
    light: makeVars(surface.light),
    dark: makeVars(surface.dark),
  }
}

const sourceWorkspaceSurfaces = {
  paper: {
    preview: { light: "oklch(0.315 0.050 145)", dark: "oklch(0.760 0.070 145)" },
    light: {
      bg: "oklch(0.966 0.008 82)",
      fg: "oklch(0.155 0.007 82)",
      card: "oklch(0.976 0.007 82)",
      popover: "oklch(0.982 0.006 82)",
      primary: "oklch(0.315 0.050 145)",
      primaryFg: "oklch(0.966 0.008 82)",
      muted: "oklch(0.920 0.007 82)",
      mutedFg: "oklch(0.420 0.007 82)",
      accent: "oklch(0.875 0.026 110)",
      border: "oklch(0.740 0.007 82)",
      sidebar: "oklch(0.940 0.007 82)",
      sidebarAccent: "oklch(0.890 0.008 82)",
      charts: [
        "oklch(0.315 0.050 145)",
        "oklch(0.420 0.007 82)",
        "oklch(0.620 0.080 130)",
        "oklch(0.560 0.120 36)",
        "oklch(0.360 0.052 250)",
      ] as [string, string, string, string, string],
    },
    dark: {
      bg: "oklch(0.140 0.008 82)",
      fg: "oklch(0.925 0.007 82)",
      card: "oklch(0.170 0.008 82)",
      popover: "oklch(0.185 0.008 82)",
      primary: "oklch(0.760 0.070 145)",
      primaryFg: "oklch(0.140 0.008 82)",
      muted: "oklch(0.225 0.008 82)",
      mutedFg: "oklch(0.660 0.007 82)",
      accent: "oklch(0.260 0.036 110)",
      border: "oklch(0.340 0.008 82)",
      sidebar: "oklch(0.115 0.008 82)",
      sidebarAccent: "oklch(0.205 0.010 82)",
      charts: [
        "oklch(0.760 0.070 145)",
        "oklch(0.680 0.007 82)",
        "oklch(0.730 0.090 130)",
        "oklch(0.700 0.120 36)",
        "oklch(0.650 0.080 250)",
      ] as [string, string, string, string, string],
    },
  },
  moss: {
    preview: { light: "oklch(0.300 0.060 144)", dark: "oklch(0.770 0.078 144)" },
    light: {
      bg: "oklch(0.958 0.014 112)",
      fg: "oklch(0.150 0.010 128)",
      card: "oklch(0.974 0.012 112)",
      popover: "oklch(0.982 0.010 112)",
      primary: "oklch(0.300 0.060 144)",
      primaryFg: "oklch(0.970 0.010 112)",
      muted: "oklch(0.900 0.018 112)",
      mutedFg: "oklch(0.410 0.020 128)",
      accent: "oklch(0.840 0.045 120)",
      border: "oklch(0.720 0.018 112)",
      sidebar: "oklch(0.925 0.018 112)",
      sidebarAccent: "oklch(0.872 0.026 120)",
      charts: [
        "oklch(0.300 0.060 144)",
        "oklch(0.460 0.050 116)",
        "oklch(0.600 0.085 132)",
        "oklch(0.555 0.115 42)",
        "oklch(0.380 0.060 236)",
      ] as [string, string, string, string, string],
    },
    dark: {
      bg: "oklch(0.125 0.012 128)",
      fg: "oklch(0.910 0.010 112)",
      card: "oklch(0.158 0.012 128)",
      popover: "oklch(0.175 0.012 128)",
      primary: "oklch(0.770 0.078 144)",
      primaryFg: "oklch(0.125 0.012 128)",
      muted: "oklch(0.210 0.014 128)",
      mutedFg: "oklch(0.630 0.014 112)",
      accent: "oklch(0.260 0.052 120)",
      border: "oklch(0.320 0.014 128)",
      sidebar: "oklch(0.102 0.012 128)",
      sidebarAccent: "oklch(0.195 0.014 128)",
    },
  },
  mist: {
    preview: { light: "oklch(0.330 0.050 172)", dark: "oklch(0.760 0.060 172)" },
    light: {
      bg: "oklch(0.977 0.006 150)",
      fg: "oklch(0.160 0.008 170)",
      card: "oklch(0.990 0.005 150)",
      popover: "oklch(0.996 0.004 150)",
      primary: "oklch(0.330 0.050 172)",
      primaryFg: "oklch(0.980 0.006 150)",
      muted: "oklch(0.930 0.008 150)",
      mutedFg: "oklch(0.440 0.012 170)",
      accent: "oklch(0.880 0.026 156)",
      border: "oklch(0.790 0.008 150)",
      sidebar: "oklch(0.952 0.007 150)",
      sidebarAccent: "oklch(0.910 0.010 156)",
    },
    dark: {
      bg: "oklch(0.128 0.010 170)",
      fg: "oklch(0.920 0.006 150)",
      card: "oklch(0.160 0.010 170)",
      popover: "oklch(0.176 0.010 170)",
      primary: "oklch(0.760 0.060 172)",
      primaryFg: "oklch(0.128 0.010 170)",
      muted: "oklch(0.215 0.010 170)",
      mutedFg: "oklch(0.635 0.008 150)",
      accent: "oklch(0.260 0.032 156)",
      border: "oklch(0.320 0.010 170)",
      sidebar: "oklch(0.104 0.010 170)",
      sidebarAccent: "oklch(0.195 0.010 170)",
    },
  },
}

const sourceWorkspaceDensity = {
  compact: {
    lineHeight: "1.56",
    sectionGap: "2.05rem",
    padding: "0.95rem",
    width: "58rem",
    fontSize: "0.955rem",
    headingWeight: "780",
    h2Weight: "760",
  },
  balanced: {
    lineHeight: "1.64",
    sectionGap: "2.35rem",
    padding: "1.1rem",
    width: "54rem",
    fontSize: "0.985rem",
    headingWeight: "800",
    h2Weight: "780",
  },
  roomy: {
    lineHeight: "1.74",
    sectionGap: "2.8rem",
    padding: "1.3rem",
    width: "50rem",
    fontSize: "1rem",
    headingWeight: "820",
    h2Weight: "800",
  },
}

const sourceWorkspaceCode = {
  panel: {
    "--folio-code-bg": "color-mix(in oklch, var(--muted) 88%, var(--background))",
    "--folio-code-foreground": "inherit",
    "--folio-code-border-radius": "0.5rem",
    "--folio-code-shadow": "none",
  },
  window: {
    "--folio-code-bg": "var(--card)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border-radius": "0.7rem",
    "--folio-code-shadow": "0 18px 48px -38px oklch(0.155 0.007 82 / 0.42)",
  },
  plate: {
    "--folio-code-bg": "var(--background)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border-radius": "0.25rem",
    "--folio-code-shadow": "none",
  },
} satisfies Record<string, Partial<ThemeStyle>>

const sourceWorkspaceFrames = {
  fine: {
    cardBorder: "1px",
    cardShadow: "0 18px 52px -44px oklch(0.155 0.007 82 / 0.32)",
    cardHoverShadow: "0 0 0 1px color-mix(in oklch, var(--border) 72%, var(--background))",
    codeBorder: "1px solid color-mix(in oklch, var(--border) 72%, var(--background))",
    h2Border: "1px solid color-mix(in oklch, var(--border) 70%, var(--background))",
    shellBorder: "1px solid color-mix(in oklch, var(--border) 72%, var(--background))",
    shellShadow: "0 18px 52px -48px oklch(0.155 0.007 82 / 0.34)",
  },
  structured: {
    cardBorder: "1px",
    cardShadow: "0 24px 72px -54px oklch(0.155 0.007 82 / 0.55)",
    cardHoverShadow: "0 18px 48px -36px oklch(0.155 0.007 82 / 0.36)",
    codeBorder: "1px solid var(--border)",
    h2Border: "1px solid var(--border)",
    shellBorder: "1px solid var(--border)",
    shellShadow: "0 24px 72px -54px oklch(0.155 0.007 82 / 0.55)",
  },
  ruled: {
    cardBorder: "1.5px",
    cardShadow: "0 22px 60px -50px oklch(0.155 0.007 82 / 0.48)",
    cardHoverShadow: "0 0 0 1.5px var(--border), 0 18px 48px -38px oklch(0.155 0.007 82 / 0.30)",
    codeBorder: "1.5px solid var(--border)",
    h2Border: "1.5px solid var(--border)",
    shellBorder: "1.5px solid var(--border)",
    shellShadow: "0 22px 60px -50px oklch(0.155 0.007 82 / 0.48)",
  },
}

function resolveSourceWorkspace(options: PresetOptionValues): ResolvedPresetTheme {
  const surface = choose(sourceWorkspaceSurfaces, options.surface, "paper")
  const density = choose(sourceWorkspaceDensity, options.density, "balanced")
  const code = choose(sourceWorkspaceCode, options.code, "panel")
  const frame = choose(sourceWorkspaceFrames, options.frame, "structured")

  return {
    preview: surface.preview,
    radius: "0.5rem",
    style: makeStyle({
      "--folio-heading-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-heading-weight": density.headingWeight,
      "--folio-body-line-height": density.lineHeight,
      "--folio-font-size-base": density.fontSize,
      "--folio-card-shadow": frame.cardShadow,
      "--folio-card-border-width": frame.cardBorder,
      "--folio-card-padding": density.padding,
      "--folio-card-hover-shadow": frame.cardHoverShadow,
      "--folio-code-border": frame.codeBorder,
      "--folio-h2-border": frame.h2Border,
      "--folio-h2-transform": "none",
      "--folio-h2-weight": density.h2Weight,
      "--folio-link-decoration": "none",
      "--folio-section-gap": density.sectionGap,
      "--folio-content-max-width": density.width,
      "--folio-workspace-shell-padding": "22px",
      "--folio-workspace-shell-border": frame.shellBorder,
      "--folio-workspace-shell-shadow": frame.shellShadow,
      "--folio-workspace-shell-background": "color-mix(in oklch, var(--muted) 42%, var(--background))",
      "--folio-workspace-shell-surface": "color-mix(in oklch, var(--card) 96%, var(--background))",
      "--folio-workspace-shell-topbar": "color-mix(in oklch, var(--muted) 66%, var(--background))",
      ...code,
    }),
    light: makeVars(surface.light),
    dark: makeVars(surface.dark),
  }
}

const organicEditorialScale = {
  poster: {
    lineHeight: "1.52",
    sectionGap: "4.5rem",
    padding: "1.05rem",
    width: "61rem",
    fontSize: "1rem",
    headingWeight: "220",
    h2Weight: "300",
  },
  essay: {
    lineHeight: "1.64",
    sectionGap: "3.5rem",
    padding: "1.15rem",
    width: "56rem",
    fontSize: "1rem",
    headingWeight: "420",
    h2Weight: "460",
  },
  compact: {
    lineHeight: "1.56",
    sectionGap: "2.6rem",
    padding: "0.95rem",
    width: "54rem",
    fontSize: "0.965rem",
    headingWeight: "420",
    h2Weight: "520",
  },
}

const organicEditorialImage = {
  cobalt: {
    preview: { light: "oklch(0.360 0.185 264)", dark: "oklch(0.740 0.140 264)" },
    primary: "oklch(0.360 0.185 264)",
    darkPrimary: "oklch(0.740 0.140 264)",
    accent: "oklch(0.900 0.046 264)",
    darkAccent: "oklch(0.245 0.080 264)",
  },
  ink: {
    preview: { light: "oklch(0.165 0.010 260)", dark: "oklch(0.900 0.008 260)" },
    primary: "oklch(0.165 0.010 260)",
    darkPrimary: "oklch(0.900 0.008 260)",
    accent: "oklch(0.930 0.006 260)",
    darkAccent: "oklch(0.235 0.010 260)",
  },
  mineral: {
    preview: { light: "oklch(0.460 0.090 194)", dark: "oklch(0.760 0.078 194)" },
    primary: "oklch(0.460 0.090 194)",
    darkPrimary: "oklch(0.760 0.078 194)",
    accent: "oklch(0.900 0.036 194)",
    darkAccent: "oklch(0.245 0.052 194)",
  },
}

const organicEditorialCode = {
  quiet: {
    "--folio-code-bg": "var(--muted)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid var(--border)",
    "--folio-code-border-radius": "0.5rem",
  },
  gallery: {
    "--folio-code-bg": "var(--background)",
    "--folio-code-foreground": "inherit",
    "--folio-code-border": "1px solid var(--foreground)",
    "--folio-code-border-radius": "0.25rem",
  },
} satisfies Record<string, Partial<ThemeStyle>>

function resolveOrganicEditorial(options: PresetOptionValues): ResolvedPresetTheme {
  const scale = choose(organicEditorialScale, options.scale, "poster")
  const image = choose(organicEditorialImage, options.image, "cobalt")
  const code = choose(organicEditorialCode, options.code, "quiet")

  return {
    preview: image.preview,
    radius: "0.5rem",
    style: makeStyle({
      "--folio-heading-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-heading-weight": scale.headingWeight,
      "--folio-body-line-height": scale.lineHeight,
      "--folio-font-size-base": scale.fontSize,
      "--folio-card-shadow": "none",
      "--folio-card-border-width": "1px",
      "--folio-card-padding": scale.padding,
      "--folio-card-hover-shadow": "0 0 0 1px var(--foreground)",
      "--folio-h2-border": "none",
      "--folio-h2-transform": "uppercase",
      "--folio-h2-weight": scale.h2Weight,
      "--folio-h2-letter-spacing": "0",
      "--folio-link-decoration": "none",
      "--folio-section-gap": scale.sectionGap,
      "--folio-content-max-width": scale.width,
      ...code,
    }),
    light: makeVars({
      bg: "oklch(0.997 0.001 260)",
      fg: "oklch(0.115 0.006 260)",
      card: "oklch(0.998 0.001 260)",
      popover: "oklch(0.999 0.001 260)",
      primary: image.primary,
      primaryFg: "oklch(0.997 0.001 260)",
      muted: "oklch(0.948 0.004 260)",
      mutedFg: "oklch(0.430 0.008 260)",
      accent: image.accent,
      border: "oklch(0.860 0.004 260)",
      sidebar: "oklch(0.972 0.003 260)",
      sidebarAccent: "oklch(0.938 0.006 260)",
      charts: [
        image.primary,
        "oklch(0.240 0.010 260)",
        "oklch(0.520 0.090 194)",
        "oklch(0.620 0.090 64)",
        "oklch(0.470 0.060 310)",
      ],
    }),
    dark: makeVars({
      bg: "oklch(0.115 0.006 260)",
      fg: "oklch(0.930 0.004 260)",
      card: "oklch(0.150 0.006 260)",
      popover: "oklch(0.168 0.006 260)",
      primary: image.darkPrimary,
      primaryFg: "oklch(0.115 0.006 260)",
      muted: "oklch(0.210 0.006 260)",
      mutedFg: "oklch(0.650 0.006 260)",
      accent: image.darkAccent,
      border: "oklch(0.300 0.006 260)",
      sidebar: "oklch(0.095 0.006 260)",
      sidebarAccent: "oklch(0.190 0.006 260)",
      charts: [
        image.darkPrimary,
        "oklch(0.800 0.006 260)",
        "oklch(0.720 0.090 194)",
        "oklch(0.760 0.090 64)",
        "oklch(0.690 0.060 310)",
      ],
    }),
  }
}

export const atlasPreset: ThemePreset = {
  id: "atlas",
  name: "Atlas",
  description: "Classic reference docs with paper rhythm and sharp examples",
  scene: "A library author reviews generated API docs in daylight, moving between prose, index pages, and code examples.",
  preview: { light: "oklch(0.27 0.014 82)", dark: "oklch(0.90 0.008 82)" },
  defaultOptions: { paper: "wove", binding: "thread", code: "ink" },
  defaultRadiusIndex: 0,
  defaultCustomization: { fontId: "folio", colorId: "ink" },
  controls: [
    {
      id: "paper",
      label: "Surface",
      description: "Surface temperature and page contrast.",
      options: [
        { label: "Wove", value: "wove" },
        { label: "Cotton", value: "cotton" },
        { label: "Parchment", value: "parchment" },
        { label: "Canvas", value: "canvas" },
      ],
    },
    {
      id: "binding",
      label: "Reading rhythm",
      description: "Spacing and hierarchy for scanning.",
      options: [
        { label: "Classic", value: "thread" },
        { label: "Balanced", value: "case" },
        { label: "Dense index", value: "index" },
        { label: "API reference", value: "reference" },
      ],
    },
    {
      id: "code",
      label: "Code blocks",
      description: "How examples separate from prose.",
      options: [
        { label: "Soft ink", value: "ink" },
        { label: "Soft panel", value: "paper" },
        { label: "Ruled plate", value: "plate" },
        { label: "Rounded panel", value: "panel" },
      ],
    },
  ],
  resolve: resolveFolio,
}

export const beaconPreset: ThemePreset = {
  id: "beacon",
  name: "Beacon",
  description: "Product docs shell with endpoint cards and compact API workflows",
  scene: "A prompt platform team scans versioned resources, endpoint cards, side navigation, and dark request examples in a product documentation workbench.",
  preview: { light: "oklch(0.470 0.120 258)", dark: "oklch(0.780 0.080 258)" },
  defaultOptions: { surface: "studio", density: "workbench", code: "terminal" },
  defaultRadiusIndex: 3,
  defaultCustomization: { fontId: "sans", colorId: "ink" },
  controls: [
    {
      id: "surface",
      label: "Product surface",
      description: "Navigation, sidebar, and card contrast.",
      options: [
        { label: "Studio", value: "studio" },
        { label: "Console", value: "console" },
      ],
    },
    {
      id: "density",
      label: "Workflow density",
      description: "How much API workflow content fits above the fold.",
      options: [
        { label: "Docs", value: "docs" },
        { label: "Workbench", value: "workbench" },
      ],
    },
    {
      id: "code",
      label: "Code blocks",
      description: "Request and response example treatment.",
      options: [
        { label: "Soft terminal", value: "terminal" },
        { label: "Panel", value: "panel" },
      ],
    },
  ],
  resolve: resolveBeacon,
}

const sourceWorkspaceControls: ThemePreset["controls"] = [
  {
    id: "density",
    label: "Docs density",
    description: "Spacing for generated guides and source examples.",
    options: [
      { label: "Compact", value: "compact" },
      { label: "Balanced", value: "balanced" },
      { label: "Roomy", value: "roomy" },
    ],
  },
  {
    id: "code",
    label: "Code frame",
    description: "How source snippets sit inside the workspace.",
    options: [
      { label: "Panel", value: "panel" },
      { label: "Window", value: "window" },
      { label: "Plate", value: "plate" },
    ],
  },
  {
    id: "frame",
    label: "Borders",
    description: "How visible the workspace rules and example outlines feel.",
    options: [
      { label: "Fine", value: "fine" },
      { label: "Structured", value: "structured" },
      { label: "Ruled", value: "ruled" },
    ],
  },
]

export const workshopPreset: ThemePreset = {
  id: "workshop",
  name: "Workshop",
  description: "Warm generated-site workspace with botanical accents",
  scene: "A maintainer previews generated documentation beside the source tree in a bright workspace before publishing.",
  preview: { light: "oklch(0.315 0.050 145)", dark: "oklch(0.760 0.070 145)" },
  defaultOptions: { surface: "paper", density: "balanced", code: "panel", frame: "structured" },
  defaultRadiusIndex: 2,
  defaultCustomization: { fontId: "sans", colorId: "ink" },
  controls: sourceWorkspaceControls,
  resolve: resolveSourceWorkspace,
}

export const canopyPreset: ThemePreset = {
  id: "canopy",
  name: "Canopy",
  description: "Compact green workspace for examples and generated guides",
  scene: "A docs author scans simple examples, generated pages, and source snippets in a calm green-tinted workspace.",
  preview: { light: "oklch(0.300 0.060 144)", dark: "oklch(0.770 0.078 144)" },
  defaultOptions: { surface: "moss", density: "compact", code: "panel", frame: "ruled" },
  defaultRadiusIndex: 2,
  defaultCustomization: { fontId: "sans", colorId: "ink" },
  controls: sourceWorkspaceControls,
  resolve: resolveSourceWorkspace,
}

export const ledgerPreset: ThemePreset = {
  id: "ledger",
  name: "Ledger",
  description: "Register pages, dense rules, API tables",
  scene: "A maintainer scans parameter tables and changelog entries on a wide monitor during a release review.",
  preview: { light: "oklch(0.36 0.038 154)", dark: "oklch(0.76 0.050 154)" },
  defaultOptions: { density: "balanced", rules: "fine" },
  defaultRadiusIndex: 1,
  defaultCustomization: { fontId: "sans", colorId: "laurel" },
  controls: [
    {
      id: "density",
      label: "Density",
      options: [
        { label: "Compact", value: "compact" },
        { label: "Balanced", value: "balanced" },
        { label: "Roomy", value: "roomy" },
      ],
    },
    {
      id: "rules",
      label: "Rules",
      options: [
        { label: "Fine", value: "fine" },
        { label: "Ruled", value: "ruled" },
      ],
    },
  ],
  resolve: resolveLedger,
}

export const proofPreset: ThemePreset = {
  id: "proof",
  name: "Proof",
  description: "Printed manual, hard hierarchy",
  scene: "A developer reads a generated manual as if it were a precise printed reference beside an editor.",
  preview: { light: "oklch(0.165 0.005 78)", dark: "oklch(0.910 0.005 78)" },
  defaultOptions: { ink: "graphite", impression: "clean" },
  defaultRadiusIndex: 0,
  defaultCustomization: { fontId: "folio", colorId: "copper" },
  controls: [
    {
      id: "ink",
      label: "Ink",
      options: [
        { label: "Graphite", value: "graphite" },
        { label: "Black", value: "black" },
      ],
    },
    {
      id: "impression",
      label: "Impression",
      options: [
        { label: "Clean", value: "clean" },
        { label: "Heavy", value: "heavy" },
      ],
    },
  ],
  resolve: resolvePress,
}

export const stacksPreset: ThemePreset = {
  id: "stacks",
  name: "Stacks",
  description: "Catalog calm, library ordering",
  scene: "A reader follows long-form guides from a quiet catalog interface with stable navigation and soft labels.",
  preview: { light: "oklch(0.370 0.055 206)", dark: "oklch(0.720 0.060 206)" },
  defaultOptions: { tone: "catalog", reading: "standard" },
  defaultRadiusIndex: 1,
  defaultCustomization: { fontId: "serif", colorId: "indigo" },
  controls: [
    {
      id: "tone",
      label: "Catalog tone",
      options: [
        { label: "Slate", value: "slate" },
        { label: "Catalog", value: "catalog" },
        { label: "Sepia", value: "sepia" },
      ],
    },
    {
      id: "reading",
      label: "Reading",
      options: [
        { label: "Standard", value: "standard" },
        { label: "Spacious", value: "spacious" },
      ],
    },
  ],
  resolve: resolveArchive,
}

export const draftlinePreset: ThemePreset = {
  id: "draftline",
  name: "Draftline",
  description: "Working document, pencil rules",
  scene: "An author edits docs before release, checking examples and notes in a low-friction working copy.",
  preview: { light: "oklch(0.340 0.010 88)", dark: "oklch(0.820 0.006 88)" },
  defaultOptions: { pencil: "soft", marks: "quiet" },
  defaultRadiusIndex: 1,
  defaultCustomization: { fontId: "sans", colorId: "ink" },
  controls: [
    {
      id: "pencil",
      label: "Pencil",
      options: [
        { label: "Soft", value: "soft" },
        { label: "Firm", value: "firm" },
      ],
    },
    {
      id: "marks",
      label: "Marks",
      options: [
        { label: "Quiet", value: "quiet" },
        { label: "Visible", value: "visible" },
      ],
    },
  ],
  resolve: resolveDraft,
}

export const aperturePreset: ThemePreset = {
  id: "aperture",
  name: "Aperture",
  description: "Neutral developer docs with compact spacing and rounded code panels",
  scene: "A platform engineer reads model, SDK, and API notes in a restrained developer documentation surface.",
  preview: { light: "oklch(0.180 0.006 160)", dark: "oklch(0.930 0.004 160)" },
  defaultOptions: { paper: "canvas", binding: "reference", code: "panel" },
  defaultRadiusIndex: 3,
  defaultCustomization: { fontId: "sans", colorId: "ink" },
  controls: atlasPreset.controls,
  resolve: resolveFolio,
}

export const organicEditorialPreset: ThemePreset = {
  id: "organic-editorial",
  name: "Organic Editorial",
  description: "Poster-scale typography with cobalt organic image language",
  scene: "A training or launch page opens with severe white space, oversized type, and abstract cobalt imagery before moving into structured technical content.",
  preview: { light: "oklch(0.360 0.185 264)", dark: "oklch(0.740 0.140 264)" },
  defaultOptions: { scale: "poster", image: "cobalt", code: "quiet" },
  defaultRadiusIndex: 2,
  defaultCustomization: { fontId: "sans", colorId: "ink" },
  controls: [
    {
      id: "scale",
      label: "Editorial scale",
      description: "How much campaign spacing the docs surface keeps.",
      options: [
        { label: "Poster", value: "poster" },
        { label: "Essay", value: "essay" },
        { label: "Compact", value: "compact" },
      ],
    },
    {
      id: "image",
      label: "Image language",
      description: "Accent direction for abstract editorial imagery.",
      options: [
        { label: "Cobalt", value: "cobalt" },
        { label: "Ink", value: "ink" },
        { label: "Mineral", value: "mineral" },
      ],
    },
    {
      id: "code",
      label: "Code blocks",
      description: "How examples sit inside the editorial surface.",
      options: [
        { label: "Quiet", value: "quiet" },
        { label: "Gallery", value: "gallery" },
      ],
    },
  ],
  resolve: resolveOrganicEditorial,
}

export const carbonPreset: ThemePreset = {
  id: "carbon",
  name: "Carbon",
  description: "Monochrome, hard technical copy",
  scene: "A power user wants an austere docs surface where code blocks and headings carry nearly all hierarchy.",
  preview: { light: "oklch(0.160 0.008 70)", dark: "oklch(0.920 0.006 70)" },
  defaultOptions: { contrast: "tempered", code: "block" },
  defaultRadiusIndex: 0,
  defaultCustomization: { fontId: "mono", colorId: "ink" },
  controls: [
    {
      id: "contrast",
      label: "Contrast",
      options: [
        { label: "Tempered", value: "tempered" },
        { label: "Stark", value: "stark" },
      ],
    },
    {
      id: "code",
      label: "Code",
      options: [
        { label: "Soft block", value: "block" },
        { label: "Outline", value: "outline" },
      ],
    },
  ],
  resolve: resolveCarbon,
}

const builtinPresets: ThemePreset[] = [
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
]

// Register builtins first and the project preset last: registerPreset is
// last-wins, so a project preset that reuses a builtin id replaces the builtin
// instead of being silently overwritten by it. Builtins get their display
// groups from the registerGroup calls below.
builtinPresets.forEach((preset) => registerPreset(preset))
if (projectThemePreset) {
  registerPreset(projectThemePreset, "project")
}

// Register preset groups. Ordering relative to registerPreset does not
// matter: registerPreset creates placeholder groups that registerGroup
// merges into (label plus union of preset ids).
registerGroup("project", "Project", projectThemePreset ? [projectThemePreset.id] : [])
registerGroup("expressive", "Expressive", ["organic-editorial", "carbon"])
registerGroup("workspace", "Workspace", ["workshop", "canopy"])
registerGroup("product-docs", "Product Docs", ["beacon", "aperture", "ledger"])
registerGroup("reference", "Reference", ["atlas", "stacks", "draftline", "proof"])

export const presets: ThemePreset[] = getPresets()
