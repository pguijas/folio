"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { useTheme } from "next-themes"
import { HugeiconsIcon } from "@hugeicons/react"
import {
  ArrowDown01Icon,
  ComputerIcon,
  Moon02Icon,
  Sun03Icon,
} from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"
import { projectThemeDefaultConfig } from "@/theme/project-theme"
import { presets } from "@/theme/presets"
import { getGroups, groupPresetsForDisplay } from "@/theme/preset-registry"
import { themeRadiusScale } from "@/theme/theme-contract.generated"
import {
  type PresetOptionValues,
  type ResolvedPresetTheme,
  type ThemePreset,
  type ThemeStyle,
  type ThemeVars,
  buildBootstrapPresets,
  normalizePresetOptions,
  resolvePresetTheme,
} from "@/theme/preset-types"

// Radius values come from the generated theme contract so the TypeScript
// scale can never drift from the Python one; only the labels live here.
const radiusLabels = ["None", "Sm", "Md", "Lg", "Full"]
const radiusOptions: Array<{ label: string; value: string }> = themeRadiusScale.map(
  (value, index) => ({ label: radiusLabels[index] ?? value, value })
)

const modeOptions = [
  { id: "light", label: "Light", icon: Sun03Icon },
  { id: "dark", label: "Dark", icon: Moon02Icon },
  { id: "system", label: "System", icon: ComputerIcon },
] as const

type ThemeMode = (typeof modeOptions)[number]["id"]

const presetGroups = getGroups()

const fontOptions = [
  {
    id: "folio",
    label: "Editorial",
    description: "Serif headings, steady sans body",
    sample: "Aa",
    style: {
      "--folio-heading-font-family": "Georgia, \"Times New Roman\", ui-serif, serif",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
    },
  },
  {
    id: "sans",
    label: "System sans",
    description: "Clean UI typography",
    sample: "Ag",
    style: {
      "--folio-heading-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
    },
  },
  {
    id: "geist",
    label: "Geist",
    description: "p2pfl web services typography",
    sample: "Gg",
    style: {
      "--folio-heading-font-family": "var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-body-font-family": "var(--font-geist-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-code-font-family": "var(--font-geist-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
    },
  },
  {
    id: "serif",
    label: "Book serif",
    description: "Bookish long-form reading",
    sample: "St",
    style: {
      "--folio-heading-font-family": "Georgia, \"Times New Roman\", ui-serif, serif",
      "--folio-body-font-family": "Georgia, \"Times New Roman\", ui-serif, serif",
      "--folio-code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
    },
  },
  {
    id: "mono",
    label: "Reference mono",
    description: "Monospaced API scanning",
    sample: "01",
    style: {
      "--folio-heading-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
      "--folio-body-font-family": "var(--font-sans), ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif",
      "--folio-code-font-family": "var(--font-mono), ui-monospace, SFMono-Regular, \"SF Mono\", Menlo, Consolas, monospace",
    },
  },
] satisfies Array<{
  id: string
  label: string
  description: string
  sample: string
  style: Pick<ResolvedPresetTheme["style"], "--folio-heading-font-family" | "--folio-body-font-family" | "--folio-code-font-family">
}>

const colorOptions = [
  {
    id: "ink",
    label: "Theme ink",
    description: "Use the preset color",
    preview: { light: "oklch(0.155 0.007 82)", dark: "oklch(0.920 0.007 82)" },
    light: {},
    dark: {},
  },
  {
    id: "laurel",
    label: "Laurel",
    description: "Botanical green accent",
    preview: { light: "oklch(0.410 0.095 146)", dark: "oklch(0.770 0.105 146)" },
    light: {
      "--primary": "oklch(0.410 0.095 146)",
      "--primary-foreground": "oklch(0.980 0.006 120)",
      "--ring": "oklch(0.410 0.095 146)",
      "--accent": "oklch(0.900 0.030 146)",
      "--accent-foreground": "oklch(0.155 0.007 82)",
      "--sidebar-primary": "oklch(0.410 0.095 146)",
      "--sidebar-primary-foreground": "oklch(0.980 0.006 120)",
      "--sidebar-ring": "oklch(0.410 0.095 146)",
      "--chart-1": "oklch(0.410 0.095 146)",
    },
    dark: {
      "--primary": "oklch(0.770 0.105 146)",
      "--primary-foreground": "oklch(0.120 0.018 146)",
      "--ring": "oklch(0.770 0.105 146)",
      "--accent": "oklch(0.260 0.045 146)",
      "--accent-foreground": "oklch(0.930 0.008 146)",
      "--sidebar-primary": "oklch(0.770 0.105 146)",
      "--sidebar-primary-foreground": "oklch(0.120 0.018 146)",
      "--sidebar-ring": "oklch(0.770 0.105 146)",
      "--chart-1": "oklch(0.770 0.105 146)",
    },
  },
  {
    id: "indigo",
    label: "Indigo",
    description: "Cool technical accent",
    preview: { light: "oklch(0.420 0.095 268)", dark: "oklch(0.760 0.090 268)" },
    light: {
      "--primary": "oklch(0.420 0.095 268)",
      "--primary-foreground": "oklch(0.975 0.006 268)",
      "--ring": "oklch(0.420 0.095 268)",
      "--accent": "oklch(0.900 0.028 268)",
      "--accent-foreground": "oklch(0.150 0.010 268)",
      "--sidebar-primary": "oklch(0.420 0.095 268)",
      "--sidebar-primary-foreground": "oklch(0.975 0.006 268)",
      "--sidebar-ring": "oklch(0.420 0.095 268)",
      "--chart-1": "oklch(0.420 0.095 268)",
    },
    dark: {
      "--primary": "oklch(0.760 0.090 268)",
      "--primary-foreground": "oklch(0.115 0.014 268)",
      "--ring": "oklch(0.760 0.090 268)",
      "--accent": "oklch(0.260 0.045 268)",
      "--accent-foreground": "oklch(0.920 0.008 268)",
      "--sidebar-primary": "oklch(0.760 0.090 268)",
      "--sidebar-primary-foreground": "oklch(0.115 0.014 268)",
      "--sidebar-ring": "oklch(0.760 0.090 268)",
      "--chart-1": "oklch(0.760 0.090 268)",
    },
  },
  {
    id: "copper",
    label: "Copper",
    description: "Warm editorial accent",
    preview: { light: "oklch(0.500 0.105 54)", dark: "oklch(0.780 0.100 54)" },
    light: {
      "--primary": "oklch(0.500 0.105 54)",
      "--primary-foreground": "oklch(0.985 0.010 54)",
      "--ring": "oklch(0.500 0.105 54)",
      "--accent": "oklch(0.900 0.040 54)",
      "--accent-foreground": "oklch(0.170 0.012 54)",
      "--sidebar-primary": "oklch(0.500 0.105 54)",
      "--sidebar-primary-foreground": "oklch(0.985 0.010 54)",
      "--sidebar-ring": "oklch(0.500 0.105 54)",
      "--chart-1": "oklch(0.500 0.105 54)",
    },
    dark: {
      "--primary": "oklch(0.780 0.100 54)",
      "--primary-foreground": "oklch(0.125 0.014 54)",
      "--ring": "oklch(0.780 0.100 54)",
      "--accent": "oklch(0.270 0.050 54)",
      "--accent-foreground": "oklch(0.930 0.010 54)",
      "--sidebar-primary": "oklch(0.780 0.100 54)",
      "--sidebar-primary-foreground": "oklch(0.125 0.014 54)",
      "--sidebar-ring": "oklch(0.780 0.100 54)",
      "--chart-1": "oklch(0.780 0.100 54)",
    },
  },
] satisfies Array<{
  id: string
  label: string
  description: string
  preview: { light: string; dark: string }
  light: Partial<ThemeVars>
  dark: Partial<ThemeVars>
}>

type StyleOption = {
  id: string
  label: string
  style: Partial<ThemeStyle>
}

type SurfaceColorOption = {
  id: string
  label: string
  preview: { light: string; dark: string }
  light: Partial<ThemeVars>
  dark: Partial<ThemeVars>
}

const surfaceColorOptions = [
  {
    id: "preset",
    label: "Preset",
    preview: { light: "oklch(0.155 0.007 82)", dark: "oklch(0.920 0.007 82)" },
    light: {},
    dark: {},
  },
  {
    id: "paper",
    label: "Paper",
    preview: { light: "oklch(0.966 0.008 82)", dark: "oklch(0.140 0.008 82)" },
    light: {
      "--background": "oklch(0.966 0.008 82)",
      "--foreground": "oklch(0.155 0.007 82)",
      "--card": "oklch(0.976 0.007 82)",
      "--popover": "oklch(0.982 0.006 82)",
      "--muted": "oklch(0.920 0.007 82)",
      "--muted-foreground": "oklch(0.420 0.007 82)",
      "--border": "oklch(0.740 0.007 82)",
      "--sidebar": "oklch(0.940 0.007 82)",
      "--sidebar-accent": "oklch(0.890 0.008 82)",
    },
    dark: {
      "--background": "oklch(0.140 0.008 82)",
      "--foreground": "oklch(0.925 0.007 82)",
      "--card": "oklch(0.170 0.008 82)",
      "--popover": "oklch(0.185 0.008 82)",
      "--muted": "oklch(0.225 0.008 82)",
      "--muted-foreground": "oklch(0.660 0.007 82)",
      "--border": "oklch(0.340 0.008 82)",
      "--sidebar": "oklch(0.115 0.008 82)",
      "--sidebar-accent": "oklch(0.205 0.010 82)",
    },
  },
  {
    id: "moss",
    label: "Moss",
    preview: { light: "oklch(0.958 0.014 112)", dark: "oklch(0.125 0.012 128)" },
    light: {
      "--background": "oklch(0.958 0.014 112)",
      "--foreground": "oklch(0.150 0.010 128)",
      "--card": "oklch(0.974 0.012 112)",
      "--popover": "oklch(0.982 0.010 112)",
      "--muted": "oklch(0.900 0.018 112)",
      "--muted-foreground": "oklch(0.410 0.020 128)",
      "--border": "oklch(0.720 0.018 112)",
      "--sidebar": "oklch(0.925 0.018 112)",
      "--sidebar-accent": "oklch(0.872 0.026 120)",
    },
    dark: {
      "--background": "oklch(0.125 0.012 128)",
      "--foreground": "oklch(0.910 0.010 112)",
      "--card": "oklch(0.158 0.012 128)",
      "--popover": "oklch(0.175 0.012 128)",
      "--muted": "oklch(0.210 0.014 128)",
      "--muted-foreground": "oklch(0.630 0.014 112)",
      "--border": "oklch(0.320 0.014 128)",
      "--sidebar": "oklch(0.102 0.012 128)",
      "--sidebar-accent": "oklch(0.195 0.014 128)",
    },
  },
  {
    id: "mist",
    label: "Mist",
    preview: { light: "oklch(0.977 0.006 150)", dark: "oklch(0.128 0.010 170)" },
    light: {
      "--background": "oklch(0.977 0.006 150)",
      "--foreground": "oklch(0.160 0.008 170)",
      "--card": "oklch(0.990 0.005 150)",
      "--popover": "oklch(0.996 0.004 150)",
      "--muted": "oklch(0.930 0.008 150)",
      "--muted-foreground": "oklch(0.440 0.012 170)",
      "--border": "oklch(0.790 0.008 150)",
      "--sidebar": "oklch(0.952 0.007 150)",
      "--sidebar-accent": "oklch(0.910 0.010 156)",
    },
    dark: {
      "--background": "oklch(0.128 0.010 170)",
      "--foreground": "oklch(0.920 0.006 150)",
      "--card": "oklch(0.160 0.010 170)",
      "--popover": "oklch(0.176 0.010 170)",
      "--muted": "oklch(0.215 0.010 170)",
      "--muted-foreground": "oklch(0.635 0.008 150)",
      "--border": "oklch(0.320 0.010 170)",
      "--sidebar": "oklch(0.104 0.010 170)",
      "--sidebar-accent": "oklch(0.195 0.010 170)",
    },
  },
] satisfies SurfaceColorOption[]

const shellPaddingOptions = [
  { id: "preset", label: "Preset", style: {} },
  { id: "flush", label: "Flush", style: { "--folio-workspace-shell-padding": "0px" } },
  { id: "frame", label: "Frame", style: { "--folio-workspace-shell-padding": "18px" } },
  { id: "gallery", label: "Gallery", style: { "--folio-workspace-shell-padding": "28px" } },
] satisfies StyleOption[]

const contentWidthOptions = [
  { id: "preset", label: "Preset", style: {} },
  { id: "focus", label: "Focus", style: { "--folio-content-max-width": "54rem" } },
  { id: "docs", label: "Docs", style: { "--folio-content-max-width": "62rem" } },
  { id: "wide", label: "Wide", style: { "--folio-content-max-width": "74rem" } },
] satisfies StyleOption[]

const rhythmOptions = [
  { id: "preset", label: "Preset", style: {} },
  {
    id: "compact",
    label: "Compact",
    style: {
      "--folio-font-size-base": "0.95rem",
      "--folio-body-line-height": "1.54",
      "--folio-section-gap": "2.4rem",
      "--folio-card-padding": "0.95rem",
    },
  },
  {
    id: "balanced",
    label: "Balanced",
    style: {
      "--folio-font-size-base": "1rem",
      "--folio-body-line-height": "1.62",
      "--folio-section-gap": "3.2rem",
      "--folio-card-padding": "1.2rem",
    },
  },
  {
    id: "roomy",
    label: "Roomy",
    style: {
      "--folio-font-size-base": "1.03rem",
      "--folio-body-line-height": "1.72",
      "--folio-section-gap": "4.1rem",
      "--folio-card-padding": "1.45rem",
    },
  },
] satisfies StyleOption[]

const borderOptions = [
  { id: "preset", label: "Preset", style: {} },
  {
    id: "fine",
    label: "Fine",
    style: {
      "--folio-card-border-width": "1px",
      "--folio-card-shadow": "none",
      "--folio-card-hover-shadow": "0 0 0 1px color-mix(in oklch, var(--border) 64%, var(--background))",
      "--folio-workspace-shell-border": "1px solid color-mix(in oklch, var(--border) 70%, var(--background))",
      "--folio-workspace-shell-shadow": "none",
    },
  },
  {
    id: "structured",
    label: "Structured",
    style: {
      "--folio-card-border-width": "1px",
      "--folio-card-shadow": "0 18px 54px -48px var(--foreground)",
      "--folio-card-hover-shadow": "0 16px 42px -34px var(--foreground)",
      "--folio-workspace-shell-border": "1px solid var(--border)",
      "--folio-workspace-shell-shadow": "0 22px 70px -58px var(--foreground)",
    },
  },
  {
    id: "ruled",
    label: "Ruled",
    style: {
      "--folio-card-border-width": "1.5px",
      "--folio-card-shadow": "0 0 0 1px var(--border)",
      "--folio-card-hover-shadow": "0 0 0 1.5px var(--border), 0 18px 48px -38px var(--foreground)",
      "--folio-workspace-shell-border": "1.5px solid var(--border)",
      "--folio-workspace-shell-shadow": "0 0 0 1px var(--border)",
    },
  },
] satisfies StyleOption[]

const codeTreatmentOptions = [
  { id: "preset", label: "Preset", style: {} },
  {
    id: "soft",
    label: "Soft",
    style: {
      "--folio-code-bg": "color-mix(in oklch, var(--muted) 86%, var(--background))",
      "--folio-code-foreground": "inherit",
      "--folio-code-border": "1px solid color-mix(in oklch, var(--border) 72%, var(--background))",
      "--folio-code-border-radius": "0.5rem",
      "--folio-code-shadow": "none",
    },
  },
  {
    id: "framed",
    label: "Framed",
    style: {
      "--folio-code-bg": "var(--background)",
      "--folio-code-foreground": "inherit",
      "--folio-code-border": "1px solid var(--border)",
      "--folio-code-border-radius": "0.35rem",
      "--folio-code-shadow": "0 16px 48px -42px var(--foreground)",
    },
  },
  {
    id: "plate",
    label: "Plate",
    style: {
      "--folio-code-bg": "color-mix(in oklch, var(--card) 72%, var(--muted))",
      "--folio-code-foreground": "inherit",
      "--folio-code-border": "1.5px solid var(--border)",
      "--folio-code-border-radius": "0.15rem",
      "--folio-code-shadow": "none",
    },
  },
  {
    id: "terminal",
    label: "Terminal",
    style: {
      "--folio-code-bg": "color-mix(in oklch, var(--card) 84%, var(--background))",
      "--folio-code-foreground": "inherit",
      "--folio-code-border": "1px solid var(--border)",
      "--folio-code-border-radius": "0.5rem",
      "--folio-code-shadow": "var(--shadow-sm, none)",
    },
  },
] satisfies StyleOption[]

interface ThemeCustomization {
  fontId: string
  colorId: string
  surfaceColorId: string
  shellPaddingId: string
  contentWidthId: string
  rhythmId: string
  borderId: string
  codeTreatmentId: string
}

interface ThemeConfig {
  presetId: string
  radiusIndex: number
  optionsByPreset: Record<string, PresetOptionValues>
  customization: ThemeCustomization
}

type LegacyThemeConfig = Partial<ThemeConfig> & {
  themeId?: string
  flavorId?: string
  optionsByFlavor?: Record<string, PresetOptionValues>
}

const DEFAULT_CUSTOMIZATION: ThemeCustomization = {
  fontId: "sans",
  colorId: "ink",
  surfaceColorId: "preset",
  shellPaddingId: "preset",
  contentWidthId: "preset",
  rhythmId: "preset",
  borderId: "preset",
  codeTreatmentId: "preset",
  ...(projectThemeDefaultConfig.customization ?? {}),
} as ThemeCustomization
const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__
const DEFAULT_CONFIG: ThemeConfig = {
  presetId: projectThemeDefaultConfig.presetId ?? configuredDefaultPresetId,
  radiusIndex: projectThemeDefaultConfig.radiusIndex ?? 2,
  optionsByPreset: projectThemeDefaultConfig.optionsByPreset ?? {},
  customization: DEFAULT_CUSTOMIZATION,
}
const STORAGE_KEY = `folio-theme:${DEFAULT_CONFIG.presetId}`
// Pre-namespacing storage key; migrated to STORAGE_KEY on first read.
const LEGACY_STORAGE_KEY = "folio-theme"
const SHELL_THEME_CSS = `
html {
  background: var(--folio-workspace-shell-topbar);
}

body {
  min-height: 100vh;
  padding: var(--folio-workspace-shell-padding);
  background: var(--folio-workspace-shell-background);
}

body > .nextra-navbar {
  top: var(--folio-workspace-shell-padding) !important;
  background: var(--folio-workspace-shell-topbar) !important;
}

body > .nextra-navbar .nextra-navbar-blur {
  border: var(--folio-workspace-shell-border);
  border-bottom: var(--folio-workspace-shell-topbar-border);
  background: var(--folio-workspace-shell-topbar) !important;
  -webkit-backdrop-filter: var(--folio-workspace-shell-topbar-blur) !important;
  backdrop-filter: var(--folio-workspace-shell-topbar-blur) !important;
}

.landing-shell {
  min-height: calc(100vh - (var(--folio-workspace-shell-padding) * 2));
  overflow: hidden;
  border: var(--folio-workspace-shell-border);
  background: var(--folio-workspace-shell-surface);
  box-shadow: var(--folio-workspace-shell-shadow);
}

.landing-navbar {
  top: var(--folio-workspace-shell-padding) !important;
  right: var(--folio-workspace-shell-padding);
  left: var(--folio-workspace-shell-padding);
  width: calc(100% - (var(--folio-workspace-shell-padding) * 2)) !important;
  border: var(--folio-workspace-shell-border);
  border-bottom: var(--folio-workspace-shell-topbar-border);
  background: var(--folio-workspace-shell-topbar) !important;
  -webkit-backdrop-filter: var(--folio-workspace-shell-topbar-blur) !important;
  backdrop-filter: var(--folio-workspace-shell-topbar-blur) !important;
}

body > div:has(> .nextra-sidebar) {
  overflow: clip;
  border-right: var(--folio-workspace-shell-border);
  border-bottom: var(--folio-workspace-shell-border);
  border-left: var(--folio-workspace-shell-border);
  background: var(--folio-workspace-shell-surface);
  box-shadow: var(--folio-workspace-shell-shadow);
}

.nextra-sidebar {
  top: calc(var(--nextra-navbar-height) + var(--folio-workspace-shell-padding)) !important;
  height: calc(100dvh - var(--nextra-navbar-height) - (var(--folio-workspace-shell-padding) * 2)) !important;
  z-index: 60 !important;
}

.nextra-toc > div {
  top: calc(var(--nextra-navbar-height) + var(--folio-workspace-shell-padding)) !important;
  max-height: calc(100dvh - var(--nextra-navbar-height) - (var(--folio-workspace-shell-padding) * 2)) !important;
}

details[data-theme-configurator] {
  isolation: isolate;
}

@media (max-width: 767px) {
  body > .nextra-navbar {
    top: 0 !important;
    margin-right: calc(var(--folio-workspace-shell-padding) * -1);
    margin-left: calc(var(--folio-workspace-shell-padding) * -1);
    width: calc(100% + (var(--folio-workspace-shell-padding) * 2)) !important;
  }

  .landing-navbar {
    top: 0 !important;
    right: 0;
    left: 0;
    width: 100% !important;
  }

  .nextra-sidebar,
  .nextra-toc > div {
    top: var(--nextra-navbar-height) !important;
  }

  .nextra-sidebar {
    height: calc(100dvh - var(--nextra-navbar-height) - var(--folio-workspace-shell-padding)) !important;
  }

  .nextra-toc > div {
    max-height: calc(100dvh - var(--nextra-navbar-height) - var(--folio-workspace-shell-padding)) !important;
  }
}
`
const LEGACY_PRESET_IDS: Record<string, string> = {
  "atelier": "atlas",
  "oxide": "proof",
  "signal": "ledger",
  "depth": "stacks",
  "flora": "draftline",
  "folio": "atlas",
  "reference": "atlas",
  "promptix": "beacon",
  "openai": "aperture",
  "press": "proof",
  "archive": "stacks",
  "draft": "draftline",
  "ledger": "ledger",
  "carbon": "carbon",
}

const DEFAULT_PRESET = presets.find((preset) => preset.id === DEFAULT_CONFIG.presetId) ?? presets[0]!

function getRadius(index: number) {
  return radiusOptions[index] ?? radiusOptions[DEFAULT_CONFIG.radiusIndex]
}

function getRadiusIndex(value: string, fallback = DEFAULT_CONFIG.radiusIndex) {
  const index = radiusOptions.findIndex((option) => option.value === value)
  return index >= 0 ? index : fallback
}

function normalizeThemeMode(value: string | undefined): ThemeMode {
  return modeOptions.some((option) => option.id === value) ? value as ThemeMode : "system"
}

function getFontOption(id: string | undefined) {
  return fontOptions.find((option) => option.id === id) ?? fontOptions[1]!
}

function getColorOption(id: string | undefined) {
  return colorOptions.find((option) => option.id === id) ?? colorOptions[0]!
}

function getSurfaceColorOption(id: string | undefined) {
  return surfaceColorOptions.find((option) => option.id === id) ?? surfaceColorOptions[0]!
}

function getShellPaddingOption(id: string | undefined) {
  return shellPaddingOptions.find((option) => option.id === id) ?? shellPaddingOptions[0]!
}

function getContentWidthOption(id: string | undefined) {
  return contentWidthOptions.find((option) => option.id === id) ?? contentWidthOptions[0]!
}

function getRhythmOption(id: string | undefined) {
  return rhythmOptions.find((option) => option.id === id) ?? rhythmOptions[0]!
}

function getBorderOption(id: string | undefined) {
  return borderOptions.find((option) => option.id === id) ?? borderOptions[0]!
}

function getCodeTreatmentOption(id: string | undefined) {
  return codeTreatmentOptions.find((option) => option.id === id) ?? codeTreatmentOptions[0]!
}

function normalizeCustomization(input: Partial<ThemeCustomization> = {}): ThemeCustomization {
  return {
    fontId: getFontOption(input.fontId).id,
    colorId: getColorOption(input.colorId).id,
    surfaceColorId: getSurfaceColorOption(input.surfaceColorId).id,
    shellPaddingId: getShellPaddingOption(input.shellPaddingId).id,
    contentWidthId: getContentWidthOption(input.contentWidthId).id,
    rhythmId: getRhythmOption(input.rhythmId).id,
    borderId: getBorderOption(input.borderId).id,
    codeTreatmentId: getCodeTreatmentOption(input.codeTreatmentId).id,
  }
}

function getCustomizationStyle(customization: ThemeCustomization): Partial<ThemeStyle> {
  return {
    ...getShellPaddingOption(customization.shellPaddingId).style,
    ...getContentWidthOption(customization.contentWidthId).style,
    ...getRhythmOption(customization.rhythmId).style,
    ...getBorderOption(customization.borderId).style,
    ...getCodeTreatmentOption(customization.codeTreatmentId).style,
  }
}

function normalizePresetId(id: string | undefined): string {
  if (!id || id === "custom") return DEFAULT_CONFIG.presetId
  return LEGACY_PRESET_IDS[id] ?? id
}

function getPreset(id: string | undefined): ThemePreset {
  const migratedId = normalizePresetId(id)
  return presets.find((preset) => preset.id === migratedId) ?? DEFAULT_PRESET
}

// Presets are deduped across groups (first group wins; the "project" group is
// registered first, so a project preset that reuses a builtin id only shows
// under Project). Presets that belong to no group render in a fallback group
// so presets registered through the extension API are never invisible. The
// logic lives in preset-registry.ts so it stays behaviorally testable.
const groupedPresets = groupPresetsForDisplay(presetGroups, presets)

function getPresetDefaults(preset: ThemePreset) {
  const radiusIndex = radiusOptions[preset.defaultRadiusIndex ?? DEFAULT_CONFIG.radiusIndex]
    ? preset.defaultRadiusIndex ?? DEFAULT_CONFIG.radiusIndex
    : DEFAULT_CONFIG.radiusIndex

  return {
    radiusIndex,
    customization: normalizeCustomization(preset.defaultCustomization ?? DEFAULT_CUSTOMIZATION),
  }
}

function getPresetOptions(config: ThemeConfig, presetId: string): PresetOptionValues {
  const preset = getPreset(presetId)
  return normalizePresetOptions(preset, config.optionsByPreset[preset.id])
}

function getRequestedPresetId(input: LegacyThemeConfig): string | undefined {
  if (input.presetId && input.presetId !== "custom") return input.presetId
  return input.flavorId ?? input.themeId ?? input.presetId
}

function getMigratedOptions(input: LegacyThemeConfig): Record<string, PresetOptionValues> {
  const optionsByPreset =
    input.optionsByPreset && typeof input.optionsByPreset === "object"
      ? { ...input.optionsByPreset }
      : {}
  const legacyOptions =
    input.optionsByFlavor && typeof input.optionsByFlavor === "object"
      ? input.optionsByFlavor
      : {}

  for (const [legacyId, options] of Object.entries(legacyOptions)) {
    const preset = getPreset(legacyId)
    if (!optionsByPreset[preset.id]) {
      optionsByPreset[preset.id] = options
    }
  }

  return optionsByPreset
}

function normalizeConfig(input: LegacyThemeConfig = {}): ThemeConfig {
  const requestedId = getRequestedPresetId(input)
  const preset = getPreset(requestedId === "custom" ? input.flavorId ?? input.themeId : requestedId)
  const defaults = getPresetDefaults(preset)
  const optionsByPreset = getMigratedOptions(input)
  const requestedRadiusIndex = Number.isInteger(input.radiusIndex)
    ? Number(input.radiusIndex)
    : defaults.radiusIndex

  if (!optionsByPreset[preset.id]) {
    optionsByPreset[preset.id] = normalizePresetOptions(preset)
  }

  return {
    presetId: preset.id,
    radiusIndex: radiusOptions[requestedRadiusIndex] ? requestedRadiusIndex : defaults.radiusIndex,
    optionsByPreset,
    customization: normalizeCustomization(input.customization ?? defaults.customization),
  }
}

function loadConfig(): ThemeConfig {
  if (typeof window === "undefined") return DEFAULT_CONFIG

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return normalizeConfig(JSON.parse(stored))
    }
    const legacy = localStorage.getItem(LEGACY_STORAGE_KEY)
    if (legacy) {
      const migrated = normalizeConfig(JSON.parse(legacy))
      localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated))
      localStorage.removeItem(LEGACY_STORAGE_KEY)
      return migrated
    }
  } catch {}

  return DEFAULT_CONFIG
}

function themeToCss(theme: ResolvedPresetTheme, radius: string, customization: ThemeCustomization) {
  const font = getFontOption(customization.fontId)
  const color = getColorOption(customization.colorId)
  const surface = getSurfaceColorOption(customization.surfaceColorId)
  const style = getCustomizationStyle(customization)
  const toVars = (vars: object) =>
    Object.entries(vars)
      .map(([key, value]) => `  ${key}: ${String(value)};`)
      .join("\n")

  return `
    :root {
${toVars(theme.light)}
${toVars(surface.light)}
${toVars(color.light)}
${toVars(theme.style)}
${toVars(style)}
${toVars(font.style)}
      --radius: ${radius};
    }
    .dark {
${toVars(theme.dark)}
${toVars(surface.dark)}
${toVars(color.dark)}
    }
${SHELL_THEME_CSS}
  `
}

function configToCss(config: ThemeConfig) {
  const normalized = normalizeConfig(config)
  const preset = getPreset(normalized.presetId)
  const options = getPresetOptions(normalized, preset.id)
  const theme = resolvePresetTheme(preset, options)
  const radius = getRadius(normalized.radiusIndex)

  return themeToCss(theme, radius.value, normalized.customization)
}

const DEFAULT_THEME_CSS = configToCss(DEFAULT_CONFIG)

function applyConfig(config: ThemeConfig) {

  const style = document.getElementById("theme-configurator-style") || (() => {
    const el = document.createElement("style")
    el.id = "theme-configurator-style"
    document.head.appendChild(el)
    return el
  })()

  style.textContent = configToCss(config)
}

// Combination-capped bootstrap payload; buildBootstrapPresets (preset-types.ts)
// embeds only the default resolution for presets whose option-combination
// count exceeds MAX_BOOTSTRAP_COMBINATIONS so the inline script stays small.
const BOOTSTRAP_PRESETS = buildBootstrapPresets(presets)

const BOOTSTRAP_FONT_OPTIONS = fontOptions.map((option) => ({
  id: option.id,
  style: option.style,
}))

const BOOTSTRAP_COLOR_OPTIONS = colorOptions.map((option) => ({
  id: option.id,
  light: option.light,
  dark: option.dark,
}))

const BOOTSTRAP_SURFACE_COLOR_OPTIONS = surfaceColorOptions.map((option) => ({
  id: option.id,
  light: option.light,
  dark: option.dark,
}))

const BOOTSTRAP_SHELL_PADDING_OPTIONS = shellPaddingOptions.map((option) => ({
  id: option.id,
  style: option.style,
}))

const BOOTSTRAP_CONTENT_WIDTH_OPTIONS = contentWidthOptions.map((option) => ({
  id: option.id,
  style: option.style,
}))

const BOOTSTRAP_RHYTHM_OPTIONS = rhythmOptions.map((option) => ({
  id: option.id,
  style: option.style,
}))

const BOOTSTRAP_BORDER_OPTIONS = borderOptions.map((option) => ({
  id: option.id,
  style: option.style,
}))

const BOOTSTRAP_CODE_TREATMENT_OPTIONS = codeTreatmentOptions.map((option) => ({
  id: option.id,
  style: option.style,
}))

const THEME_BOOTSTRAP_SCRIPT = `
(() => {
  try {
    const presets = ${JSON.stringify(BOOTSTRAP_PRESETS)};
    const radiusOptions = ${JSON.stringify(radiusOptions)};
    const fontOptions = ${JSON.stringify(BOOTSTRAP_FONT_OPTIONS)};
    const colorOptions = ${JSON.stringify(BOOTSTRAP_COLOR_OPTIONS)};
    const surfaceColorOptions = ${JSON.stringify(BOOTSTRAP_SURFACE_COLOR_OPTIONS)};
    const shellPaddingOptions = ${JSON.stringify(BOOTSTRAP_SHELL_PADDING_OPTIONS)};
    const contentWidthOptions = ${JSON.stringify(BOOTSTRAP_CONTENT_WIDTH_OPTIONS)};
    const rhythmOptions = ${JSON.stringify(BOOTSTRAP_RHYTHM_OPTIONS)};
    const borderOptions = ${JSON.stringify(BOOTSTRAP_BORDER_OPTIONS)};
    const codeTreatmentOptions = ${JSON.stringify(BOOTSTRAP_CODE_TREATMENT_OPTIONS)};
    const defaultConfig = ${JSON.stringify(DEFAULT_CONFIG)};
    const legacyPresetIds = ${JSON.stringify(LEGACY_PRESET_IDS)};
    const shellThemeCss = ${JSON.stringify(SHELL_THEME_CSS)};
    const toVars = (vars) => Object.entries(vars).map(([key, value]) => "  " + key + ": " + value + ";").join("\\n");
    const normalizePresetId = (id) => !id || id === "custom" ? defaultConfig.presetId : legacyPresetIds[id] || id;
    const getPreset = (id) => {
      const migratedId = normalizePresetId(id);
      return presets.find((item) => item.id === migratedId) || presets.find((item) => item.id === defaultConfig.presetId) || presets[0];
    };
    const getRadius = (index) => radiusOptions[index] || radiusOptions[defaultConfig.radiusIndex];
    const getFontOption = (id) => fontOptions.find((item) => item.id === id) || fontOptions.find((item) => item.id === defaultConfig.customization.fontId) || fontOptions[0];
    const getColorOption = (id) => colorOptions.find((item) => item.id === id) || colorOptions.find((item) => item.id === defaultConfig.customization.colorId) || colorOptions[0];
    const getSurfaceColorOption = (id) => surfaceColorOptions.find((item) => item.id === id) || surfaceColorOptions[0];
    const getShellPaddingOption = (id) => shellPaddingOptions.find((item) => item.id === id) || shellPaddingOptions[0];
    const getContentWidthOption = (id) => contentWidthOptions.find((item) => item.id === id) || contentWidthOptions[0];
    const getRhythmOption = (id) => rhythmOptions.find((item) => item.id === id) || rhythmOptions[0];
    const getBorderOption = (id) => borderOptions.find((item) => item.id === id) || borderOptions[0];
    const getCodeTreatmentOption = (id) => codeTreatmentOptions.find((item) => item.id === id) || codeTreatmentOptions[0];
    const getCustomizationStyle = (customization) => ({
      ...getShellPaddingOption(customization.shellPaddingId).style,
      ...getContentWidthOption(customization.contentWidthId).style,
      ...getRhythmOption(customization.rhythmId).style,
      ...getBorderOption(customization.borderId).style,
      ...getCodeTreatmentOption(customization.codeTreatmentId).style,
    });
    const getRadiusIndex = (value, fallback) => {
      const index = radiusOptions.findIndex((item) => item.value === value);
      return index >= 0 ? index : fallback;
    };
    const normalizeCustomization = (raw = {}) => {
      const current = raw && typeof raw === "object" ? raw : {};
      return {
        fontId: getFontOption(current.fontId).id,
        colorId: getColorOption(current.colorId).id,
        surfaceColorId: getSurfaceColorOption(current.surfaceColorId).id,
        shellPaddingId: getShellPaddingOption(current.shellPaddingId).id,
        contentWidthId: getContentWidthOption(current.contentWidthId).id,
        rhythmId: getRhythmOption(current.rhythmId).id,
        borderId: getBorderOption(current.borderId).id,
        codeTreatmentId: getCodeTreatmentOption(current.codeTreatmentId).id,
      };
    };
    const getPresetDefaults = (preset) => {
      const radiusIndex = radiusOptions[preset.defaultRadiusIndex ?? defaultConfig.radiusIndex]
        ? preset.defaultRadiusIndex ?? defaultConfig.radiusIndex
        : defaultConfig.radiusIndex;
      return {
        radiusIndex,
        customization: normalizeCustomization(preset.defaultCustomization || defaultConfig.customization),
      };
    };
    const getRequestedPresetId = (raw = {}) => {
      if (raw.presetId && raw.presetId !== "custom") return raw.presetId;
      return raw.flavorId || raw.themeId || raw.presetId;
    };
    const getOptionKey = (options) => Object.keys(options).sort().map((key) => key + ":" + options[key]).join("|");
    const normalizeOptions = (preset, rawOptions) => {
      const normalized = { ...preset.defaultOptions };
      const current = rawOptions && typeof rawOptions === "object" ? rawOptions : {};
      preset.controls.forEach((control) => {
        const requested = current[control.id];
        normalized[control.id] = control.values.includes(requested) ? requested : normalized[control.id];
      });
      return normalized;
    };
    const getMigratedOptions = (raw = {}) => {
      const optionsByPreset = raw.optionsByPreset && typeof raw.optionsByPreset === "object" ? { ...raw.optionsByPreset } : {};
      const legacyOptions = raw.optionsByFlavor && typeof raw.optionsByFlavor === "object" ? raw.optionsByFlavor : {};
      Object.entries(legacyOptions).forEach(([legacyId, options]) => {
        const preset = getPreset(legacyId);
        if (!optionsByPreset[preset.id]) {
          optionsByPreset[preset.id] = options;
        }
      });
      return optionsByPreset;
    };
    const normalizeConfig = (raw = {}) => {
      const requestedId = getRequestedPresetId(raw);
      const preset = getPreset(requestedId === "custom" ? raw.flavorId || raw.themeId : requestedId);
      const defaults = getPresetDefaults(preset);
      const optionsByPreset = getMigratedOptions(raw);
      const requestedRadiusIndex = Number.isInteger(raw.radiusIndex) ? raw.radiusIndex : defaults.radiusIndex;
      if (!optionsByPreset[preset.id]) {
        optionsByPreset[preset.id] = normalizeOptions(preset);
      }
      return {
        presetId: preset.id,
        radiusIndex: radiusOptions[requestedRadiusIndex] ? requestedRadiusIndex : defaults.radiusIndex,
        optionsByPreset,
        customization: normalizeCustomization(raw.customization || defaults.customization),
      };
    };
    const readConfig = () => {
      try {
        const stored = localStorage.getItem("${STORAGE_KEY}");
        if (stored) {
          return normalizeConfig(JSON.parse(stored));
        }
        const legacy = localStorage.getItem("${LEGACY_STORAGE_KEY}");
        if (legacy) {
          const migrated = normalizeConfig(JSON.parse(legacy));
          localStorage.setItem("${STORAGE_KEY}", JSON.stringify(migrated));
          localStorage.removeItem("${LEGACY_STORAGE_KEY}");
          return migrated;
        }
        return normalizeConfig({});
      } catch {
        return normalizeConfig({});
      }
    };
    const getTheme = (preset, options) => preset.themes[getOptionKey(options)] || preset.themes[preset.defaultKey];
    const getStyleElement = () => document.getElementById("theme-configurator-style") || (() => {
      const element = document.createElement("style");
      element.id = "theme-configurator-style";
      document.head.appendChild(element);
      return element;
    })();
    const setPage = (page = "presets") => {
      const requested = page === "custom" ? "custom" : "presets";
      document.querySelectorAll("[data-theme-page]").forEach((button) => {
        button.dataset.active = button.dataset.themePage === requested ? "true" : "false";
      });
      document.querySelectorAll("[data-theme-panel]").forEach((panel) => {
        panel.dataset.active = panel.dataset.themePanel === requested ? "true" : "false";
      });
    };
    const markActive = (rawConfig) => {
      const config = normalizeConfig(rawConfig);
      const preset = getPreset(config.presetId);
      const options = normalizeOptions(preset, config.optionsByPreset[preset.id]);
      const customization = normalizeCustomization(config.customization);
      document.querySelectorAll("[data-theme-preset]").forEach((button) => {
        button.dataset.active = button.dataset.themePreset === preset.id ? "true" : "false";
      });
      document.querySelectorAll("[data-preset-panel]").forEach((panel) => {
        panel.dataset.active = panel.dataset.presetPanel === preset.id ? "true" : "false";
      });
      document.querySelectorAll("[data-preset-id][data-preset-control][data-preset-option]").forEach((button) => {
        button.dataset.active = button.dataset.presetId === preset.id && options[button.dataset.presetControl] === button.dataset.presetOption ? "true" : "false";
      });
      document.querySelectorAll("[data-radius-option]").forEach((button) => {
        button.dataset.active = button.dataset.radiusOption === String(config.radiusIndex) ? "true" : "false";
      });
      document.querySelectorAll("[data-font-option]").forEach((button) => {
        button.dataset.active = button.dataset.fontOption === customization.fontId ? "true" : "false";
      });
      document.querySelectorAll("[data-color-option]").forEach((button) => {
        button.dataset.active = button.dataset.colorOption === customization.colorId ? "true" : "false";
      });
      document.querySelectorAll("[data-surface-color-option]").forEach((button) => {
        button.dataset.active = button.dataset.surfaceColorOption === customization.surfaceColorId ? "true" : "false";
      });
      document.querySelectorAll("[data-shell-padding-option]").forEach((button) => {
        button.dataset.active = button.dataset.shellPaddingOption === customization.shellPaddingId ? "true" : "false";
      });
      document.querySelectorAll("[data-content-width-option]").forEach((button) => {
        button.dataset.active = button.dataset.contentWidthOption === customization.contentWidthId ? "true" : "false";
      });
      document.querySelectorAll("[data-rhythm-option]").forEach((button) => {
        button.dataset.active = button.dataset.rhythmOption === customization.rhythmId ? "true" : "false";
      });
      document.querySelectorAll("[data-border-option]").forEach((button) => {
        button.dataset.active = button.dataset.borderOption === customization.borderId ? "true" : "false";
      });
      document.querySelectorAll("[data-code-treatment-option]").forEach((button) => {
        button.dataset.active = button.dataset.codeTreatmentOption === customization.codeTreatmentId ? "true" : "false";
      });
    };
    const apply = (rawConfig, persist = false, syncControls = true) => {
      const config = normalizeConfig(rawConfig);
      const preset = getPreset(config.presetId);
      const options = normalizeOptions(preset, config.optionsByPreset[preset.id]);
      const theme = getTheme(preset, options);
      const radius = getRadius(config.radiusIndex);
      const font = getFontOption(config.customization.fontId);
      const color = getColorOption(config.customization.colorId);
      const surface = getSurfaceColorOption(config.customization.surfaceColorId);
      const style = getCustomizationStyle(config.customization);
      // Keep this format byte-identical to themeToCss(): the bootstrap runs
      // before hydration and rewrites the server-rendered style element, so a
      // format drift would make every page load a hydration mismatch even for
      // the default config.
      getStyleElement().textContent = "\\n    :root {\\n" + toVars(theme.light) + "\\n" + toVars(surface.light) + "\\n" + toVars(color.light) + "\\n" + toVars(theme.style) + "\\n" + toVars(style) + "\\n" + toVars(font.style) + "\\n      --radius: " + radius.value + ";\\n    }\\n    .dark {\\n" + toVars(theme.dark) + "\\n" + toVars(surface.dark) + "\\n" + toVars(color.dark) + "\\n    }\\n" + shellThemeCss + "\\n  ";
      if (persist) {
        localStorage.setItem("${STORAGE_KEY}", JSON.stringify(config));
      }
      if (syncControls) {
        markActive(config);
      }
    };
    const applyPreset = (presetId) => {
      const config = readConfig();
      const preset = getPreset(presetId);
      const defaults = getPresetDefaults(preset);
      apply({
        ...config,
        presetId: preset.id,
        radiusIndex: defaults.radiusIndex,
        optionsByPreset: { ...config.optionsByPreset, [preset.id]: normalizeOptions(preset) },
        customization: defaults.customization,
      }, true);
    };
    apply(readConfig(), false, false);
    // A plain inline <script> re-executes whenever the docs layout remounts
    // during client-side navigation. Re-applying the theme above is idempotent
    // and desirable, but the document-level click listener must only ever be
    // registered once or handlers would accumulate across navigations.
    if (window.__folioThemeBootstrapBound) {
      return;
    }
    window.__folioThemeBootstrapBound = true;
    document.addEventListener("click", (event) => {
      const backButton = event.target.closest("[data-theme-back]");
      if (backButton) {
        setPage(backButton.dataset.themeBack);
        return;
      }
      const customButton = event.target.closest("[data-theme-custom]");
      if (customButton) {
        setPage("custom");
        return;
      }
      const presetButton = event.target.closest("[data-theme-preset]");
      if (presetButton) {
        applyPreset(presetButton.dataset.themePreset);
        return;
      }
      const optionButton = event.target.closest("[data-preset-id][data-preset-control][data-preset-option]");
      if (optionButton) {
        const config = readConfig();
        const preset = getPreset(optionButton.dataset.presetId || config.presetId);
        const currentOptions = normalizeOptions(preset, config.optionsByPreset[preset.id]);
        const nextOptions = { ...currentOptions, [optionButton.dataset.presetControl]: optionButton.dataset.presetOption };
        const theme = getTheme(preset, nextOptions);
        apply({
          ...config,
          presetId: preset.id,
          radiusIndex: getRadiusIndex(theme.radius, config.radiusIndex),
          optionsByPreset: { ...config.optionsByPreset, [preset.id]: nextOptions },
        }, true);
        return;
      }
      const radiusButton = event.target.closest("[data-radius-option]");
      if (radiusButton) {
        apply({ ...readConfig(), radiusIndex: Number(radiusButton.dataset.radiusOption) }, true);
        return;
      }
      const fontButton = event.target.closest("[data-font-option]");
      if (fontButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, fontId: fontButton.dataset.fontOption } }, true);
        return;
      }
      const colorButton = event.target.closest("[data-color-option]");
      if (colorButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, colorId: colorButton.dataset.colorOption } }, true);
        return;
      }
      const surfaceColorButton = event.target.closest("[data-surface-color-option]");
      if (surfaceColorButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, surfaceColorId: surfaceColorButton.dataset.surfaceColorOption } }, true);
        return;
      }
      const shellPaddingButton = event.target.closest("[data-shell-padding-option]");
      if (shellPaddingButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, shellPaddingId: shellPaddingButton.dataset.shellPaddingOption } }, true);
        return;
      }
      const contentWidthButton = event.target.closest("[data-content-width-option]");
      if (contentWidthButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, contentWidthId: contentWidthButton.dataset.contentWidthOption } }, true);
        return;
      }
      const rhythmButton = event.target.closest("[data-rhythm-option]");
      if (rhythmButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, rhythmId: rhythmButton.dataset.rhythmOption } }, true);
        return;
      }
      const borderButton = event.target.closest("[data-border-option]");
      if (borderButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, borderId: borderButton.dataset.borderOption } }, true);
        return;
      }
      const codeTreatmentButton = event.target.closest("[data-code-treatment-option]");
      if (codeTreatmentButton) {
        const config = readConfig();
        apply({ ...config, customization: { ...config.customization, codeTreatmentId: codeTreatmentButton.dataset.codeTreatmentOption } }, true);
        return;
      }
      if (event.target.closest("[data-theme-reset]")) {
        apply(defaultConfig, true);
      }
    });
  } catch {}
})();
`

function ThemePreviewStrip({ theme, isDark }: { theme: ResolvedPresetTheme; isDark: boolean }) {
  const vars = isDark ? theme.dark : theme.light
  const s = theme.style
  const isUppercase = s["--folio-h2-transform"] === "uppercase"
  const hasBottomBorder = s["--folio-h2-border"] !== "none"
  const cardRadius = theme.radius
  const hasShadow = s["--folio-card-shadow"] !== "none"
  const isInvertedCode = s["--folio-code-bg"] === "var(--foreground)"
  const borderWidth = s["--folio-card-border-width"]

  return (
    <div
      className="mt-2 flex h-10 w-full gap-1.5 overflow-hidden rounded-sm p-1"
      style={{ background: vars["--background"] }}
    >
      <div className="flex min-w-0 flex-[2] flex-col justify-center gap-0.5">
        <div
          className="h-1.5"
          style={{
            background: vars["--foreground"],
            width: isUppercase ? "54%" : "74%",
            borderRadius: cardRadius === "0" ? "0" : "9999px",
          }}
        />
        {hasBottomBorder && (
          <div className="h-px w-full" style={{ background: vars["--border"] }} />
        )}
        <div
          className="h-1 w-[90%] opacity-40"
          style={{ background: vars["--foreground"], borderRadius: cardRadius === "0" ? "0" : "9999px" }}
        />
        <div
          className="h-1 w-[65%] opacity-40"
          style={{ background: vars["--foreground"], borderRadius: cardRadius === "0" ? "0" : "9999px" }}
        />
      </div>

      <div
        className="flex min-w-0 flex-1 flex-col justify-center p-1"
        style={{
          background: vars["--card"] || vars["--background"],
          borderRadius: cardRadius,
          border: `${borderWidth} solid ${vars["--border"]}`,
          boxShadow: hasShadow ? "0 1px 3px oklch(0.1 0 0 / 0.12)" : "none",
        }}
      >
        <div
          className="mb-0.5 h-1 w-3/4"
          style={{ background: vars["--primary"], borderRadius: cardRadius === "0" ? "0" : "9999px" }}
        />
        <div
          className="h-0.5 w-full opacity-30"
          style={{ background: vars["--foreground"], borderRadius: cardRadius === "0" ? "0" : "9999px" }}
        />
      </div>

      <div
        className="flex w-5 shrink-0 flex-col justify-center p-0.5"
        style={{
          background: isInvertedCode ? vars["--foreground"] : vars["--muted"],
          borderRadius: cardRadius === "0" ? "0" : "2px",
          border: isInvertedCode ? "none" : `1px solid ${vars["--border"]}`,
        }}
      >
        <div
          className="mb-0.5 h-0.5 w-full opacity-70"
          style={{ background: isInvertedCode ? vars["--background"] : vars["--primary"] }}
        />
        <div
          className="h-0.5 w-3/4 opacity-40"
          style={{ background: isInvertedCode ? vars["--background"] : vars["--foreground"] }}
        />
      </div>
    </div>
  )
}

function PresetVisualTile({ theme, isDark }: { theme: ResolvedPresetTheme; isDark: boolean }) {
  const vars = isDark ? theme.dark : theme.light
  const s = theme.style
  const cardRadius = theme.radius
  const isInvertedCode = s["--folio-code-bg"] === "var(--foreground)"
  const hasShadow = s["--folio-card-shadow"] !== "none"

  return (
    <div
      className="theme-visual-preview mb-1.5 grid h-12 w-full grid-cols-[1.35fr_0.85fr] gap-1 overflow-hidden rounded-sm border p-1"
      style={{ background: vars["--background"], borderColor: vars["--border"] }}
      aria-hidden="true"
    >
      <div className="flex min-w-0 flex-col justify-between">
        <div className="space-y-1">
          <div
            className="h-2 w-10/12"
            style={{ background: vars["--foreground"], borderRadius: cardRadius === "0" ? "0" : "9999px" }}
          />
          <div
            className="h-1 w-7/12 opacity-55"
            style={{ background: vars["--foreground"], borderRadius: cardRadius === "0" ? "0" : "9999px" }}
          />
        </div>
        <div className="grid grid-cols-3 gap-1">
          {[0, 1, 2].map((item) => (
            <div
              key={item}
              className="h-4"
              style={{
                background: item === 0 ? vars["--primary"] : vars["--muted"],
                border: `1px solid ${vars["--border"]}`,
                borderRadius: cardRadius,
              }}
            />
          ))}
        </div>
      </div>

      <div className="grid min-w-0 grid-rows-[1fr_1fr] gap-1">
        <div
          style={{
            background: vars["--card"] || vars["--background"],
            border: `1px solid ${vars["--border"]}`,
            borderRadius: cardRadius,
            boxShadow: hasShadow ? "0 1px 3px oklch(0.1 0 0 / 0.12)" : "none",
          }}
        />
        <div
          className="flex flex-col justify-center gap-1 p-1"
          style={{
            background: isInvertedCode ? vars["--foreground"] : vars["--muted"],
            border: isInvertedCode ? "none" : `1px solid ${vars["--border"]}`,
            borderRadius: cardRadius,
          }}
        >
          <div
            className="h-0.5 w-full opacity-80"
            style={{ background: isInvertedCode ? vars["--background"] : vars["--primary"] }}
          />
          <div
            className="h-0.5 w-7/12 opacity-45"
            style={{ background: isInvertedCode ? vars["--background"] : vars["--foreground"] }}
          />
        </div>
      </div>
    </div>
  )
}

function CurrentThemeSummary({
  preset,
  theme,
  isDark,
}: {
  preset: ThemePreset
  theme: ResolvedPresetTheme
  isDark: boolean
}) {
  const vars = isDark ? theme.dark : theme.light

  return (
    <div
      data-theme-current
      className="flex min-w-0 items-center gap-2 border border-border bg-background px-2 py-1.5"
    >
      <span
        className="grid size-6 shrink-0 place-items-center border"
        style={{ background: vars["--background"], borderColor: vars["--border"] }}
        aria-hidden="true"
      >
        <span
          className="size-3.5"
          style={{ background: vars["--primary"], borderRadius: theme.radius === "0" ? "0" : "9999px" }}
        />
      </span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-semibold leading-tight text-foreground">
          {preset.name}
        </span>
      </span>
    </div>
  )
}

function ThemeModeControls({
  activeMode,
  onSelect,
}: {
  activeMode: ThemeMode
  onSelect: (mode: ThemeMode) => void
}) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Theme scheme
      </h4>
      <div className="grid grid-cols-3 gap-1.5">
        {modeOptions.map((option) => (
          <button
            key={option.id}
            type="button"
            data-theme-mode={option.id}
            data-active={activeMode === option.id ? "true" : "false"}
            onClick={() => onSelect(option.id)}
            className={cn(
              "inline-flex min-h-9 items-center justify-center gap-1.5 border border-border bg-background px-2 py-1.5 text-xs font-semibold transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
              "hover:bg-muted"
            )}
          >
            <HugeiconsIcon icon={option.icon} size={14} strokeWidth={1.5} />
            <span className="truncate">{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function PresetControlsPanel({
  config,
  preset,
  isActive,
  isDark,
  onUpdate,
}: {
  config: ThemeConfig
  preset: ThemePreset
  isActive: boolean
  isDark: boolean
  onUpdate: (presetId: string, controlId: string, value: string) => void
}) {
  const selectedOptions = getPresetOptions(config, preset.id)
  const selectedTheme = resolvePresetTheme(preset, selectedOptions)

  return (
    <div
      data-preset-panel={preset.id}
      data-active={isActive ? "true" : "false"}
      className="hidden data-[active=true]:block"
    >
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Preset controls
      </h4>
      <ThemePreviewStrip theme={selectedTheme} isDark={isDark} />
      <div className="mt-3 space-y-3">
        {preset.controls.map((control) => (
          <div key={control.id} className="space-y-1.5">
            <div className="text-xs font-medium text-foreground">{control.label}</div>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(4.25rem,1fr))] gap-1.5">
              {control.options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  data-preset-id={preset.id}
                  data-preset-control={control.id}
                  data-preset-option={option.value}
                  data-active={selectedOptions[control.id] === option.value ? "true" : "false"}
                  onClick={() => onUpdate(preset.id, control.id, option.value)}
                  className={cn(
                    "inline-flex min-h-8 items-center justify-center gap-1.5 rounded-sm border px-2 py-1 text-xs font-medium transition-colors duration-150",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
                    "border-border bg-background text-foreground hover:bg-muted"
                  )}
                >
                  {option.swatch ? (
                    <span
                      aria-hidden="true"
                      data-preset-option-swatch
                      className="size-2.5 shrink-0 rounded-full border border-foreground/10"
                      style={{ background: option.swatch }}
                    />
                  ) : null}
                  <span className="truncate">{option.label}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StyleOptionGroup({
  label,
  options,
  activeId,
  dataAttribute,
  onSelect,
}: {
  label: string
  options: StyleOption[]
  activeId: string
  dataAttribute: string
  onSelect: (id: string) => void
}) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </h4>
      <div className="grid grid-cols-2 gap-1.5">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            {...{ [dataAttribute]: option.id }}
            data-active={activeId === option.id ? "true" : "false"}
            onClick={() => onSelect(option.id)}
            className={cn(
              "min-h-9 border border-border bg-background px-2 py-1.5 text-left transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
              "hover:bg-muted"
            )}
          >
            <span className="block truncate text-xs font-semibold">{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function SurfaceColorGroup({
  options,
  activeId,
  isDark,
  onSelect,
}: {
  options: SurfaceColorOption[]
  activeId: string
  isDark: boolean
  onSelect: (id: string) => void
}) {
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Surface color
      </h4>
      <div className="grid grid-cols-2 gap-1.5">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            data-surface-color-option={option.id}
            data-active={activeId === option.id ? "true" : "false"}
            onClick={() => onSelect(option.id)}
            className={cn(
              "grid min-h-12 grid-cols-[2rem_1fr] gap-2 border border-border bg-background px-2 py-2 text-left transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
              "hover:bg-muted"
            )}
          >
            <span
              className="mt-0.5 size-6 border border-current/20"
              style={{ background: isDark ? option.preview.dark : option.preview.light }}
              aria-hidden="true"
            />
            <span className="min-w-0">
              <span className="block text-xs font-semibold">{option.label}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

export function ThemeConfigurator() {
  const [config, setConfig] = useState<ThemeConfig>(DEFAULT_CONFIG)
  const [activePage, setActivePage] = useState<"presets" | "custom">("presets")
  const [mounted, setMounted] = useState(false)
  const [drawerTarget, setDrawerTarget] = useState<HTMLElement | null>(null)
  const drawerRef = useRef<HTMLDetailsElement | null>(null)
  const { resolvedTheme, theme, setTheme } = useTheme()

  useEffect(() => {
    const loaded = loadConfig()
    applyConfig(loaded)
    const frame = requestAnimationFrame(() => {
      const latest = loadConfig()
      applyConfig(latest)
      setConfig(latest)
      setMounted(true)
    })
    return () => cancelAnimationFrame(frame)
  }, [])

  useEffect(() => {
    function syncDrawerTarget() {
      const target = document.querySelector(".nextra-sidebar-footer")
      setDrawerTarget(target instanceof HTMLElement ? target : null)
    }

    syncDrawerTarget()
    const observer = new MutationObserver(syncDrawerTarget)
    observer.observe(document.body, { childList: true, subtree: true })

    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    function closeDrawerOnOutsidePointerDown(event: PointerEvent) {
      const control = drawerRef.current
      const target = event.target

      if (!control?.open || !(target instanceof Node) || control.contains(target)) {
        return
      }

      control.open = false
    }

    document.addEventListener("pointerdown", closeDrawerOnOutsidePointerDown)

    return () => {
      document.removeEventListener("pointerdown", closeDrawerOnOutsidePointerDown)
    }
  }, [])

  const updateConfig = useCallback((patch: LegacyThemeConfig) => {
    setConfig((prev) => {
      const next = normalizeConfig({ ...prev, ...patch })
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      applyConfig(next)
      return next
    })
  }, [])

  const updateCustomization = useCallback((patch: Partial<ThemeCustomization>) => {
    const current = normalizeCustomization(config.customization)
    updateConfig({ customization: { ...current, ...patch } })
  }, [config.customization, updateConfig])

  const selectPreset = useCallback((presetId: string) => {
    const preset = getPreset(presetId)
    const defaults = getPresetDefaults(preset)

    updateConfig({
      presetId: preset.id,
      radiusIndex: defaults.radiusIndex,
      optionsByPreset: {
        ...config.optionsByPreset,
        [preset.id]: normalizePresetOptions(preset),
      },
      customization: defaults.customization,
    })
  }, [config.optionsByPreset, updateConfig])

  const updatePresetOption = useCallback((presetId: string, controlId: string, value: string) => {
    const preset = getPreset(presetId)
    const nextOptions = {
      ...getPresetOptions(config, preset.id),
      [controlId]: value,
    }
    const theme = resolvePresetTheme(preset, nextOptions)

    updateConfig({
      presetId: preset.id,
      radiusIndex: getRadiusIndex(theme.radius, config.radiusIndex),
      optionsByPreset: {
        ...config.optionsByPreset,
        [preset.id]: nextOptions,
      },
    })
  }, [config, updateConfig])

  const updateRadius = useCallback((radiusIndex: number) => {
    updateConfig({ radiusIndex })
  }, [updateConfig])

  const isDark = mounted && resolvedTheme === "dark"
  const activeMode = mounted ? normalizeThemeMode(theme) : "system"
  const activeModeLabel = activeMode === "system"
    ? isDark ? "System: Dark" : "System: Light"
    : modeOptions.find((option) => option.id === activeMode)?.label ?? "System"
  const activePreset = getPreset(config.presetId)
  const activePresetOptions = getPresetOptions(config, activePreset.id)
  const activeTheme = resolvePresetTheme(activePreset, activePresetOptions)
  const customization = normalizeCustomization(config.customization)

  const control = (
    <details
      ref={drawerRef}
      className="group/theme-picker theme-drawer-control relative z-[80] min-w-0"
      data-theme-configurator
    >
      <summary
        className="theme-drawer-trigger"
        title={`Change appearance. Current mode: ${activeModeLabel}. Current theme: ${activePreset.name}`}
        aria-label={`Customize appearance. Current mode: ${activeModeLabel}. Current theme: ${activePreset.name}`}
      >
        <span className="theme-drawer-trigger-label">Theme</span>
        <HugeiconsIcon
          className="theme-drawer-trigger-chevron"
          icon={ArrowDown01Icon}
          size={13}
          strokeWidth={1.9}
        />
      </summary>
      <div className="theme-drawer-panel absolute left-0 bottom-full mb-2 rounded-md border border-border bg-popover p-3 text-popover-foreground shadow-xl">
        <div
          data-theme-page="presets"
          data-theme-panel="presets"
          data-active={activePage === "presets" ? "true" : "false"}
          className="hidden data-[active=true]:block"
        >
            <div className="space-y-4">
              <CurrentThemeSummary
                preset={activePreset}
                theme={activeTheme}
                isDark={isDark}
              />

              <ThemeModeControls activeMode={activeMode} onSelect={(mode) => setTheme(mode)} />

              <div className="space-y-3">
                {groupedPresets.map((group) => (
                  <section key={group.id} data-theme-group={group.id} className="space-y-1.5">
                    <h4
                      data-theme-group-label
                      className="font-mono text-[11px] font-semibold text-muted-foreground"
                    >
                      {group.label}
                    </h4>
                    <div
                      data-theme-carousel
                      className="flex gap-1.5 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
                    >
                      {group.presets.map((preset) => {
                        const presetOptions = getPresetOptions(config, preset.id)
                        const previewTheme = resolvePresetTheme(preset, presetOptions)

                        return (
                          <button
                            key={preset.id}
                            type="button"
                            data-theme-preset={preset.id}
                            data-active={activePreset.id === preset.id ? "true" : "false"}
                            onClick={() => selectPreset(preset.id)}
                            className={cn(
                              "min-h-[4.75rem] w-[7.25rem] shrink-0 border border-border bg-background px-2 py-1.5 text-left transition-colors duration-150",
                              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                              "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
                              "hover:bg-muted"
                            )}
                          >
                            <PresetVisualTile theme={previewTheme} isDark={isDark} />
                            <span className="flex min-w-0 items-center gap-1">
                              <span className="block min-w-0 flex-1 truncate text-xs font-semibold">
                                {preset.name}
                              </span>
                              {preset.id === DEFAULT_CONFIG.presetId && (
                                <span
                                  data-theme-default-tag
                                  className="shrink-0 border border-current/20 px-1 font-mono text-[9px] leading-4 opacity-75"
                                >
                                  Default
                                </span>
                              )}
                            </span>
                          </button>
                        )
                      })}
                    </div>
                  </section>
                ))}
              </div>

              <button
                type="button"
                data-theme-custom
                onClick={() => setActivePage("custom")}
                className={cn(
                  "w-full border border-border bg-background px-3 py-3 text-left transition-colors duration-150",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  "hover:bg-muted"
                )}
              >
                <span className="block text-sm font-semibold text-foreground">Customize</span>
              </button>

              <button
                type="button"
                data-theme-reset
                onClick={() => {
                  updateConfig(DEFAULT_CONFIG)
                }}
                className="w-full border-t border-border pt-3 text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                Reset appearance
              </button>
            </div>
          </div>

          <div
            data-theme-page="custom"
            data-theme-panel="custom"
            data-active={activePage === "custom" ? "true" : "false"}
            className="hidden data-[active=true]:block"
          >
            <div className="space-y-5">
              <div className="theme-panel-header">
                <button
                  type="button"
                  data-theme-back="presets"
                  onClick={() => setActivePage("presets")}
                  className="theme-back-button"
                >
                  Back
                </button>
                <CurrentThemeSummary
                  preset={activePreset}
                  theme={activeTheme}
                  isDark={isDark}
                />
              </div>

              {presets.map((preset) => (
                <PresetControlsPanel
                  key={preset.id}
                  config={config}
                  preset={preset}
                  isActive={activePreset.id === preset.id}
                  isDark={isDark}
                  onUpdate={updatePresetOption}
                />
              ))}

              <StyleOptionGroup
                label="Shell spacing"
                options={shellPaddingOptions}
                activeId={customization.shellPaddingId}
                dataAttribute="data-shell-padding-option"
                onSelect={(shellPaddingId) => updateCustomization({ shellPaddingId })}
              />

              <StyleOptionGroup
                label="Content width"
                options={contentWidthOptions}
                activeId={customization.contentWidthId}
                dataAttribute="data-content-width-option"
                onSelect={(contentWidthId) => updateCustomization({ contentWidthId })}
              />

              <StyleOptionGroup
                label="Reading rhythm"
                options={rhythmOptions}
                activeId={customization.rhythmId}
                dataAttribute="data-rhythm-option"
                onSelect={(rhythmId) => updateCustomization({ rhythmId })}
              />

              <StyleOptionGroup
                label="Borders"
                options={borderOptions}
                activeId={customization.borderId}
                dataAttribute="data-border-option"
                onSelect={(borderId) => updateCustomization({ borderId })}
              />

              <StyleOptionGroup
                label="Code blocks"
                options={codeTreatmentOptions}
                activeId={customization.codeTreatmentId}
                dataAttribute="data-code-treatment-option"
                onSelect={(codeTreatmentId) => updateCustomization({ codeTreatmentId })}
              />

              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Typography
                </h4>
                <div className="grid grid-cols-2 gap-1.5">
                  {fontOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      data-font-option={option.id}
                      data-active={customization.fontId === option.id ? "true" : "false"}
                      onClick={() => updateCustomization({ fontId: option.id })}
                      className={cn(
                        "grid min-h-14 grid-cols-[2.35rem_1fr] gap-2 border border-border bg-background px-2 py-2 text-left transition-colors duration-150",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
                        "hover:bg-muted"
                      )}
                    >
                      <span
                        className="self-center text-xl font-semibold leading-none"
                        style={{ fontFamily: option.style["--folio-heading-font-family"] }}
                      >
                        {option.sample}
                      </span>
                      <span className="min-w-0">
                        <span className="block text-xs font-semibold">{option.label}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Accent color
                </h4>
                <div className="grid grid-cols-2 gap-1.5">
                  {colorOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      data-color-option={option.id}
                      data-active={customization.colorId === option.id ? "true" : "false"}
                      onClick={() => updateCustomization({ colorId: option.id })}
                      className={cn(
                        "grid min-h-12 grid-cols-[2rem_1fr] gap-2 border border-border bg-background px-2 py-2 text-left transition-colors duration-150",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
                        "hover:bg-muted"
                      )}
                    >
                      <span
                        className="mt-0.5 size-6 border border-current/20"
                        style={{ background: isDark ? option.preview.dark : option.preview.light }}
                        aria-hidden="true"
                      />
                      <span className="min-w-0">
                        <span className="block text-xs font-semibold">{option.label}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <SurfaceColorGroup
                options={surfaceColorOptions}
                activeId={customization.surfaceColorId}
                isDark={isDark}
                onSelect={(surfaceColorId) => updateCustomization({ surfaceColorId })}
              />

              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Corner radius
                </h4>
                <div className="flex gap-1.5">
                  {radiusOptions.map((option, i) => (
                    <button
                      key={option.label}
                      type="button"
                      data-radius-option={i}
                      data-active={config.radiusIndex === i ? "true" : "false"}
                      onClick={() => updateRadius(i)}
                      className={cn(
                        "h-8 flex-1 border text-xs font-medium transition-all duration-150",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        "data-[active=true]:border-primary data-[active=true]:bg-primary data-[active=true]:text-primary-foreground",
                        "border-border bg-background text-foreground hover:bg-muted"
                      )}
                      style={{ borderRadius: option.value || "0" }}
                      title={option.label}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                data-theme-reset
                onClick={() => {
                  updateConfig(DEFAULT_CONFIG)
                }}
                className="w-full border-t border-border pt-3 text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                Reset appearance
              </button>
            </div>
          </div>
        </div>
    </details>
  )

  return (
    <>
      <ThemeStyleBootstrap />
      {drawerTarget ? (
        createPortal(control, drawerTarget)
      ) : (
        <div className="theme-drawer-fallback">{control}</div>
      )}
    </>
  )
}

/**
 * The saved-reader-theme bootstrap on its own: the default theme CSS plus the
 * pre-hydration script that rewrites it to whatever the reader stored. Pages
 * that don't mount the configurator UI (the landing) mount this instead, so
 * the theme stays in sync across every route. Idempotent — the script
 * re-applies the stored config and binds its document listener only once.
 */
export function ThemeStyleBootstrap() {
  return (
    <>
      {/* The bootstrap script rewrites this element's text before hydration
          (to the reader's saved theme), so the hydrated innerHTML legitimately
          differs from DEFAULT_THEME_CSS whenever a non-default config is
          stored. Suppress the mismatch so React never "corrects" the element
          back to the default CSS mid-load. */}
      <style
        id="theme-configurator-style"
        suppressHydrationWarning
        dangerouslySetInnerHTML={{ __html: DEFAULT_THEME_CSS }}
      />
      <script
        id="theme-configurator-boot"
        dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP_SCRIPT }}
      />
    </>
  )
}
