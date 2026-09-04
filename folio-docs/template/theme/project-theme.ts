import type { ThemePreset } from "./preset-types"

export const projectThemePreset: ThemePreset | null = null

export const projectThemeDefaultConfig: {
  presetId?: string
  radiusIndex?: number
  optionsByPreset?: Record<string, Record<string, string>>
  customization?: Record<string, string>
} = {}
