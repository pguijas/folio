// Theme field names are generated from folio/schemas/theme_contract.py
import type { ThemeStyle, ThemeVars } from "./theme-contract.generated"
export type { ThemeStyle, ThemeVars }
export type PresetOptionValues = Record<string, string>

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
  swatch?: string
  description?: string
}

export interface PresetControl {
  id: string
  label: string
  description?: string
  options: PresetControlOption[]
}

export interface ThemeDefaultCustomization {
  fontId?: string
  colorId?: string
  surfaceColorId?: string
  shellPaddingId?: string
  contentWidthId?: string
  rhythmId?: string
  borderId?: string
  codeTreatmentId?: string
}

export interface ThemePreset {
  id: string
  name: string
  description: string
  scene: string
  preview: { light: string; dark: string }
  defaultOptions: PresetOptionValues
  defaultRadiusIndex?: number
  defaultCustomization?: ThemeDefaultCustomization
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

// Cheap upper bound on getPresetOptionCombinations(preset).length: the
// option-count product. Used to decide whether enumerating the cartesian
// product is affordable at all, without materializing it first.
export function countPresetOptionCombinations(preset: ThemePreset): number {
  return preset.controls.reduce(
    (product, control) => product * Math.max(control.options.length, 1),
    1
  )
}

// Defense in depth on top of the config-side combination cap: if a preset
// still resolves to an unreasonable number of option combinations, embed only
// the default resolution so the inline bootstrap script stays small. The
// bootstrap falls back to the default theme for missing keys and the React
// component resolves the exact options after hydration.
export const MAX_BOOTSTRAP_COMBINATIONS = 512

export interface BootstrapPreset {
  id: string
  defaultOptions: PresetOptionValues
  defaultRadiusIndex?: number
  defaultCustomization?: ThemeDefaultCustomization
  controls: Array<{ id: string; values: string[] }>
  defaultKey: string
  themes: Record<string, ResolvedPresetTheme>
}

export function buildBootstrapPresets(
  presetList: ThemePreset[],
  maxCombinations: number = MAX_BOOTSTRAP_COMBINATIONS
): BootstrapPreset[] {
  return presetList.map((preset) => {
    const defaultOptions = normalizePresetOptions(preset)
    // Check the budget BEFORE enumerating: an over-budget preset must not pay
    // the full cartesian-product enumeration cost just to be told it is over
    // budget, so the cap bounds both output size and enumeration work.
    const combinationCount = countPresetOptionCombinations(preset)
    const withinBudget = combinationCount <= maxCombinations
    if (!withinBudget) {
      console.warn(
        `[theme-configurator] Preset "${preset.id}" has ${combinationCount} option combinations; embedding only the default resolution in the bootstrap script.`
      )
    }
    const combinations = withinBudget
      ? getPresetOptionCombinations(preset)
      : [defaultOptions]
    const themes = Object.fromEntries(
      combinations.map((options) => [
        getPresetOptionKey(options),
        resolvePresetTheme(preset, options),
      ])
    )

    return {
      id: preset.id,
      defaultOptions,
      defaultRadiusIndex: preset.defaultRadiusIndex,
      defaultCustomization: preset.defaultCustomization,
      controls: preset.controls.map((control) => ({
        id: control.id,
        values: control.options.map((option) => option.value),
      })),
      defaultKey: getPresetOptionKey(defaultOptions),
      themes,
    }
  })
}
