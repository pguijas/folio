export type ThemeVars = Record<string, string>
export type PresetOptionValues = Record<string, string>

export interface ThemeStyle {
  "--heading-font-family": string
  "--body-font-family": string
  "--code-font-family": string
  "--heading-letter-spacing": string
  "--heading-weight": string
  "--body-line-height": string
  "--font-size-base": string
  "--card-shadow": string
  "--card-border-width": string
  "--card-padding": string
  "--card-hover-shadow": string
  "--card-backdrop": string
  "--card-opacity": string
  "--code-border-radius": string
  "--code-border": string
  "--code-bg": string
  "--code-foreground": string
  "--code-shadow": string
  "--h2-border": string
  "--h2-transform": string
  "--h2-letter-spacing": string
  "--h2-weight": string
  "--h2-padding-left": string
  "--h2-border-left": string
  "--link-decoration": string
  "--section-gap": string
  "--content-max-width": string
  "--workspace-shell-padding": string
  "--workspace-shell-border": string
  "--workspace-shell-shadow": string
  "--workspace-shell-background": string
  "--workspace-shell-surface": string
  "--workspace-shell-topbar": string
}

export interface ResolvedPresetTheme {
  preview: { light: string; dark: string }
  radius: string
  style: ThemeStyle
  light: ThemeVars
  dark: ThemeVars
}

export interface PresetControlOption {
  label: string
  value: string
  description?: string
}

export interface PresetControl {
  id: string
  label: string
  description?: string
  options: PresetControlOption[]
}

export interface ThemePreset {
  id: string
  name: string
  description: string
  scene: string
  preview: { light: string; dark: string }
  defaultOptions: PresetOptionValues
  defaultRadiusIndex?: number
  defaultCustomization?: { fontId: string; colorId: string }
  controls: PresetControl[]
  resolve: (options: PresetOptionValues) => ResolvedPresetTheme
}

export function normalizePresetOptions(
  preset: ThemePreset,
  options: Partial<PresetOptionValues> = {}
): PresetOptionValues {
  const normalized: PresetOptionValues = { ...preset.defaultOptions }

  for (const control of preset.controls) {
    const requested = options[control.id]
    const fallback = preset.defaultOptions[control.id] ?? control.options[0]?.value
    const hasRequested = control.options.some((option) => option.value === requested)
    normalized[control.id] = hasRequested ? String(requested) : fallback
  }

  return normalized
}

export function getPresetOptionKey(options: PresetOptionValues): string {
  return Object.keys(options)
    .sort()
    .map((key) => `${key}:${options[key]}`)
    .join("|")
}

export function resolvePresetTheme(
  preset: ThemePreset,
  options: Partial<PresetOptionValues> = {}
): ResolvedPresetTheme {
  return preset.resolve(normalizePresetOptions(preset, options))
}

export function getPresetOptionCombinations(preset: ThemePreset): PresetOptionValues[] {
  if (preset.controls.length === 0) {
    return [normalizePresetOptions(preset)]
  }

  return preset.controls.reduce<PresetOptionValues[]>(
    (sets, control) =>
      sets.flatMap((set) =>
        control.options.map((option) =>
          normalizePresetOptions(preset, {
            ...set,
            [control.id]: option.value,
          })
        )
      ),
    [normalizePresetOptions(preset)]
  )
}
